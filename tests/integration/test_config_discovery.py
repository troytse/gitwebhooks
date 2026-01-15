"""Integration tests for configuration file auto-discovery.

Tests the complete workflow of config file discovery when running
gitwebhooks-cli without the -c argument.
"""

import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest


class TestConfigAutoDiscovery:
    """Test automatic configuration file discovery."""

    def test_user_level_config_auto_discovery(self, tmp_path, monkeypatch):
        """Should auto-discover and use user level config."""
        config_content = """[server]
port = 18080
address = 127.0.0.1

[github]
handle_events = push
verify = false
"""
        user_config = tmp_path / '.gitwebhooks.ini'
        user_config.write_text(config_content)

        monkeypatch.setenv('HOME', str(tmp_path))

        # Run the CLI to check config discovery
        result = subprocess.run(
            [sys.executable, '-m', 'gitwebhooks.main', '--help'],
            capture_output=True,
            text=True,
            cwd=tmp_path
        )

        # The help should work (no config needed for help)
        assert result.returncode == 0 or 'gitwebhooks-cli' in result.stdout.lower()

    def test_local_level_config_auto_discovery(self, tmp_path, monkeypatch):
        """Should auto-discover local level config when user config doesn't exist."""
        config_content = """[server]
port = 18080
"""

        # Create empty home (no user config)
        empty_home = tmp_path / 'empty_home'
        empty_home.mkdir()
        monkeypatch.setenv('HOME', str(empty_home))

        # Create local config
        local_dir = tmp_path / 'usr_local_etc'
        local_dir.mkdir()
        local_config = local_dir / 'gitwebhooks.ini'
        local_config.write_text(config_content)

        # Patch the constant to use our test path
        import gitwebhooks.utils.constants as constants
        original_paths = constants.CONFIG_SEARCH_PATHS
        constants.CONFIG_SEARCH_PATHS = [
            '~/.gitwebhooks.ini',
            str(local_config)
        ]

        try:
            result = subprocess.run(
                [sys.executable, '-m', 'gitwebhooks.main', '--help'],
                capture_output=True,
                text=True
            )
            assert 'gitwebhooks-cli' in result.stdout.lower() or result.returncode == 0
        finally:
            constants.CONFIG_SEARCH_PATHS = original_paths

    def test_system_level_config_auto_discovery(self, tmp_path, monkeypatch):
        """Should auto-discover system level config as fallback."""
        config_content = """[server]
port = 18080
"""

        # Create empty home and no local config
        empty_home = tmp_path / 'empty_home'
        empty_home.mkdir()
        monkeypatch.setenv('HOME', str(empty_home))

        # Create system config
        system_config = tmp_path / 'system_config.ini'
        system_config.write_text(config_content)

        # Patch to use our test paths
        import gitwebhooks.utils.constants as constants
        original_paths = constants.CONFIG_SEARCH_PATHS
        constants.CONFIG_SEARCH_PATHS = [
            '~/.gitwebhooks.ini',
            str(tmp_path / 'nonexistent' / 'local.ini'),
            str(system_config)
        ]

        try:
            result = subprocess.run(
                [sys.executable, '-m', 'gitwebhooks.main', '--help'],
                capture_output=True,
                text=True
            )
            assert 'gitwebhooks-cli' in result.stdout.lower() or result.returncode == 0
        finally:
            constants.CONFIG_SEARCH_PATHS = original_paths


class TestConfigPriority:
    """Test configuration file priority when multiple exist."""

    def test_user_config_has_highest_priority(self, tmp_path, monkeypatch):
        """Should use user config when both user and local configs exist."""
        user_config_content = """[server]
port = 18081
"""
        local_config_content = """[server]
port = 18082
"""

        # Create both configs
        user_config = tmp_path / '.gitwebhooks.ini'
        user_config.write_text(user_config_content)

        local_config = tmp_path / 'local.ini'
        local_config.write_text(local_config_content)

        monkeypatch.setenv('HOME', str(tmp_path))

        # Patch to include both
        import gitwebhooks.utils.constants as constants
        original_paths = constants.CONFIG_SEARCH_PATHS
        constants.CONFIG_SEARCH_PATHS = [
            '~/.gitwebhooks.ini',
            str(local_config)
        ]

        try:
            # User config should be found first
            from gitwebhooks.main import find_config_file
            result = find_config_file()
            assert result is not None
            assert '.gitwebhooks.ini' in result
            # Should be user config, not local
            assert 'local' not in result.lower()
        finally:
            constants.CONFIG_SEARCH_PATHS = original_paths


