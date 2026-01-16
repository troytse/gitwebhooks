"""Unit tests for ServiceInstallContext dataclass

Tests the service installation context data model.
"""

import pytest
from pathlib import Path
from gitwebhooks.models.config import ServiceInstallContext
from gitwebhooks.utils.constants import ConfigLevel
from gitwebhooks.utils.systemd import InstallationType


class TestServiceInstallContext:
    """Test ServiceInstallContext dataclass"""

    def test_service_install_context_creation_with_all_fields(self):
        """Test creating ServiceInstallContext with all fields"""
        context = ServiceInstallContext(
            config_level=ConfigLevel.USER,
            config_path=Path("~/.gitwebhooks.ini"),
            install_type=InstallationType.PIPX,
            use_python_module=False,
            cli_path="/usr/local/bin/gitwebhooks-cli",
            python_path=None
        )

        assert context.config_level == ConfigLevel.USER
        assert context.config_path == Path("~/.gitwebhooks.ini")
        assert context.install_type == InstallationType.PIPX
        assert context.use_python_module is False
        assert context.cli_path == "/usr/local/bin/gitwebhooks-cli"
        assert context.python_path is None

    def test_service_install_context_with_python_module(self):
        """Test creating ServiceInstallContext with python module"""
        context = ServiceInstallContext(
            config_level=ConfigLevel.LOCAL,
            config_path="/usr/local/etc/gitwebhooks.ini",
            install_type=InstallationType.VENV,
            use_python_module=True,
            cli_path="/usr/local/bin/gitwebhooks-cli",
            python_path="/usr/bin/python3"
        )

        assert context.use_python_module is True
        assert context.python_path == "/usr/bin/python3"

    def test_service_install_context_validates_python_module_requirement(self):
        """Test that use_python_module=True requires python_path"""
        with pytest.raises(ValueError) as exc_info:
            ServiceInstallContext(
                config_level=ConfigLevel.USER,
                config_path="~/.gitwebhooks.ini",
                install_type=InstallationType.VENV,
                use_python_module=True,
                cli_path="/usr/local/bin/gitwebhooks-cli",
                python_path=None
            )

        assert "python_path is required" in str(exc_info.value)

    def test_service_install_context_validates_config_path_not_empty(self):
        """Test that config_path cannot be empty"""
        with pytest.raises(ValueError) as exc_info:
            ServiceInstallContext(
                config_level=ConfigLevel.USER,
                config_path=".",
                install_type=InstallationType.PIPX,
                use_python_module=False,
                cli_path="/usr/local/bin/gitwebhooks-cli"
            )

        assert "config_path cannot be empty" in str(exc_info.value)

    def test_service_install_context_converts_string_config_path(self):
        """Test that string config_path is converted to Path"""
        context = ServiceInstallContext(
            config_level=ConfigLevel.SYSTEM,
            config_path="/etc/gitwebhooks.ini",
            install_type=InstallationType.SYSTEM_PIP,
            use_python_module=False,
            cli_path="/usr/local/bin/gitwebhooks-cli"
        )

        assert isinstance(context.config_path, Path)

    def test_get_exec_start_command_with_cli(self):
        """Test get_exec_start_command() returns CLI command"""
        context = ServiceInstallContext(
            config_level=ConfigLevel.USER,
            config_path="~/.gitwebhooks.ini",
            install_type=InstallationType.PIPX,
            use_python_module=False,
            cli_path="/usr/local/bin/gitwebhooks-cli"
        )

        command = context.get_exec_start_command()
        assert command == "/usr/local/bin/gitwebhooks-cli -c ~/.gitwebhooks.ini"

    def test_get_exec_start_command_with_python_module(self):
        """Test get_exec_start_command() returns python -m command"""
        context = ServiceInstallContext(
            config_level=ConfigLevel.LOCAL,
            config_path="/usr/local/etc/gitwebhooks.ini",
            install_type=InstallationType.VENV,
            use_python_module=True,
            cli_path="/usr/local/bin/gitwebhooks-cli",
            python_path="/home/user/venv/bin/python"
        )

        command = context.get_exec_start_command()
        assert command == "/home/user/venv/bin/python -m gitwebhooks.main -c /usr/local/etc/gitwebhooks.ini"

    def test_get_config_path_str(self):
        """Test get_config_path_str() returns string path"""
        context = ServiceInstallContext(
            config_level=ConfigLevel.SYSTEM,
            config_path="/etc/gitwebhooks.ini",
            install_type=InstallationType.SYSTEM_PIP,
            use_python_module=False,
            cli_path="/usr/local/bin/gitwebhooks-cli"
        )

        path_str = context.get_config_path_str()
        assert path_str == "/etc/gitwebhooks.ini"
        assert isinstance(path_str, str)


class TestServiceInstallContextIntegration:
    """Integration tests for ServiceInstallContext with ConfigLevel"""

    def test_context_with_each_config_level(self):
        """Test ServiceInstallContext works with all config levels"""
        for level in ConfigLevel:
            context = ServiceInstallContext(
                config_level=level,
                config_path=level.get_config_path(),
                install_type=InstallationType.PIPX,
                use_python_module=False,
                cli_path="/usr/local/bin/gitwebhooks-cli"
            )

            assert context.config_level == level
            assert context.config_path == level.get_config_path()
            assert isinstance(context.get_config_path_str(), str)
