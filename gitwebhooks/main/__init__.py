"""CLI main function

Command-line interface module providing compatibility with the original git-webhooks-server.py.
"""

import argparse
import sys
from pathlib import Path
from typing import List

from gitwebhooks.server import WebhookServer
from gitwebhooks.utils.exceptions import ConfigurationError

# Try to import subcommands, may not be available in older versions
try:
    from gitwebhooks.cli import register_subparsers
    HAS_SUBCOMMANDS = True
except ImportError:
    HAS_SUBCOMMANDS = False


def main(argv: List[str] = None) -> int:
    """Main entry point

    Args:
        argv: Command-line argument list (defaults to sys.argv[1:])

    Returns:
        Exit code (0 = success, 1 = error)

    Raises:
        SystemExit: Exit on error

    Command Line Arguments:
        -h, --help      Show help message and exit
        -c, --config    Specify configuration file path
        service         Service management subcommands
        config          Configuration management subcommands

    Default Config Path:
        ~/.gitwebhook.ini

    Examples:
        python3 -m gitwebhooks.main -c /path/to/config.ini
        gitwebhooks-cli --config /etc/webhooks.ini
        gitwebhooks-cli service install
        gitwebhooks-cli config init
    """
    if argv is None:
        argv = sys.argv[1:]

    # Default configuration file path (changed to user home directory)
    default_config = '~/.gitwebhook.ini'

    # Create main argument parser
    parser = argparse.ArgumentParser(
        prog='gitwebhooks-cli',
        description='Git Webhooks Server - Automated deployment webhook handler',
        add_help=True
    )
    parser.add_argument(
        '-c', '--config',
        default=default_config,
        help='Path to INI configuration file (default: ~/.gitwebhook.ini)'
    )

    # Add subcommands if available
    if HAS_SUBCOMMANDS:
        subparsers = parser.add_subparsers(dest='command', help='Subcommands')
        register_subparsers(subparsers)

    # Parse arguments
    args = parser.parse_args(argv)

    # If no subcommand, run server (backward compatible behavior)
    if not hasattr(args, 'func'):
        return run_server(args.config)

    # Execute subcommand
    return args.func(args)


def run_server(config_file: str) -> int:
    """Run the webhook server

    Args:
        config_file: Path to configuration file

    Returns:
        Exit code (0 = success, 1 = error)
    """
    # Expand user path
    config_path = Path(config_file).expanduser()

    # Check configuration file exists
    if not config_path.exists():
        print(f'Error: Configuration file not found: {config_path}', file=sys.stderr)
        return 1

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


if __name__ == '__main__':
    sys.exit(main())
