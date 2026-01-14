"""systemd service utilities

Provides functions for generating and managing systemd service files.
"""

import os
import subprocess
import sys
from pathlib import Path


# Service file template
SERVICE_TEMPLATE = """[Unit]
Description=Git Webhooks Server
Documentation=https://github.com/troytse/git-webhooks-server
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart={cli_path} -c {config_path}
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


def generate_service_file(cli_path: str, config_path: str) -> str:
    """Generate systemd service file content

    Args:
        cli_path: Path to gitwebhooks-cli executable
        config_path: Path to configuration file

    Returns:
        Service file content as string
    """
    return SERVICE_TEMPLATE.format(
        cli_path=cli_path,
        config_path=config_path
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
