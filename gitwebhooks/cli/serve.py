"""Serve command module

Provides server startup and systemd service management functionality.
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

from gitwebhooks.server import WebhookServer
from gitwebhooks.utils.exceptions import ConfigurationError
from gitwebhooks.utils.constants import CONFIG_SEARCH_PATHS

# Import service management functions
from gitwebhooks.cli.service import install_service, uninstall_service

# Import version display
from gitwebhooks import __version__


def cmd_serve(args: argparse.Namespace) -> int:
    """Handle serve subcommand.

    This function dispatches to the appropriate serve action:
    - No action: Start the webhook server
    - install: Install systemd service
    - uninstall: Uninstall systemd service

    Args:
        args: Parsed command-line arguments
            - serve_action: The serve sub-action (install, uninstall, or None)
            - config: Configuration file path (from global -c argument)
            - force: Force overwrite existing service (install action)
            - dry_run: Preview mode (install action)
            - verbose: Verbosity level (install action)
            - purge: Also remove config file (uninstall action)

    Returns:
        Exit code (0 = success, 1 = error)
    """
    # Get serve_action from args
    serve_action = getattr(args, 'serve_action', None)

    if serve_action == 'install':
        # Call install_service directly (no deprecation warning)
        return install_service(
            force=getattr(args, 'force', False),
            verbose=getattr(args, 'verbose', 0),
            dry_run=getattr(args, 'dry_run', False),
            config_level_override=getattr(args, 'config_level', None),
            config_path_override=getattr(args, 'config', None)
        )
    elif serve_action == 'uninstall':
        # Call uninstall_service directly (no deprecation warning)
        return uninstall_service(purge=getattr(args, 'purge', False))
    else:
        # Start server
        return start_server(args)


def start_server(args: argparse.Namespace) -> int:
    """Start the webhook server.

    Args:
        args: Parsed command-line arguments
            - config: Configuration file path (from global -c argument)

    Returns:
        Exit code (0 = success, 1 = error)
    """
    # Get config path from args
    config_file = getattr(args, 'config', None)

    # Print version
    print(f'gitwebhooks-cli {__version__}')

    # Auto-discover config file if not specified
    if config_file is None:
        config_file = find_config_file()
        if config_file is None:
            # No config found - format error with all search paths
            searched_paths = [Path(p).expanduser().resolve() for p in CONFIG_SEARCH_PATHS]
            error_msg = format_config_error(searched_paths)
            print(error_msg, file=sys.stderr)
            return 1

    # Expand user path
    config_path = Path(config_file).expanduser()

    # Check configuration file exists
    if not config_path.exists():
        print(f'Error: Configuration file not found: {config_path}', file=sys.stderr)
        return 1

    # Print configuration file being used
    print(f'Using configuration file: {config_path}')
    print('Starting server...')

    # Create and run server
    try:
        server = WebhookServer(config_path=str(config_path))
        server.run()
        return 0
    except ConfigurationError as e:
        print(f'Configuration error: {e}', file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print('\nServer stopped by user')
        return 0
    except Exception as e:
        print(f'Error: {e}', file=sys.stderr)
        return 1


def find_config_file() -> Optional[str]:
    """Find configuration file by priority order.

    Searches for configuration files in the following order:
    1. User level: ~/.gitwebhooks.ini
    2. Local level: /usr/local/etc/gitwebhooks.ini
    3. System level: /etc/gitwebhooks.ini

    Returns:
        Path string of the first existing configuration file, or None if not found.
    """
    for config_path in CONFIG_SEARCH_PATHS:
        expanded_path = Path(config_path).expanduser().resolve()
        if expanded_path.exists():
            return str(expanded_path)
    return None


def format_config_error(searched_paths: list) -> str:
    """Format user-friendly error message for missing configuration file.

    Args:
        searched_paths: List of paths that were searched.

    Returns:
        Formatted error message string.
    """
    lines = [
        'Error: Configuration file not found.',
        'Searched paths:'
    ]
    for i, path in enumerate(searched_paths, 1):
        lines.append(f'  {i}. {path}')
    lines.append('')
    lines.append('You can create a configuration file using:')
    lines.append('  gitwebhooks-cli config init')
    return '\n'.join(lines)
