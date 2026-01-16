"""Configuration-related data models

Provides data classes for configuration and service installation contexts.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from gitwebhooks.utils.constants import ConfigLevel
from gitwebhooks.utils.systemd import InstallationType


@dataclass
class ServiceInstallContext:
    """Service installation context

    Contains all information needed for service installation,
    including configuration level, paths, and installation type.

    Attributes:
        config_level: Configuration file level (user/local/system)
        config_path: Full path to configuration file
        install_type: Installation type (pipx/venv/virtualenv/system)
        use_python_module: Whether to use 'python -m' format
        cli_path: Path to gitwebhooks-cli executable
        python_path: Python interpreter path (required when use_python_module=True)
    """

    config_level: ConfigLevel
    config_path: Path
    install_type: InstallationType
    use_python_module: bool
    cli_path: str
    python_path: Optional[str] = None

    def __post_init__(self):
        """Validate the service installation context

        Raises:
            ValueError: If validation fails
        """
        # Ensure config_path is a Path object
        if isinstance(self.config_path, str):
            self.config_path = Path(self.config_path)

        # Validate use_python_module requires python_path
        if self.use_python_module and not self.python_path:
            raise ValueError(
                "python_path is required when use_python_module is True"
            )

        # Validate config_path is not empty
        if not self.config_path or str(self.config_path) == '.':
            raise ValueError("config_path cannot be empty")

    def get_exec_start_command(self) -> str:
        """Generate the ExecStart command for systemd service file

        Returns:
            Complete ExecStart command string
        """
        if self.use_python_module and self.python_path:
            return f"{self.python_path} -m gitwebhooks.main -c {self.config_path}"
        else:
            return f"{self.cli_path} -c {self.config_path}"

    def get_config_path_str(self) -> str:
        """Get configuration file path as string

        Returns:
            Configuration file path as string
        """
        return str(self.config_path)
