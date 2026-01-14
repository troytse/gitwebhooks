"""systemd service utilities

Provides functions for generating and managing systemd service files.
"""

import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional, List


class InstallationType(Enum):
    """Installation type enumeration

    Represents the method used to install git-webhooks-server.
    """
    PIPX = "pipx"          # Installed via pipx (recommended)
    VENV = "venv"          # Python standard library venv
    VIRTUALENV = "virtualenv"  # Third-party virtualenv tool
    SYSTEM_PIP = "system"  # System pip installation (not recommended)
    CONDA = "conda"        # Conda environment (not supported)
    UNKNOWN = "unknown"    # Unable to detect


@dataclass
class InstallationEnvironment:
    """Installation environment detection result

    Contains information about the current installation environment,
    including type, paths, and support status.
    """
    type: InstallationType
    python_path: str
    cli_path: str
    venv_root: Optional[str] = None
    detection_methods: List[str] = None
    is_supported: bool = True
    error_message: Optional[str] = None

    def __post_init__(self):
        if self.detection_methods is None:
            self.detection_methods = []


# Service file template
SERVICE_TEMPLATE = """[Unit]
Description=Git Webhooks Server
Documentation=https://github.com/troytse/git-webhooks-server
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart={exec_start}
Restart=on-failure
RestartSec=1min
StandardOutput=journal
StandardError=journal

# Security settings
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
"""


def detect_python_interpreter() -> str:
    """Detect the current Python interpreter path

    Uses a three-tier fallback strategy:
    1. sys.executable (most reliable, includes venv path automatically)
    2. shutil.which('python3') or shutil.which('python')
    3. Hardcoded '/usr/bin/python3' (last resort)

    Returns:
        Absolute path to the Python interpreter
    """
    # Priority 1: Use sys.executable (most reliable)
    if sys.executable:
        return sys.executable

    # Priority 2: Use which to find python
    python_path = shutil.which('python3') or shutil.which('python')
    if python_path:
        return python_path

    # Priority 3: Hardcoded fallback
    return '/usr/bin/python3'


def detect_installation_type(cli_path: Optional[str] = None) -> InstallationEnvironment:
    """Detect the current installation environment type

    Detection priority order:
    1. CONDA - Check CONDA_PREFIX environment variable (must reject)
    2. PIPX - Check if ~/.local/pipx/venvs/gitwebhooks-server exists
    3. VENV - Check sys.base_prefix != sys.prefix and pyvenv.cfg exists
    4. VIRTUALENV - Check sys.real_prefix attribute
    5. SYSTEM_PIP - Default fallback

    Args:
        cli_path: Optional path to gitwebhooks-cli (auto-detected if not provided)

    Returns:
        InstallationEnvironment instance with detected type and paths
    """
    detection_methods = []

    # Auto-detect CLI path if not provided
    if cli_path is None:
        try:
            result = subprocess.run(
                ['which', 'gitwebhooks-cli'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                cli_path = result.stdout.strip()
                detection_methods.append('which gitwebhooks-cli')
        except (subprocess.TimeoutExpired, FileNotFoundError):
            cli_path = '/usr/local/bin/gitwebhooks-cli'

    # Check conda (highest priority - must reject)
    if os.getenv('CONDA_PREFIX'):
        detection_methods.append('CONDA_PREFIX env var')
        return InstallationEnvironment(
            type=InstallationType.CONDA,
            python_path=sys.executable,
            cli_path=cli_path,
            detection_methods=detection_methods,
            is_supported=False,
            error_message=(
                "conda environments are not supported. "
                "Please use pipx or venv for installation."
            )
        )

    # Check pipx
    pipx_venv = Path.home() / '.local' / 'pipx' / 'venvs' / 'gitwebhooks-server'
    if pipx_venv.exists():
        detection_methods.append('pipx venv directory')
        return InstallationEnvironment(
            type=InstallationType.PIPX,
            python_path=sys.executable,
            cli_path=cli_path,
            detection_methods=detection_methods,
        )

    # Check venv / virtualenv
    in_venv = (
        hasattr(sys, 'real_prefix') or
        (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    )

    if in_venv:
        if hasattr(sys, 'real_prefix'):
            detection_methods.append('sys.real_prefix (virtualenv)')
            venv_type = InstallationType.VIRTUALENV
        else:
            detection_methods.append('sys.base_prefix != sys.prefix (venv)')
            venv_type = InstallationType.VENV

        return InstallationEnvironment(
            type=venv_type,
            python_path=sys.executable,
            cli_path=cli_path,
            venv_root=sys.prefix,
            detection_methods=detection_methods,
        )

    # Default: system pip installation
    detection_methods.append('default (system pip)')
    return InstallationEnvironment(
        type=InstallationType.SYSTEM_PIP,
        python_path=detect_python_interpreter(),
        cli_path=cli_path,
        detection_methods=detection_methods,
    )


def check_systemd() -> bool:
    """Check if systemctl is available

    Returns:
        True if systemctl command exists, False otherwise
    """
    try:
        result = subprocess.run(
            ['which', 'systemctl'],
            capture_output=True,
            timeout=5
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def check_root_permission() -> bool:
    """Check if running with root privileges

    Returns:
        True if running as root, False otherwise
    """
    return os.geteuid() == 0


def generate_service_file(
    cli_path: str,
    config_path: str,
    python_path: Optional[str] = None,
    use_python_module: bool = False
) -> str:
    """Generate systemd service file content

    Args:
        cli_path: Path to gitwebhooks-cli executable
        config_path: Path to configuration file
        python_path: Python interpreter path (if using python -m mode)
        use_python_module: If True, use 'python -m gitwebhooks.cli' format

    Returns:
        Service file content as string
    """
    if use_python_module and python_path:
        exec_start = f"{python_path} -m gitwebhooks.cli -c {config_path}"
    else:
        exec_start = f"{cli_path} -c {config_path}"

    return SERVICE_TEMPLATE.format(
        exec_start=exec_start
    )


def get_service_path() -> Path:
    """Get the standard systemd service file path

    Returns:
        Path to service file location
    """
    return Path('/etc/systemd/system/git-webhooks-server.service')


def get_cli_path() -> str:
    """Get the absolute path to gitwebhooks-cli

    Returns:
        Absolute path to gitwebhooks-cli executable

    Note:
        This assumes the CLI is installed in /usr/local/bin
        or available in the system PATH.
    """
    # Try to find gitwebhooks-cli in PATH
    try:
        result = subprocess.run(
            ['which', 'gitwebhooks-cli'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    # Fallback to standard location
    return '/usr/local/bin/gitwebhooks-cli'
