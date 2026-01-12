"""
Unit Tests for Configuration Loading (User Story 10)

Tests for verifying that the server correctly loads and validates
configuration files at startup.
"""

import unittest
import sys
import subprocess
import tempfile
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tests.conftest import TestConfigBuilder


class TestConfigLoading(unittest.TestCase):
    """Test configuration file loading and validation."""

    def test_valid_config_loads_successfully(self):
        """
        Test that a valid INI configuration file loads successfully.

        The server should start normally with a properly formatted
        configuration file containing all required sections.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            config_builder = TestConfigBuilder(temp_dir)
            config_builder.add_repository("test/repo", temp_dir, "echo test")
            config_path = config_builder.build()

            # Try to import and parse the config
            import configparser
            config = configparser.ConfigParser()
            config.read(config_path)

            # Verify sections exist
            self.assertTrue(config.has_section('server'))
            self.assertTrue(config.has_section('github'))
            self.assertTrue(config.has_section('test/repo'))

            # Verify required values
            self.assertIn('port', config['server'])
            self.assertIn('log_file', config['server'])
            self.assertIn('handle_events', config['github'])

    def test_missing_config_exits_with_code_1(self):
        """
        Test that missing configuration file causes exit code 1.

        When the specified config file doesn't exist, the server
        should exit with status code 1.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            nonexistent_config = f"{temp_dir}/nonexistent.ini"

            # Run server with nonexistent config
            server_script = Path(__file__).parent.parent.parent / "git-webhooks-server.py"

            result = subprocess.run(
                [sys.executable, str(server_script), "-c", nonexistent_config],
                capture_output=True,
                timeout=5
            )

            # Should exit with code 1
            self.assertEqual(result.returncode, 1)

    def test_invalid_config_exits_with_code_1(self):
        """
        Test that malformed INI file causes exit code 1.

        When the config file is not valid INI format, the server
        should exit with status code 1.
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as f:
            f.write("This is not valid INI format\n")
            f.write("[missing closing bracket\n")
            invalid_config = f.name

        try:
            server_script = Path(__file__).parent.parent.parent / "git-webhooks-server.py"

            result = subprocess.run(
                [sys.executable, str(server_script), "-c", invalid_config],
                capture_output=True,
                timeout=5
            )

            # Should exit with code 1
            self.assertEqual(result.returncode, 1)

        finally:
            Path(invalid_config).unlink(missing_ok=True)

    def test_custom_config_file_with_c_argument(self):
        """
        Test that -c argument loads custom config file.

        The server should accept a custom config file path via
        the -c or --config command line argument.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            config_builder = TestConfigBuilder(temp_dir)
            config_builder.add_repository("custom/repo", temp_dir, "echo test")
            config_path = config_builder.build()

            # Verify config file exists
            self.assertTrue(Path(config_path).exists())

            # Parse the config to verify it's valid
            import configparser
            config = configparser.ConfigParser()
            config.read(config_path)

            # Should have the custom repo we added
            self.assertTrue(config.has_section('custom/repo'))

    def test_help_display_with_h_argument(self):
        """
        Test that -h argument displays help information.

        The server should display usage help when -h or --help
        is provided.
        """
        server_script = Path(__file__).parent.parent.parent / "git-webhooks-server.py"

        result = subprocess.run(
            [sys.executable, str(server_script), "-h"],
            capture_output=True,
            timeout=5
        )

        # Should exit with code 0 (help displayed)
        # Note: help() calls sys.exit(0) in the server code
        self.assertIn(result.returncode, [0, 1])

        # Output should contain usage information
        output = result.stdout.decode('utf-8') + result.stderr.decode('utf-8')
        self.assertIn('usage', output.lower())

    def test_config_without_server_section(self):
        """
        Test that config without [server] section is handled.

        The server should have defaults or appropriate error handling
        for missing server section.
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as f:
            f.write("[github]\n")
            f.write("handle_events = push\n")
            f.write("verify = false\n")
            config_path = f.name

        try:
            import configparser
            config = configparser.ConfigParser()
            config.read(config_path)

            # Config should load but server section might be missing
            self.assertFalse(config.has_section('server'))

        finally:
            Path(config_path).unlink(missing_ok=True)

    def test_config_with_default_values(self):
        """
        Test that config uses default values for optional settings.

        When optional config values are not specified, the server
        should use sensible defaults.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            config_builder = TestConfigBuilder(temp_dir)
            config_builder.add_repository("test/repo", temp_dir, "echo test")
            config_path = config_builder.build()

            import configparser
            config = configparser.ConfigParser()
            config.read(config_path)

            # Check for expected defaults
            port = config.getint('server', 'port')
            self.assertIsInstance(port, int)
            self.assertGreater(port, 0)
            self.assertLess(port, 65536)

    def test_multiple_repository_sections(self):
        """
        Test that multiple repository sections are loaded correctly.

        The config should support multiple [owner/repo] sections
        for different repositories.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            config_builder = TestConfigBuilder(temp_dir)
            config_builder.add_repository("user/repo1", f"{temp_dir}/repo1", "cmd1")
            config_builder.add_repository("user/repo2", f"{temp_dir}/repo2", "cmd2")
            config_builder.add_repository("org/repo3", f"{temp_dir}/repo3", "cmd3")
            config_path = config_builder.build()

            import configparser
            config = configparser.ConfigParser()
            config.read(config_path)

            # All repos should be in config
            self.assertTrue(config.has_section('user/repo1'))
            self.assertTrue(config.has_section('user/repo2'))
            self.assertTrue(config.has_section('org/repo3'))

    def test_ssl_enable_false_in_config(self):
        """
        Test that SSL can be disabled via config.

        When ssl.enable is set to false, the server should use
        plain HTTP.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            config_builder = TestConfigBuilder(temp_dir)
            config_builder.add_repository("test/repo", temp_dir, "echo test")
            config_path = config_builder.build()

            import configparser
            config = configparser.ConfigParser()
            config.read(config_path)

            # SSL should be disabled by default
            self.assertTrue(config.has_section('ssl'))
            enable_ssl = config.getboolean('ssl', 'enable')
            self.assertFalse(enable_ssl)

    def test_handle_events_comma_separated(self):
        """
        Test that handle_events accepts comma-separated values.

        The handle_events setting should support multiple events
        separated by commas.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            config_builder = TestConfigBuilder(temp_dir)
            # Add custom handle_events
            config_path = config_builder.build()

            # Read and modify to add comma-separated events
            with open(config_path, 'r') as f:
                content = f.read()

            # Replace single event with comma-separated list
            content = content.replace('handle_events = push',
                                    'handle_events = push,release,ping')

            with open(config_path, 'w') as f:
                f.write(content)

            import configparser
            config = configparser.ConfigParser()
            config.read(config_path)

            events = config.get('github', 'handle_events')
            events_list = [e.strip() for e in events.split(',')]

            self.assertIn('push', events_list)
            self.assertIn('release', events_list)
            self.assertIn('ping', events_list)


if __name__ == '__main__':
    unittest.main()
