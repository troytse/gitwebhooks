"""
Unit Tests for Configuration View Command (User Stories 1, 2, 3)

Tests for verifying the config view command functionality including
file location, content display, error handling, and sensitive field highlighting.
"""

import unittest
import sys
import tempfile
import argparse
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from gitwebhooks.cli.config import (
    locate_config_file,
    cmd_view,
    format_config_header,
    format_config_content,
    is_sensitive_key,
    should_use_color,
    format_sensitive_field
)
from gitwebhooks.utils.constants import (
    CONFIG_SEARCH_PATHS,
    SENSITIVE_KEYWORDS,
    COLOR_SENSITIVE,
    COLOR_RESET
)


class TestLocateConfigFile(unittest.TestCase):
    """Test configuration file location logic."""

    def test_locate_config_file_with_user_specified_path(self):
        """
        Test that locate_config_file() returns the user-specified path when -c is used.

        When a user specifies a configuration file path with -c argument,
        that path should be returned directly if it exists.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a test config file
            config_path = Path(temp_dir) / "test_config.ini"
            config_path.write_text("[server]\nport = 6789\n")

            # Create args with config path
            args = argparse.Namespace(config=str(config_path))

            # Locate config
            result = locate_config_file(args)

            # Verify the correct path is returned
            self.assertEqual(result, config_path)

    def test_locate_config_file_priority_order(self):
        """
        Test that locate_config_file() searches paths in correct priority order.

        The function should search for configuration files in the following order:
        1. ~/.gitwebhooks.ini (user home)
        2. /usr/local/etc/gitwebhooks.ini (system local)
        3. /etc/gitwebhooks.ini (system global)
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create mock config files in temp directory
            user_config = Path(temp_dir) / "user_config.ini"
            local_config = Path(temp_dir) / "local_config.ini"
            system_config = Path(temp_dir) / "system_config.ini"

            user_config.write_text("[user]\n")
            local_config.write_text("[local]\n")
            system_config.write_text("[system]\n")

            # Create args without -c (auto-detect mode)
            args = argparse.Namespace(config=None)

            # Mock CONFIG_SEARCH_PATHS to use our temp files
            import gitwebhooks.cli.config as config_module
            original_paths = config_module.CONFIG_SEARCH_PATHS
            config_module.CONFIG_SEARCH_PATHS = [str(user_config), str(local_config), str(system_config)]

            try:
                # Should find the first (user) config
                result = locate_config_file(args)
                self.assertEqual(result, user_config)

                # Remove user config, should find local
                user_config.unlink()
                result = locate_config_file(args)
                self.assertEqual(result, local_config)

                # Remove local config, should find system
                local_config.unlink()
                result = locate_config_file(args)
                self.assertEqual(result, system_config)

                # Remove all, should return None
                system_config.unlink()
                result = locate_config_file(args)
                self.assertIsNone(result)
            finally:
                config_module.CONFIG_SEARCH_PATHS = original_paths

    def test_locate_config_file_nonexistent_user_path(self):
        """
        Test that locate_config_file() returns None when -c specifies nonexistent file.

        When user specifies a path with -c that doesn't exist,
        the function should return None (not fall back to auto-detection).
        """
        args = argparse.Namespace(config="/nonexistent/path/config.ini")
        result = locate_config_file(args)
        self.assertIsNone(result)


