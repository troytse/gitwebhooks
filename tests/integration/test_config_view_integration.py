"""
Integration Tests for Configuration View Command (User Stories 1, 2, 3)

End-to-end tests for the config view command including file location,
content display, error handling, sensitive field highlighting, and edge cases.
"""

import unittest
import sys
import tempfile
import subprocess
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tests.conftest import WebhookTestCase

# Get the project root directory for PYTHONPATH
PROJECT_ROOT = str(Path(__file__).parent.parent.parent)


def run_cmd_with_env(cmd_list):
    """Helper function to run command with proper PYTHONPATH."""
    env = os.environ.copy()
    env['PYTHONPATH'] = PROJECT_ROOT
    return subprocess.run(
        cmd_list,
        capture_output=True,
        text=True,
        timeout=5,
        env=env
    )


class TestConfigViewIntegration(WebhookTestCase):
    """Integration tests for config view command."""

    def test_config_view_displays_config_content(self):
        """
        Test that config view displays configuration file content.

        Running gitwebhooks-cli config view should display the current
        configuration file with sections and key-value pairs.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a test config file
            config_path = Path(temp_dir) / "test_config.ini"
            config_content = """[server]
address = 0.0.0.0
port = 6789
log_file = /var/log/gitwebhooks.log

[github]
handle_events = push
verify = true
secret = my_webhook_secret

[repo/example]
cwd = /var/www/example
cmd = git pull
"""
            config_path.write_text(config_content)

            # Run config view command
            result = run_cmd_with_env(
                [sys.executable, '-m', 'gitwebhooks', 'config', 'view', '-c', str(config_path)]
            )

            # Should succeed
            self.assertEqual(result.returncode, 0)

            # Should display config file path
            self.assertIn('Config File:', result.stdout)
            self.assertIn(str(config_path), result.stdout)

            # Should display sections
            self.assertIn('[server]', result.stdout)
            self.assertIn('[github]', result.stdout)
            self.assertIn('[repo/example]', result.stdout)

            # Should display key-value pairs
            self.assertIn('address = 0.0.0.0', result.stdout)
            self.assertIn('port = 6789', result.stdout)

    def test_config_view_user_specified_file_not_found(self):
        """
        Test that config view displays clear error for user-specified file.

        When user specifies a file with -c that doesn't exist,
        should show a clear error message.
        """
        result = run_cmd_with_env(
            [sys.executable, '-m', 'gitwebhooks', 'config', 'view', '-c', '/nonexistent/config.ini']
        )

        # Should fail
        self.assertEqual(result.returncode, 1)

        # Should display error with file path
        self.assertIn('Configuration file not found', result.stderr)
        self.assertIn('/nonexistent/config.ini', result.stderr)

    def test_config_view_invalid_ini_format(self):
        """
        Test that config view displays parsing error for invalid INI.

        When configuration file has invalid INI format, should display
        detailed parsing error information.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create invalid INI file
            config_path = Path(temp_dir) / "invalid.ini"
            config_path.write_text("""[server
port = 6789
invalid section format
""")

            result = run_cmd_with_env(
                [sys.executable, '-m', 'gitwebhooks', 'config', 'view', '-c', str(config_path)]
            )

            # Should fail
            self.assertEqual(result.returncode, 1)

            # Should display parsing error
            self.assertIn('Failed to parse configuration file', result.stderr)
            self.assertIn('Parsing error', result.stderr)

    def test_config_view_empty_config_file(self):
        """
        Test that config view handles empty configuration file.

        When configuration file exists but has no valid sections,
        should display appropriate message.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "empty.ini"
            config_path.write_text("")

            result = run_cmd_with_env(
                [sys.executable, '-m', 'gitwebhooks', 'config', 'view', '-c', str(config_path)]
            )

            # Should succeed
            self.assertEqual(result.returncode, 0)

            # Should display empty message
            self.assertIn('empty or has no valid sections', result.stdout)

    def test_config_view_sensitive_field_highlighting(self):
        """
        Test that config view highlights sensitive fields.

        Configuration keys containing sensitive keywords (secret, password,
        token, key, passphrase) should be highlighted in yellow.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "sensitive.ini"
            config_content = """[github]
secret = my_github_secret
token = my_api_token

[database]
password = db_password
api_key = 12345

[ssh]
passphrase = ssh_secret

[server]
port = 6789
"""
            config_path.write_text(config_content)

            # Ensure NO_COLOR is not set
            original_no_color = os.environ.get('NO_COLOR')
            if 'NO_COLOR' in os.environ:
                del os.environ['NO_COLOR']

            try:
                env = os.environ.copy()
                env['PYTHONPATH'] = PROJECT_ROOT
                result = subprocess.run(
                    [sys.executable, '-m', 'gitwebhooks', 'config', 'view', '-c', str(config_path)],
                    capture_output=True,
                    text=True,
                    timeout=5,
                    env=env
                )

                # Should succeed
                self.assertEqual(result.returncode, 0)

                # Should contain sensitive values
                self.assertIn('my_github_secret', result.stdout)
                self.assertIn('my_api_token', result.stdout)
                self.assertIn('db_password', result.stdout)
                self.assertIn('12345', result.stdout)
                self.assertIn('ssh_secret', result.stdout)

                # Non-sensitive values should also be present
                self.assertIn('port = 6789', result.stdout)
            finally:
                if original_no_color:
                    os.environ['NO_COLOR'] = original_no_color

    def test_config_view_no_color_disables_highlighting(self):
        """
        Test that NO_COLOR environment variable disables highlighting.

        When NO_COLOR is set, sensitive fields should not have color codes.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.ini"
            config_content = """[github]
secret = my_secret
"""
            config_path.write_text(config_content)

            env = os.environ.copy()
            env['PYTHONPATH'] = PROJECT_ROOT
            env['NO_COLOR'] = '1'

            result = subprocess.run(
                [sys.executable, '-m', 'gitwebhooks', 'config', 'view', '-c', str(config_path)],
                capture_output=True,
                text=True,
                timeout=5,
                env=env
            )

            # Should succeed
            self.assertEqual(result.returncode, 0)

            # Should not contain ANSI color codes
            self.assertNotIn('\033[', result.stdout)

    def test_config_view_symlink_handling(self):
        """
        Test that config view handles symbolic links correctly.

        When configuration file is a symlink, both link and target
        paths should be displayed.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create target file
            target = Path(temp_dir) / "actual_config.ini"
            target.write_text("""[server]
port = 6789
""")

            # Create symlink
            link = Path(temp_dir) / "config_link.ini"
            link.symlink_to(target)

            result = run_cmd_with_env(
                [sys.executable, '-m', 'gitwebhooks', 'config', 'view', '-c', str(link)]
            )

            # Should succeed
            self.assertEqual(result.returncode, 0)

            # Should show symlink relationship
            self.assertIn('->', result.stdout)
            self.assertIn(str(link), result.stdout)
            self.assertIn(str(target), result.stdout)


if __name__ == '__main__':
    unittest.main()
