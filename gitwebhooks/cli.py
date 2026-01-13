"""CLI main function

Command-line interface module providing compatibility with the original git-webhooks-server.py.
"""

import getopt
import sys
from pathlib import Path
from typing import List

from gitwebhooks.server import WebhookServer
from gitwebhooks.utils.exceptions import ConfigurationError


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

    Default Config Path:
        /usr/local/etc/git-webhooks-server.ini

    Examples:
        python3 -m gitwebhooks.cli -c /path/to/config.ini
        gitwebhooks-cli --config /etc/webhooks.ini
    """
    if argv is None:
        argv = sys.argv[1:]

    # Default configuration file path
    default_config = '/usr/local/etc/git-webhooks-server.ini'
    config_file = default_config

    # Parse command-line arguments
    try:
        opts, _ = getopt.getopt(argv, 'hc:', ['config=', 'help'])
    except getopt.GetoptError:
        print_help()
        return 1

    for opt, value in opts:
        if opt in ('-h', '--help'):
            print_help()
            return 0
        elif opt in ('-c', '--config'):
            config_file = value

    # Check configuration file exists
    if not Path(config_file).exists():
        print(f'Error: Configuration file not found: {config_file}', file=sys.stderr)
        return 1

    # Create and run server
    try:
        server = WebhookServer(config_path=config_file)
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


def print_help() -> None:
    """Print help information

    Display command-line usage instructions
    """
    print('Git Webhooks Server - Automated deployment webhook handler')
    print()
    print('Usage:')
    print('  gitwebhooks-cli -c <configuration_file>')
    print('  gitwebhooks-cli --config=<configuration_file>')
    print('  gitwebhooks-cli --help')
    print()
    print('Options:')
    print('  -h, --help      Show this help message and exit')
    print('  -c, --config    Path to INI configuration file')
    print()
    print('Default configuration path:')
    print('  /usr/local/etc/git-webhooks-server.ini')
    print()
    print('Examples:')
    print('  gitwebhooks-cli -c /etc/webhooks.ini')
    print('  gitwebhooks-cli --config=./my-config.ini')
    print()
    print('Report bugs to: https://github.com/yourusername/git-webhooks-server/issues')


if __name__ == '__main__':
    sys.exit(main())