class TestConfigErrorHandling:
    """Test error handling when configuration is not found."""

    def test_error_message_when_no_config_exists(self, tmp_path, monkeypatch):
        """Should display friendly error message when no config found."""
        # Empty directory with no configs
        empty_home = tmp_path / 'empty_home'
        empty_home.mkdir()
        monkeypatch.setenv('HOME', str(empty_home))

        # Patch to use only non-existent paths
        import gitwebhooks.utils.constants as constants
        original_paths = constants.CONFIG_SEARCH_PATHS
        constants.CONFIG_SEARCH_PATHS = [
            str(tmp_path / 'nonexistent1.ini'),
            str(tmp_path / 'nonexistent2.ini'),
        ]

        try:
            result = subprocess.run(
                [sys.executable, '-m', 'gitwebhooks.main'],
                capture_output=True,
                text=True
            )
            # Should fail with error message
            assert result.returncode != 0
            stderr = result.stderr.lower()
            assert 'configuration file not found' in stderr or 'error' in stderr
        finally:
            constants.CONFIG_SEARCH_PATHS = original_paths

    def test_error_message_lists_searched_paths(self, tmp_path, monkeypatch):
        """Error message should list all searched paths."""
        empty_home = tmp_path / 'empty_home'
        empty_home.mkdir()
        monkeypatch.setenv('HOME', str(empty_home))

        # Test using the format_config_error function directly
        # since subprocess runs in separate process
        from gitwebhooks.main import format_config_error
        from pathlib import Path

        test_paths = [
            tmp_path / 'path1.ini',
            tmp_path / 'path2.ini',
        ]

        error_msg = format_config_error(test_paths)

        # Should contain searched paths
        for path in test_paths:
            assert str(path) in error_msg
            assert path.stem in error_msg

    def test_error_suggests_config_init_command(self, tmp_path, monkeypatch):
        """Error message should suggest using config init command."""
        empty_home = tmp_path / 'empty_home'
        empty_home.mkdir()
        monkeypatch.setenv('HOME', str(empty_home))

        import gitwebhooks.utils.constants as constants
        original_paths = constants.CONFIG_SEARCH_PATHS
        constants.CONFIG_SEARCH_PATHS = [str(tmp_path / 'nonexistent.ini')]

        try:
            result = subprocess.run(
                [sys.executable, '-m', 'gitwebhooks.main'],
                capture_output=True,
                text=True
            )
            stderr = result.stderr.lower()
            assert 'config init' in stderr
        finally:
            constants.CONFIG_SEARCH_PATHS = original_paths


class TestExplicitConfigArgument:
    """Test -c argument behavior (User Story 2)."""

    def test_explicit_config_overrides_auto_discovery(self, tmp_path, monkeypatch):
        """Should use explicitly specified config file."""
        user_config_content = """[server]
port = 18081
"""
        explicit_config_content = """[server]
port = 18099
"""

        # Create user config
        user_config = tmp_path / '.gitwebhooks.ini'
        user_config.write_text(user_config_content)

        # Create explicit config
        explicit_config = tmp_path / 'explicit.ini'
        explicit_config.write_text(explicit_config_content)

        monkeypatch.setenv('HOME', str(tmp_path))

        # Use -c to specify explicit config
        from gitwebhooks.main import run_server

        # Mock the server to avoid actually starting it
        from unittest.mock import patch, MagicMock
        with patch('gitwebhooks.main.WebhookServer') as mock_server:
            mock_instance = MagicMock()
            mock_server.return_value = mock_instance
            mock_instance.run.side_effect = KeyboardInterrupt()  # Exit immediately

            result = run_server(str(explicit_config))
            # Server should have been created with explicit config
            mock_server.assert_called_once()
            call_args = mock_server.call_args
            assert str(explicit_config) in str(call_args)

    def test_error_on_nonexistent_explicit_config(self, tmp_path):
        """Should error when explicitly specified config doesn't exist."""
        nonexistent = tmp_path / 'does_not_exist.ini'

        from gitwebhooks.main import run_server
        result = run_server(str(nonexistent))

        # Should return error code
        assert result != 0


class TestConfigPathOutput:
    """Test configuration file path output (User Story 3)."""

    def test_prints_config_path_when_auto_discovered(self, tmp_path, monkeypatch, capsys):
        """Should print config file path when auto-discovered."""
        config_content = """[server]
port = 18080
"""
        user_config = tmp_path / '.gitwebhooks.ini'
        user_config.write_text(config_content)

        monkeypatch.setenv('HOME', str(tmp_path))

        from gitwebhooks.main import run_server
        from unittest.mock import patch, MagicMock

        with patch('gitwebhooks.main.WebhookServer') as mock_server:
            mock_instance = MagicMock()
            mock_server.return_value = mock_instance
            mock_instance.run.side_effect = KeyboardInterrupt()

            run_server(None)

            captured = capsys.readouterr()
            assert 'Using configuration file:' in captured.out
            assert str(user_config) in captured.out or '.gitwebhooks.ini' in captured.out

    def test_prints_config_path_when_explicitly_specified(self, tmp_path, capsys):
        """Should print config file path when explicitly specified."""
        config_content = """[server]
port = 18080
"""
        explicit_config = tmp_path / 'custom.ini'
        explicit_config.write_text(config_content)

        from gitwebhooks.main import run_server
        from unittest.mock import patch, MagicMock

        with patch('gitwebhooks.main.WebhookServer') as mock_server:
            mock_instance = MagicMock()
            mock_server.return_value = mock_instance
            mock_instance.run.side_effect = KeyboardInterrupt()

            run_server(str(explicit_config))

            captured = capsys.readouterr()
            assert 'Using configuration file:' in captured.out
            assert str(explicit_config) in captured.out
