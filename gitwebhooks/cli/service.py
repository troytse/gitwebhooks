"""Service installation CLI commands

Provides systemd service installation and removal functionality.
"""

import argparse
import subprocess
import sys
from pathlib import Path

from gitwebhooks.utils.systemd import (
    check_systemd,
    check_root_permission,
    generate_service_file,
    get_service_path,
    get_cli_path
)
from gitwebhooks.cli.prompts import ask_yes_no


# Error codes
E_PERM = 1
E_SYSTEMD = 1
E_EXISTS = 1


def cmd_install(args: argparse.Namespace) -> int:
    """Install systemd service

    Args:
        args: Parsed command-line arguments
            - force: Force overwrite existing service

    Returns:
        Exit code (0 = success, 1 = error)
    """
    # Check root permission
    if not check_root_permission():
        print('Error: This operation requires root privileges', file=sys.stderr)
        print('Please use: sudo gitwebhooks-cli service install', file=sys.stderr)
        return E_PERM

    # Check systemd availability
    if not check_systemd():
        print('Error: systemd is not supported on this system', file=sys.stderr)
        return E_SYSTEMD

    # Check if service already exists
    service_path = get_service_path()
    if service_path.exists():
        if not args.force:
            print(f'Error: Service already installed', file=sys.stderr)
            print(f'Service file: {service_path}', file=sys.stderr)
            print('Use --force to force overwrite', file=sys.stderr)
            return E_EXISTS

        # Confirm overwrite
        if not confirm_overwrite():
            print('Installation cancelled')
            return 0

    # Perform installation
    return install_service(args.force)


def install_service(force: bool = False) -> int:
    """Execute service installation logic

    Args:
        force: Force overwrite existing service

    Returns:
        Exit code (0 = success, 1 = error)
    """
    print('Installing systemd service...')

    # Get paths
    service_path = get_service_path()
    cli_path = get_cli_path()
    config_path = '~/.gitwebhook.ini'

    # Generate service file
    service_content = generate_service_file(cli_path, config_path)

    # Write service file
    try:
        service_path.write_text(service_content)
        print(f'Service file: {service_path}')
    except (IOError, OSError) as e:
        print(f'Error: Cannot write service file: {e}', file=sys.stderr)
        return 1

    # Reload systemd daemon
    print('Reloading systemd daemon...')
    try:
        subprocess.run(
            ['systemctl', 'daemon-reload'],
            check=True,
            capture_output=True
        )
    except subprocess.CalledProcessError as e:
        print(f'Warning: systemctl daemon-reload failed: {e}', file=sys.stderr)
        # Continue anyway

    # Enable and start service
    return enable_and_start_service()


def check_service_exists() -> bool:
    """Check if service is already installed

    Returns:
        True if service file exists, False otherwise
    """
    return get_service_path().exists()


def confirm_overwrite() -> bool:
    """Ask user to confirm overwrite

    Returns:
        True if user confirms, False otherwise
    """
    return ask_yes_no('Service already exists, overwrite? (y/N) ', default=False)


def enable_and_start_service() -> int:
    """Enable and start the service

    Returns:
        Exit code (0 = success, 1 = error)
    """
    # Ask if user wants to enable and start
    if not ask_yes_no('Enable and start service? (Y/n) ', default=True):
        print('Service installed but not started')
        print('Start manually: sudo systemctl start git-webhooks-server')
        return 0

    # Enable service
    print('Enabling service...')
    try:
        subprocess.run(
            ['systemctl', 'enable', 'git-webhooks-server'],
            check=True,
            capture_output=True
        )
    except subprocess.CalledProcessError as e:
        print(f'Warning: systemctl enable failed: {e}', file=sys.stderr)
        # Continue anyway

    # Start service
    print('Starting service...')
    try:
        subprocess.run(
            ['systemctl', 'start', 'git-webhooks-server'],
            check=True,
            capture_output=True
        )
    except subprocess.CalledProcessError as e:
        print(f'Warning: systemctl start failed: {e}', file=sys.stderr)
        # Continue anyway

    print()
    print('Installation complete!')
    print('Service status: systemctl status git-webhooks-server')

    return 0


def cmd_uninstall(args: argparse.Namespace) -> int:
    """Uninstall systemd service

    Args:
        args: Parsed command-line arguments
            - purge: Also remove configuration file

    Returns:
        Exit code (0 = success, 1 = error)
    """
    # Check root permission
    if not check_root_permission():
        print('Error: This operation requires root privileges', file=sys.stderr)
        print('Please use: sudo gitwebhooks-cli service uninstall', file=sys.stderr)
        return E_PERM

    # Check if service is installed
    if not check_service_exists():
        print('Error: Service not installed', file=sys.stderr)
        return 1

    # Perform uninstallation
    return uninstall_service(args.purge)


def uninstall_service(purge: bool = False) -> int:
    """Execute service uninstallation logic

    Args:
        purge: Also remove configuration file

    Returns:
        Exit code (0 = success, 1 = error)
    """
    print('Uninstalling systemd service...')

    # Stop and disable service
    stop_and_disable_service()

    # Remove service file
    remove_service_file()

    # Handle configuration cleanup
    handle_config_cleanup(purge)

    print()
    print('Uninstallation complete!')

    return 0


def stop_and_disable_service() -> None:
    """Stop and disable the service

    Returns:
        None
    """
    service_path = get_service_path()

    # Stop service if running
    print('Stopping service...')
    try:
        subprocess.run(
            ['systemctl', 'stop', 'git-webhooks-server'],
            check=False,
            capture_output=True
        )
    except Exception as e:
        print(f'Warning: systemctl stop failed: {e}', file=sys.stderr)
        # Continue anyway

    # Disable service
    print('Disabling service...')
    try:
        subprocess.run(
            ['systemctl', 'disable', 'git-webhooks-server'],
            check=False,
            capture_output=True
        )
    except Exception as e:
        print(f'Warning: systemctl disable failed: {e}', file=sys.stderr)
        # Continue anyway


def remove_service_file() -> None:
    """Remove the service file

    Returns:
        None
    """
    service_path = get_service_path()

    print('Removing service file...')
    try:
        service_path.unlink()
    except OSError as e:
        print(f'Warning: Failed to remove service file: {e}', file=sys.stderr)
        # Continue anyway

    # Reload systemd daemon
    print('Reloading systemd daemon...')
    try:
        subprocess.run(
            ['systemctl', 'daemon-reload'],
            check=False,
            capture_output=True
        )
    except Exception as e:
        print(f'Warning: systemctl daemon-reload failed: {e}', file=sys.stderr)
        # Continue anyway


def handle_config_cleanup(purge: bool) -> None:
    """Handle configuration file cleanup

    Args:
        purge: If True, remove configuration file

    Returns:
        None
    """
    config_path = Path('~/.gitwebhook.ini').expanduser()

    if not purge:
        return

    if config_path.exists():
        print(f'Removing configuration file: {config_path}')
        try:
            config_path.unlink()
        except OSError as e:
            print(f'Warning: Failed to remove configuration file: {e}', file=sys.stderr)
            # Continue anyway
