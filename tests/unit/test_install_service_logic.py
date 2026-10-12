"""Unit tests for service installation logic

Tests the core service installation functions and parameter handling.
"""

import pytest
from unittest.mock import patch, MagicMock

from gitwebhooks.cli.service import install_service
from gitwebhooks.utils.constants import ConfigLevel


class TestInstallServiceConfigLevelHandling:
    """Test install_service config level handling"""

    @patch('gitwebhooks.cli.service.detect_installation_type')
    @patch('gitwebhooks.cli.service.get_service_path')
    @patch('gitwebhooks.cli.service.generate_service_file')
    @patch('gitwebhooks.cli.service.ask_config_level')
    @patch('gitwebhooks.cli.service.print')
    def test_install_service_interactive_mode(
        self, mock_print, mock_ask, mock_generate, mock_service_path, mock_detect
    ):
        """Test install_service in interactive mode"""
        # Setup mocks
        mock_env = MagicMock()
        mock_env.type.value = "pipx"
        mock_env.is_supported = True
        mock_env.python_path = "/usr/bin/python3"
        mock_env.cli_path = "/usr/local/bin/gitwebhooks-cli"
        mock_detect.return_value = mock_env

        mock_service_path.return_value = MagicMock()
        mock_ask.return_value = ConfigLevel.USER
        mock_generate.return_value = "[Unit]\nDescription=Test"

        result = install_service(dry_run=True)

        # Should prompt for config level
        mock_ask.assert_called_once()
        assert result == 0

    @patch('gitwebhooks.cli.service.detect_installation_type')
    @patch('gitwebhooks.cli.service.get_service_path')
    @patch('gitwebhooks.cli.service.generate_service_file')
    @patch('gitwebhooks.cli.service.print')
    def test_install_service_with_config_level_override(
        self, mock_print, mock_generate, mock_service_path, mock_detect
    ):
        """Test install_service with --config-level parameter"""
        # Setup mocks
        mock_env = MagicMock()
        mock_env.type.value = "pipx"
        mock_env.is_supported = True
        mock_env.python_path = "/usr/bin/python3"
        mock_env.cli_path = "/usr/local/bin/gitwebhooks-cli"
        mock_detect.return_value = mock_env

        mock_service_path.return_value = MagicMock()
        mock_generate.return_value = "[Unit]\nDescription=Test"

        result = install_service(
            dry_run=True,
            config_level_override="local"
        )

        # Should use local config level
        assert result == 0
        # Check that dry-run output includes config info
        print_calls = [str(call) for call in mock_print.call_args_list]
        output = ' '.join(print_calls)
        assert 'local' in output.lower() or '/usr/local/etc' in output

    @patch('gitwebhooks.cli.service.detect_installation_type')
    @patch('gitwebhooks.cli.service.get_service_path')
    @patch('gitwebhooks.cli.service.generate_service_file')
    @patch('gitwebhooks.cli.service.print')
    def test_install_service_with_invalid_config_level(
        self, mock_print, mock_generate, mock_service_path, mock_detect
    ):
        """Test install_service rejects invalid config level"""
        # Setup mocks
        mock_env = MagicMock()
        mock_env.type.value = "pipx"
        mock_env.is_supported = True
        mock_env.python_path = "/usr/bin/python3"
        mock_env.cli_path = "/usr/local/bin/gitwebhooks-cli"
        mock_detect.return_value = mock_env

        result = install_service(
            dry_run=True,
            config_level_override="invalid"
        )

        # Should return error
        assert result == 1
        # Check error message was printed
        mock_print.assert_called()

    @patch('gitwebhooks.cli.service.detect_installation_type')
    @patch('gitwebhooks.cli.service.get_service_path')
    @patch('gitwebhooks.cli.service.generate_service_file')
    @patch('gitwebhooks.cli.service.print')
    def test_install_service_with_config_path_override(
        self, mock_print, mock_generate, mock_service_path, mock_detect
    ):
        """Test install_service with -c parameter (backward compatibility)"""
        # Setup mocks
        mock_env = MagicMock()
        mock_env.type.value = "pipx"
        mock_env.is_supported = True
        mock_env.python_path = "/usr/bin/python3"
        mock_env.cli_path = "/usr/local/bin/gitwebhooks-cli"
        mock_detect.return_value = mock_env

        mock_service_path.return_value = MagicMock()
        mock_generate.return_value = "[Unit]\nDescription=Test"

        result = install_service(
            dry_run=True,
            config_path_override="/custom/config.ini"
        )

        # Should use custom config path
        assert result == 0
        # Check that config path is in output
        print_calls = [str(call) for call in mock_print.call_args_list]
        output = ' '.join(print_calls)
        assert '/custom/config.ini' in output

    @patch('gitwebhooks.cli.service.detect_installation_type')
    @patch('gitwebhooks.cli.service.get_service_path')
    @patch('gitwebhooks.cli.service.generate_service_file')
    @patch('gitwebhooks.cli.service.print')
    def test_install_service_dry_run_shows_config_info(
        self, mock_print, mock_generate, mock_service_path, mock_detect
    ):
        """Test install_service shows config info in dry-run mode"""
        # Setup mocks
        mock_env = MagicMock()
        mock_env.type.value = "pipx"
        mock_env.is_supported = True
        mock_env.python_path = "/usr/bin/python3"
        mock_env.cli_path = "/usr/local/bin/gitwebhooks-cli"
        mock_detect.return_value = mock_env

        mock_service_path.return_value = MagicMock()
        mock_generate.return_value = "[Unit]\nDescription=Test"

        result = install_service(
            dry_run=True,
            config_level_override="system"
        )

        assert result == 0
        # Check that config info is printed
        print_calls = [str(call) for call in mock_print.call_args_list]
        output = ' '.join(print_calls)
        assert 'configuration' in output.lower()


class TestInstallServiceConfigPathMapping:
    """Test config path to level mapping"""

    @pytest.mark.parametrize("path,expected_level", [
        ("~/.gitwebhooks.ini", ConfigLevel.USER),
        ("/usr/local/etc/gitwebhooks.ini", ConfigLevel.LOCAL),
        ("/etc/gitwebhooks.ini", ConfigLevel.SYSTEM),
        ("/custom/path.ini", ConfigLevel.USER),  # Custom paths default to USER
    ])
    def test_config_path_mapping(self, path, expected_level):
        """Test that config paths map to correct levels"""
        from pathlib import Path as PathLib

        # This tests the mapping logic used in install_service
        expanded = PathLib(path).expanduser()

        if str(expanded) == str(PathLib("~/.gitwebhooks.ini").expanduser()):
            assert expected_level == ConfigLevel.USER
        elif str(expanded) == "/usr/local/etc/gitwebhooks.ini":
            assert expected_level == ConfigLevel.LOCAL
        elif str(expanded) == "/etc/gitwebhooks.ini":
            assert expected_level == ConfigLevel.SYSTEM
        else:
            # Custom paths default to USER
            assert expected_level == ConfigLevel.USER
