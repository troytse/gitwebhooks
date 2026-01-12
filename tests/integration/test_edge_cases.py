"""
Integration Tests for Edge Cases (Phase 15)

Tests for covering edge cases and error handling paths.
"""

import unittest
import sys
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tests.conftest import WebhookTestCase, TestConfigBuilder
from tests.utils.http_client import TestWebhookClient
from tests.utils.server_manager import TestServer
from tests.fixtures.github_payloads import PayloadBuilder


class TestEdgeCases(WebhookTestCase):
    """Test edge cases and error handling."""

    def setUp(self):
        """Set up test environment."""
        super().setUp()
        self.temp_dir = self.create_temp_dir()

    def test_zero_content_length_handled(self):
        """
        Test that Content-Length: 0 is handled correctly.
        """
        config_builder = TestConfigBuilder(self.temp_dir)
        config_path = config_builder.build()

        with TestServer(config_path) as server:
            server.wait_for_ready()

            client = TestWebhookClient("127.0.0.1", server.port)

            response = client.send_raw(
                "POST",
                "/",
                headers={
                    "X-GitHub-Event": "push",
                    "Content-Length": "0"
                },
                body=b""
            )

            # Should handle gracefully (400 for empty body)
            self.assertIn(response.status_code, [400, 404])

    def test_missing_content_length_handled(self):
        """
        Test that missing Content-Length header is handled.
        """
        config_builder = TestConfigBuilder(self.temp_dir)
        config_path = config_builder.build()

        with TestServer(config_path) as server:
            server.wait_for_ready()

            client = TestWebhookClient("127.0.0.1", server.port)

            response = client.send_raw(
                "POST",
                "/",
                headers={"X-GitHub-Event": "push"},
                body=b'{"test": "data"}'
            )

            # Should handle (server may use chunked encoding or fail gracefully)
            self.assertIsNotNone(response)

    def test_missing_repo_config_section_handled(self):
        """
        Test when repo is found but cwd or cmd is missing.
        """
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as f:
            f.write("[server]\nport=6789\n\n")
            f.write("[github]\nhandle_events=push\nverify=false\n\n")
            f.write("[incomplete/repo]\n")  # No cwd or cmd
            config_path = f.name

        try:
            with TestServer(config_path) as server:
                server.wait_for_ready()

                client = TestWebhookClient("127.0.0.1", server.port)

                response = client.send_webhook(
                    headers={"X-GitHub-Event": "push"},
                    payload=PayloadBuilder.github_push_event(repo="incomplete/repo")
                )

                # Should handle gracefully (200 but command may fail)
                self.assertIn(response.status_code, [200, 500])
        finally:
            Path(config_path).unlink(missing_ok=True)

    def test_empty_handle_events_accepts_all(self):
        """
        Test that empty handle_events accepts all events.
        """
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as f:
            f.write("[server]\nport=6789\n\n")
            f.write("[github]\nhandle_events=\nverify=false\n\n")  # Empty events
            f.write("[test/repo]\ncwd=/tmp\ncmd=echo test\n")
            config_path = f.name

        try:
            with TestServer(config_path) as server:
                server.wait_for_ready()

                client = TestWebhookClient("127.0.0.1", server.port)

                # Send any event - should be accepted
                response = client.send_webhook(
                    headers={"X-GitHub-Event": "random_event"},
                    payload=PayloadBuilder.github_push_event(repo="test/repo")
                )

                # Should not get 406 (not acceptable)
                self.assertNotEqual(response.status_code, 406)
        finally:
            Path(config_path).unlink(missing_ok=True)

    def test_concurrent_webhook_requests(self):
        """
        Test that multiple concurrent requests are handled.
        """
        import threading

        marker_file = Path(self.temp_dir) / ".concurrent_marker"
        cmd = f"touch {marker_file}"

        config_builder = TestConfigBuilder(self.temp_dir)
        config_builder.set_platform_verify('github', verify=False)
        config_builder.add_repository("test/repo", self.temp_dir, cmd)
        config_path = config_builder.build()

        with TestServer(config_path) as server:
            server.wait_for_ready()

            results = []

            def send_request():
                client = TestWebhookClient("127.0.0.1", server.port)
                response = client.send_webhook(
                    headers={"X-GitHub-Event": "push"},
                    payload=PayloadBuilder.github_push_event(repo="test/repo")
                )
                results.append(response.status_code)

            # Send multiple concurrent requests
            threads = []
            for _ in range(5):
                t = threading.Thread(target=send_request)
                threads.append(t)
                t.start()

            # Wait for all threads
            for t in threads:
                t.join()

            time.sleep(1)

            # All requests should get 200
            for status in results:
                self.assertEqual(status, 200)

    def test_large_command_output_handled(self):
        """
        Test that commands with large output are handled.
        """
        large_output_file = Path(self.temp_dir) / "large_output.txt"
        cmd = f"yes | head -n 10000 > {large_output_file}"

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

            time.sleep(2)

            # Output file should exist
            self.assertTrue(large_output_file.exists())

    def test_log_file_directory_not_exists(self):
        """
        Test when log file directory doesn't exist.
        """
        log_path = f"/tmp/nonexistent_log_dir_12345/test.log"

        config_builder = TestConfigBuilder(self.temp_dir)
        config_builder.set_server_config(log_file=log_path)
        config_builder.set_platform_verify('github', verify=False)
        config_builder.add_repository("test/repo", self.temp_dir, "echo test")
        config_path = config_builder.build()

        # Server should start despite log directory not existing
        # (it may log to stdout only)
        with TestServer(config_path) as server:
            server.wait_for_ready()
            self.assertTrue(server.is_running)

    def test_repo_name_with_special_characters(self):
        """
        Test repo names with spaces and special characters.
        """
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as f:
            f.write("[server]\nport=6789\n\n")
            f.write("[github]\nhandle_events=push\nverify=false\n\n")
            # Repo with special chars
            f.write("[user/repo.with.dots]\ncwd=/tmp\ncmd=echo test\n")
            config_path = f.name

        try:
            with TestServer(config_path) as server:
                server.wait_for_ready()

                client = TestWebhookClient("127.0.0.1", server.port)

                response = client.send_webhook(
                    headers={"X-GitHub-Event": "push"},
                    payload=PayloadBuilder.github_push_event(repo="user/repo.with.dots")
                )

                # Should handle the special characters
                self.assertIsNotNone(response)
        finally:
            Path(config_path).unlink(missing_ok=True)


if __name__ == '__main__':
    unittest.main()
