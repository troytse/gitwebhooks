"""
Integration Tests for Command Execution (User Story 8)

Tests for verifying that webhook requests trigger the configured commands
in the correct working directory.
"""

import unittest
import sys
from pathlib import Path
import os

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tests.conftest import WebhookTestCase, TestConfigBuilder
from tests.utils.http_client import TestWebhookClient
from tests.utils.server_manager import TestServer
from tests.fixtures.github_payloads import PayloadBuilder


class TestCommandExecution(WebhookTestCase):
    """Test command execution triggered by webhooks."""

    def setUp(self):
        """Set up test environment."""
        super().setUp()
        self.temp_dir = self.create_temp_dir()

    def test_command_executes_successfully(self):
        """
        Test that configured command executes successfully.

        When a webhook is received for a configured repository,
        the associated command should be executed.
        """
        marker_file = Path(self.temp_dir) / ".test_marker"
        cmd = f"touch {marker_file}"

        config_builder = TestConfigBuilder(self.temp_dir)
        config_builder.set_platform_verify('github', verify=False)
        config_builder.add_repository("test/repo", self.temp_dir, cmd)
        config_path = config_builder.build()

        with TestServer(config_path) as server:
            server.wait_for_ready()

            client = TestWebhookClient("127.0.0.1", server.port)

            # Send webhook
            response = client.send_webhook(
                headers={"X-GitHub-Event": "push"},
                payload=PayloadBuilder.github_push_event(repo="test/repo")
            )

            # Should get 200 OK
            self.assertStatusCode(response, 200)

            # Verify marker file was created (command executed)
            self.assertTrue(self.wait_for_file(marker_file),
                          f"Command did not execute: marker file not found at {marker_file}")

    def test_large_command_output_does_not_block(self):
        """
        Test that a command producing more output than the OS pipe buffer
        still completes.

        Regression: execute_deployment used to create stdout/stderr pipes that
        were never read, so a chatty deploy command blocked forever once it
        filled the pipe buffer (Linux default 64 KiB) - the "push, nothing
        happens, no error, no log tail" symptom.
        """
        marker_file = Path(self.temp_dir) / ".flood_marker"
        emitter = Path(self.temp_dir) / "emit.py"
        emitter.write_text(
            "import sys\n"
            "sys.stdout.write('x' * 400000)\n"
            "sys.stdout.flush()\n"
            "open(sys.argv[1], 'w').write('done')\n",
            encoding='utf-8'
        )
        cmd = f"{sys.executable} {emitter} {marker_file}"

        config_builder = TestConfigBuilder(self.temp_dir)
        config_builder.set_platform_verify('github', verify=False)
        config_builder.add_repository("test/repo", self.temp_dir, cmd)
        config_path = config_builder.build()

        with TestServer(config_path) as server:
            server.wait_for_ready()

            client = TestWebhookClient("127.0.0.1", server.port)

            response = client.send_webhook(
                headers={"X-GitHub-Event": "push"},
                payload=PayloadBuilder.github_push_event(repo="test/repo")
            )
            self.assertStatusCode(response, 200)

            self.assertTrue(
                self.wait_for_file(marker_file, timeout=30),
                "deploy command never finished: it blocked writing to an unread pipe"
            )

    def test_command_failure_logged_but_returns_200(self):
        """
        Test that command failure is logged but server returns 200.

        Commands are executed asynchronously with Popen, so failures
        don't block the HTTP response. The server should still return 200
        and log the failure.
        """
        # Command that will fail (exit code 1)
        cmd = "exit 1"

        config_builder = TestConfigBuilder(self.temp_dir)
        config_builder.set_platform_verify('github', verify=False)
        config_builder.add_repository("test/repo", self.temp_dir, cmd)

        log_file = self.create_temp_file(suffix=".log")
        config_builder.set_server_config(log_file=log_file)
        config_path = config_builder.build()

        with TestServer(config_path) as server:
            server.wait_for_ready()

            client = TestWebhookClient("127.0.0.1", server.port)

            # Send webhook
            response = client.send_webhook(
                headers={"X-GitHub-Event": "push"},
                payload=PayloadBuilder.github_push_event(repo="test/repo")
            )

            # Should still return 200 (non-blocking execution)
            self.assertStatusCode(response, 200)

            # The failure must be visible in the log (exit code + output tail)
            self.assertTrue(
                self.wait_for_log_contains(log_file, 'Deployment failed (exit 1)'),
                "command failure was not logged"
            )

    def test_unknown_repo_logged_warning(self):
        """
        Test that unknown repository is logged with warning.

        When a webhook references a repository not in the config,
        the server should log a warning and return appropriate status.
        """
        config_builder = TestConfigBuilder(self.temp_dir)
        config_builder.set_platform_verify('github', verify=False)
        # Don't add "unknown/repo" to config
        config_path = config_builder.build()

        log_file = self.create_temp_file(suffix=".log")
        config_builder.set_server_config(log_file=log_file)
        config_path = config_builder.build()

        with TestServer(config_path) as server:
            server.wait_for_ready()

            client = TestWebhookClient("127.0.0.1", server.port)

            # Send webhook for unknown repo
            response = client.send_webhook(
                headers={"X-GitHub-Event": "push"},
                payload=PayloadBuilder.github_push_event(repo="unknown/repo")
            )

            # Should get 404 or log warning (repo not found)
            self.assertIn(response.status_code, [200, 404],
                         f"Unexpected status: {response.status_code}")

            # Check log for warning
            self.assertTrue(
                self.wait_for_log_contains(log_file, 'No repository configuration'),
                "missing repository configuration was not logged"
            )

    def test_nonexistent_directory_logged_error(self):
        """
        Test that invalid cwd path is logged as error.

        If the configured cwd doesn't exist, the command execution
        should fail and be logged.
        """
        nonexistent_dir = "/tmp/nonexistent_test_dir_12345"
        cmd = "echo 'test'"

        config_builder = TestConfigBuilder(self.temp_dir)
        config_builder.set_platform_verify('github', verify=False)
        config_builder.add_repository("test/repo", nonexistent_dir, cmd)

        log_file = self.create_temp_file(suffix=".log")
        config_builder.set_server_config(log_file=log_file)
        config_path = config_builder.build()

        with TestServer(config_path) as server:
            server.wait_for_ready()

            client = TestWebhookClient("127.0.0.1", server.port)

            # Send webhook
            response = client.send_webhook(
                headers={"X-GitHub-Event": "push"},
                payload=PayloadBuilder.github_push_event(repo="test/repo")
            )

            # Should return 200 (async execution)
            self.assertStatusCode(response, 200)

            # Check log for error
            self.assertTrue(
                self.wait_for_log_contains(log_file, 'Execution failed'),
                "bad working directory was not logged"
            )

    def test_marker_file_created_on_success(self):
        """
        Test that marker file is created when command succeeds.

        This is a more detailed version of test_command_executes_successfully
        that specifically verifies the marker file creation pattern.
        """
        repo_name = "test/repo"
        marker_name = ".success_marker"
        marker_file = Path(self.temp_dir) / marker_name
        cmd = f"touch {marker_file} && echo 'success'"

        config_builder = TestConfigBuilder(self.temp_dir)
        config_builder.set_platform_verify('github', verify=False)
        config_builder.add_repository(repo_name, self.temp_dir, cmd)
        config_path = config_builder.build()

        with TestServer(config_path) as server:
            server.wait_for_ready()

            client = TestWebhookClient("127.0.0.1", server.port)

            # Send webhook
            response = client.send_webhook(
                headers={"X-GitHub-Event": "push"},
                payload=PayloadBuilder.github_push_event(repo=repo_name)
            )

            self.assertStatusCode(response, 200)

            # Verify marker file exists
            self.assertTrue(self.wait_for_file(marker_file),
                          f"Marker file not created at {marker_file}")

    def test_command_with_output(self):
        """
        Test that command output is handled correctly.

        Commands with output should execute without issues.
        Output is redirected to PIPE in Popen.
        """
        output_file = Path(self.temp_dir) / "output.txt"
        cmd = f"echo 'Hello World' > {output_file}"

        config_builder = TestConfigBuilder(self.temp_dir)
        config_builder.set_platform_verify('github', verify=False)
        config_builder.add_repository("test/repo", self.temp_dir, cmd)
        config_path = config_builder.build()

        with TestServer(config_path) as server:
            server.wait_for_ready()

            client = TestWebhookClient("127.0.0.1", server.port)

            # Send webhook
            response = client.send_webhook(
                headers={"X-GitHub-Event": "push"},
                payload=PayloadBuilder.github_push_event(repo="test/repo")
            )

            self.assertStatusCode(response, 200)

            # Verify output file exists
            self.assertTrue(self.wait_for_file(output_file),
                          f"Output file not created at {output_file}")

            # Check content
            content = output_file.read_text().strip()
            self.assertEqual(content, "Hello World")

    def test_multiple_webhooks_trigger_multiple_commands(self):
        """
        Test that multiple webhook requests trigger multiple executions.

        Sending the same webhook multiple times should execute
        the command each time.
        """
        counter_file = Path(self.temp_dir) / "counter.txt"
        cmd = f"if [ -f {counter_file} ]; then count=$(cat {counter_file}); else count=0; fi; echo $((count + 1)) > {counter_file}"

        config_builder = TestConfigBuilder(self.temp_dir)
        config_builder.set_platform_verify('github', verify=False)
        config_builder.add_repository("test/repo", self.temp_dir, cmd)
        config_path = config_builder.build()

        with TestServer(config_path) as server:
            server.wait_for_ready()

            client = TestWebhookClient("127.0.0.1", server.port)

            def count_so_far():
                """Current counter value (0 if the file is absent/unreadable)."""
                try:
                    return int(counter_file.read_text().strip())
                except (OSError, ValueError):
                    return 0

            # Send first webhook
            response1 = client.send_webhook(
                headers={"X-GitHub-Event": "push"},
                payload=PayloadBuilder.github_push_event(repo="test/repo")
            )
            self.assertStatusCode(response1, 200)
            self.wait_until(lambda: count_so_far() >= 1)

            # Send second webhook
            response2 = client.send_webhook(
                headers={"X-GitHub-Event": "push"},
                payload=PayloadBuilder.github_push_event(repo="test/repo")
            )
            self.assertStatusCode(response2, 200)
            self.wait_until(lambda: count_so_far() >= 2)

            # Send third webhook
            response3 = client.send_webhook(
                headers={"X-GitHub-Event": "push"},
                payload=PayloadBuilder.github_push_event(repo="test/repo")
            )
            self.assertStatusCode(response3, 200)
            self.assertTrue(
                self.wait_until(lambda: count_so_far() >= 3),
                "not all three webhooks triggered their command"
            )

            # Verify counter is 3
            self.assertTrue(counter_file.exists())
            count = int(counter_file.read_text().strip())
            self.assertEqual(count, 3, "Command should execute 3 times")

    def _read_log_file(self, log_path: str) -> str:
        """Read log file content."""
        try:
            with open(log_path, 'r') as f:
                return f.read()
        except FileNotFoundError:
            return ""


if __name__ == '__main__':
    unittest.main()
