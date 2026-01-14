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
    detect_installation_type,
    InstallationType,
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
            - verbose: Verbosity level (0=normal, 1=verbose, 2=extra verbose)
            - dry_run: Preview mode without actual installation

    Returns:
        Exit code (0 = success, 1 = error)
    """
    # Get verbose and dry_run from args
    verbose = getattr(args, 'verbose', 0)
    dry_run = getattr(args, 'dry_run', False)

    # For dry-run mode, skip root check
    if not dry_run:
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
    else:
        # In dry-run mode, warn if service exists but continue
        service_path = get_service_path()
        if service_path.exists() and not args.force:
            print(f'Notice: Service already exists at {service_path}', file=sys.stderr)
            print('Previewing service file content (use --force to suppress this notice)...', file=sys.stderr)
            print()

    # Perform installation
    return install_service(force=args.force, verbose=verbose, dry_run=dry_run)


def install_service(force: bool = False, verbose: int = 0, dry_run: bool = False) -> int:
    """Execute service installation logic

    Args:
        force: Force overwrite existing service
        verbose: Verbosity level (0=normal, 1=verbose, 2=extra verbose)
        dry_run: Preview mode without actual installation

    Returns:
        Exit code (0 = success, 1 = error)
    """
    # Detect installation environment
    env = detect_installation_type()

    # Verbose output
    if verbose >= 1:
        print('Detecting Python environment...')
        print(f'  Installation type: {env.type.value}')
        print(f'  Python interpreter: {env.python_path}')
        print(f'  CLI path: {env.cli_path}')
        if verbose >= 2 and env.detection_methods:
            print(f'  Detection methods: {", ".join(env.detection_methods)}')
        if env.venv_root:
            print(f'  Virtual environment root: {env.venv_root}')
        print()

    # Check if environment is supported
    if not env.is_supported:
        print(f'Error: {env.error_message}', file=sys.stderr)
        print()
        print('For migration from conda:', file=sys.stderr)
        print('  1. Deactivate your conda environment: conda deactivate', file=sys.stderr)
        print('  2. Install using pipx: pipx install git-webhooks-server', file=sys.stderr)
        print('     OR create a venv: python3 -m venv ~/venv/gitwebhooks', file=sys.stderr)
        return 1

    # Warnings for non-recommended installation types
    if env.type == InstallationType.VIRTUALENV:
        print('Warning: virtualenv detected. venv is recommended.', file=sys.stderr)
        print()
    elif env.type == InstallationType.SYSTEM_PIP:
        print('Warning: System pip installation is not recommended.', file=sys.stderr)
        print('Consider using pipx or venv for better isolation.', file=sys.stderr)
        print()

    # Get paths
    service_path = get_service_path()
    config_path = '~/.gitwebhook.ini'

    # Generate service file based on installation type
    # For pipx: use cli_path directly
    # For others: use python -m gitwebhooks.cli
    use_python_module = env.type != InstallationType.PIPX

    service_content = generate_service_file(
        cli_path=env.cli_path,
        config_path=config_path,
        python_path=env.python_path if use_python_module else None,
        use_python_module=use_python_module
    )

    # Dry-run mode
    if dry_run:
        print('Dry-run mode: Preview of service file:')
        print('---')
        print(service_content)
        print('---')
        print()
        print(f'Service file would be written to: {service_path}')
        print('Dry-run complete: No changes made.')
        return 0

    # Actual installation
    print('Installing systemd service...')

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
    except OSError as e:
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
    except OSError as e:
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
    except OSError as e:
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