class TestFormatConfigHeader(unittest.TestCase):
    """Test configuration header formatting."""

    def test_format_config_header_user_specified(self):
        """
        Test that format_config_header() correctly formats user-specified config.

        Header should show: Config File: <path> (source: user-specified)
        """
        config_path = Path("/custom/path/config.ini")
        result = format_config_header(config_path, "user-specified")
        self.assertEqual(result, "Config File: /custom/path/config.ini (source: user-specified)")

    def test_format_config_header_auto_detected(self):
        """
        Test that format_config_header() correctly formats auto-detected config.

        Header should show: Config File: <path> (source: auto-detected)
        """
        config_path = Path("/home/user/.gitwebhooks.ini")
        result = format_config_header(config_path, "auto-detected")
        self.assertEqual(result, "Config File: /home/user/.gitwebhooks.ini (source: auto-detected)")

    def test_format_config_header_with_symlink(self):
        """
        Test that format_config_header() displays symlink target.

        When config file is a symlink, both the link path and target
        should be displayed: link -> target
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create target file
            target = Path(temp_dir) / "actual_config.ini"
            target.write_text("[server]\nport = 6789\n")

            # Create symlink
            link = Path(temp_dir) / "config_link.ini"
            link.symlink_to(target)

            result = format_config_header(link, "auto-detected")

            # Should show link -> target
            self.assertIn("->", result)
            self.assertIn(str(link), result)
            self.assertIn(str(target), result)


class TestFormatConfigContent(unittest.TestCase):
    """Test configuration content formatting."""

    def test_format_config_content_with_sections(self):
        """
        Test that format_config_content() correctly formats config with sections.

        Configuration should be displayed with section headers and key=value pairs.
        """
        import configparser

        parser = configparser.ConfigParser()
        parser.add_section('server')
        parser.set('server', 'address', '0.0.0.0')
        parser.set('server', 'port', '6789')
        parser.add_section('github')
        parser.set('github', 'secret', 'my_secret')

        result = format_config_content(parser)

        self.assertIn('[server]', result)
        self.assertIn('address = 0.0.0.0', result)
        self.assertIn('port = 6789', result)
        self.assertIn('[github]', result)
        # The secret value may be wrapped in ANSI color codes
        self.assertIn('my_secret', result)

    def test_format_config_content_empty(self):
        """
        Test that format_config_content() handles empty configuration.

        When configuration has no sections, should return appropriate message.
        """
        import configparser

        parser = configparser.ConfigParser()
        result = format_config_content(parser)

        self.assertEqual(result, '(Configuration file is empty or has no valid sections)')


class TestIsSensitiveKey(unittest.TestCase):
    """Test sensitive key detection."""

    def test_is_sensitive_key_detects_secret(self):
        """
        Test that is_sensitive_key() detects keys containing 'secret'.

        Keys with 'secret' in any case should be identified as sensitive.
        """
        self.assertTrue(is_sensitive_key('secret'))
        self.assertTrue(is_sensitive_key('webhook_secret'))
        self.assertTrue(is_sensitive_key('SECRET'))
        self.assertTrue(is_sensitive_key('mySecretKey'))

    def test_is_sensitive_key_detects_password(self):
        """
        Test that is_sensitive_key() detects keys containing 'password'.

        Keys with 'password' in any case should be identified as sensitive.
        """
        self.assertTrue(is_sensitive_key('password'))
        self.assertTrue(is_sensitive_key('db_password'))
        self.assertTrue(is_sensitive_key('PASSWORD'))
        self.assertTrue(is_sensitive_key('myPassword'))

    def test_is_sensitive_key_detects_token(self):
        """
        Test that is_sensitive_key() detects keys containing 'token'.

        Keys with 'token' in any case should be identified as sensitive.
        """
        self.assertTrue(is_sensitive_key('token'))
        self.assertTrue(is_sensitive_key('api_token'))
        self.assertTrue(is_sensitive_key('TOKEN'))
        self.assertTrue(is_sensitive_key('accessToken'))

    def test_is_sensitive_key_detects_key(self):
        """
        Test that is_sensitive_key() detects keys containing 'key'.

        Keys with 'key' in any case should be identified as sensitive.
        """
        self.assertTrue(is_sensitive_key('key'))
        self.assertTrue(is_sensitive_key('api_key'))
        self.assertTrue(is_sensitive_key('private_key'))
        self.assertTrue(is_sensitive_key('KEY'))
        self.assertTrue(is_sensitive_key('myKey'))

    def test_is_sensitive_key_detects_passphrase(self):
        """
        Test that is_sensitive_key() detects keys containing 'passphrase'.

        Keys with 'passphrase' in any case should be identified as sensitive.
        """
        self.assertTrue(is_sensitive_key('passphrase'))
        self.assertTrue(is_sensitive_key('ssh_passphrase'))
        self.assertTrue(is_sensitive_key('PASSPHRASE'))
        self.assertTrue(is_sensitive_key('myPassphrase'))

    def test_is_sensitive_key_non_sensitive(self):
        """
        Test that is_sensitive_key() returns False for non-sensitive keys.

        Keys without sensitive keywords should not be flagged.
        """
        self.assertFalse(is_sensitive_key('port'))
        self.assertFalse(is_sensitive_key('address'))
        self.assertFalse(is_sensitive_key('log_file'))
        self.assertFalse(is_sensitive_key('handle_events'))


class TestShouldUseColor(unittest.TestCase):
    """Test color output detection."""

    def test_should_use_color_defaults_true(self):
        """
        Test that should_use_color() returns True by default.

        When NO_COLOR is not set and TERM is not 'dumb', color should be enabled.
        """
        # Ensure NO_COLOR is not set
        original_no_color = os.environ.get('NO_COLOR')
        original_term = os.environ.get('TERM')

        if 'NO_COLOR' in os.environ:
            del os.environ['NO_COLOR']
        if 'TERM' in os.environ:
            del os.environ['TERM']

        try:
            result = should_use_color()
            self.assertTrue(result)
        finally:
            if original_no_color:
                os.environ['NO_COLOR'] = original_no_color
            if original_term:
                os.environ['TERM'] = original_term

    def test_should_use_color_with_no_color_env(self):
        """
        Test that should_use_color() returns False when NO_COLOR is set.

        Setting the NO_COLOR environment variable should disable color output.
        """
        os.environ['NO_COLOR'] = '1'
        try:
            result = should_use_color()
            self.assertFalse(result)
        finally:
            del os.environ['NO_COLOR']

    def test_should_use_color_with_dumb_term(self):
        """
        Test that should_use_color() returns False when TERM=dumb.

        Terminals that don't support color should be detected.
        """
        original_term = os.environ.get('TERM')
        os.environ['TERM'] = 'dumb'
        try:
            result = should_use_color()
            self.assertFalse(result)
        finally:
            if original_term:
                os.environ['TERM'] = original_term
            else:
                del os.environ['TERM']


class TestFormatSensitiveField(unittest.TestCase):
    """Test sensitive field formatting."""

    def test_format_sensitive_field_with_color(self):
        """
        Test that format_sensitive_field() applies color codes for sensitive keys.

        Sensitive fields should be wrapped with ANSI color codes when enabled.
        """
        # Ensure color is enabled
        original_no_color = os.environ.get('NO_COLOR')
        if 'NO_COLOR' in os.environ:
            del os.environ['NO_COLOR']
        if 'TERM' in os.environ:
            del os.environ['TERM']

        try:
            result = format_sensitive_field('secret', 'my_secret_value')
            self.assertIn(COLOR_SENSITIVE, result)
            self.assertIn(COLOR_RESET, result)
            self.assertIn('my_secret_value', result)
        finally:
            if original_no_color:
                os.environ['NO_COLOR'] = original_no_color

    def test_format_sensitive_field_without_color(self):
        """
        Test that format_sensitive_field() skips color when disabled.

        When color output is disabled (NO_COLOR set), should return plain value.
        """
        os.environ['NO_COLOR'] = '1'
        try:
            result = format_sensitive_field('secret', 'my_secret_value')
            self.assertNotIn(COLOR_SENSITIVE, result)
            self.assertNotIn(COLOR_RESET, result)
            self.assertEqual(result, 'my_secret_value')
        finally:
            del os.environ['NO_COLOR']

    def test_format_sensitive_field_non_sensitive(self):
        """
        Test that format_sensitive_field() doesn't color non-sensitive keys.

        Non-sensitive fields should not have color applied.
        """
        # Ensure color is enabled
        if 'NO_COLOR' in os.environ:
            del os.environ['NO_COLOR']
        if 'TERM' in os.environ:
            del os.environ['TERM']

        result = format_sensitive_field('port', '6789')
        self.assertNotIn(COLOR_SENSITIVE, result)
        self.assertNotIn(COLOR_RESET, result)
        self.assertEqual(result, '6789')


if __name__ == '__main__':
    unittest.main()
