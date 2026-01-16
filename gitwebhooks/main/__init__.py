"""CLI main function

Command-line interface module providing compatibility with the original gitwebhooks.py.
"""

import argparse
import sys
from pathlib import Path
from typing import List, Optional

from gitwebhooks.server import WebhookServer
from gitwebhooks.utils.exceptions import ConfigurationError
from gitwebhooks.utils.constants import CONFIG_SEARCH_PATHS

# Try to import subcommands, may not be available in older versions
try:
    from gitwebhooks.cli import register_subparsers
    HAS_SUBCOMMANDS = True
except ImportError:
    HAS_SUBCOMMANDS = False

# Global parser reference for help command
_parser = None


def get_parser() -> argparse.ArgumentParser:
    """Get the main argument parser instance.

    Returns:
        The main ArgumentParser instance

    Examples:
        >>> parser = get_parser()
        >>> isinstance(parser, argparse.ArgumentParser)
        True
    """
    global _parser
    if _parser is None:
        _parser = create_parser()
    return _parser


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the main argument parser.

    Returns:
        Configured ArgumentParser instance

    Examples:
        >>> parser = create_parser()
        >>> isinstance(parser, argparse.ArgumentParser)
        True
    """
    # Create main argument parser (help disabled)
    parser = argparse.ArgumentParser(
        prog='gitwebhooks-cli',
        description='Git Webhooks Server - Automated deployment webhook handler',
        add_help=False
    )
    parser.add_argument(
        '-c', '--config',
        default=None,
        help='Path to INI configuration file (default: auto-discover)'
    )

    # Add subcommands if available
    if HAS_SUBCOMMANDS:
        subparsers = parser.add_subparsers(dest='command', help='Subcommands')
        register_subparsers(subparsers)

    return parser


def find_config_file() -> Optional[str]:
    """Find configuration file by priority order.

    Searches for configuration files in the following order:
    1. User level: ~/.gitwebhooks.ini
    2. Local level: /usr/local/etc/gitwebhooks.ini
    3. System level: /etc/gitwebhooks.ini

    Returns:
        Path string of the first existing configuration file, or None if not found.

    Examples:
        >>> find_config_file()  # doctest: +SKIP
        '/home/user/.gitwebhooks.ini'
        >>> find_config_file()  # doctest: +SKIP
        None
    """
    for config_path in CONFIG_SEARCH_PATHS:
        expanded_path = Path(config_path).expanduser().resolve()
        if expanded_path.exists():
            return str(expanded_path)
    return None


def format_config_error(searched_paths: List[Path]) -> str:
    """Format user-friendly error message for missing configuration file.

    Args:
        searched_paths: List of paths that were searched.

    Returns:
        Formatted error message string.

    Examples:
        >>> paths = [Path('/home/user/.gitwebhooks.ini')]
        >>> format_config_error(paths)  # doctest: +SKIP
        'Error: Configuration file not found.\\nSearched paths:\\n  1. /home/user/.gitwebhooks.ini\\n\\nYou can create a configuration file using:\\n  gitwebhooks-cli config init'
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


def main(argv: List[str] = None) -> int:
    """Main entry point

    Args:
        argv: Command-line argument list (defaults to sys.argv[1:])

    Returns:
        Exit code (0 = success, 1 = error)

    Raises:
        SystemExit: Exit on error

    Command Line Arguments:
        -v, --version   Show version information and exit
        -c, --config     Specify configuration file path (optional)
        serve            Start webhook server or manage systemd service
        config           Configuration management subcommands
        help             Show help information

    Config Discovery:
        When -c is not specified, searches in order:
        1. ~/.gitwebhooks.ini (user level)
        2. /usr/local/etc/gitwebhooks.ini (local level)
        3. /etc/gitwebhooks.ini (system level)

    Examples:
        python3 -m gitwebhooks.main -v
        python3 -m gitwebhooks.main serve
        python3 -m gitwebhooks.main serve -c /path/to/config.ini
        gitwebhooks-cli serve install
        gitwebhooks-cli config init
        gitwebhooks-cli help
    """
    if argv is None:
        argv = sys.argv[1:]

    # Pre-check for -v/--version parameters (takes priority over everything)
    if '-v' in argv or '--version' in argv:
        from gitwebhooks.main.version import print_version
        print_version()
        return 0

    # Check for -h/--help parameters and show error
    if '-h' in argv or '--help' in argv:
        print('Error: -h/--help parameters are not supported.', file=sys.stderr)
        print('Use \'gitwebhooks-cli help\' or \'gitwebhooks-cli help <subcommand>\' instead.', file=sys.stderr)
        return 1

    # Create parser and parse arguments
    parser = create_parser()

    # Check if user provided a command (first argument without leading dash)
    command = None
    for i, arg in enumerate(argv):
        if not arg.startswith('-'):
            command = arg
            break

    # Try to parse arguments
    try:
        args = parser.parse_args(argv)
    except SystemExit as e:
        # argparse will call sys.exit on error, catch it to provide better error
        if e.code != 0:
            # Parsing failed, check if it's an unknown command
            if command and command not in ['serve', 'config', 'help', 'service']:
                print(f"Error: Unknown command '{command}'", file=sys.stderr)
                print("Available commands: serve, config, help", file=sys.stderr)
                print()
                print("Use 'gitwebhooks-cli help' to see usage information", file=sys.stderr)
            return 1
        raise

    # If no subcommand specified, show help (new default behavior)
    if not hasattr(args, 'func') or args.func is None:
        from gitwebhooks.cli.help import show_main_help
        show_main_help(parser)
        return 0

    # Execute subcommand
    return args.func(args)


def run_server(config_file: Optional[str]) -> int:
    """Run the webhook server

    Args:
        config_file: Path to configuration file, or None to auto-discover

    Returns:
        Exit code (0 = success, 1 = error)
    """
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
