"""CLI subcommands module

Provides subcommand registration and implementation for gitwebhooks-cli.
"""

from gitwebhooks.cli.service import cmd_install, cmd_uninstall
from gitwebhooks.cli.config import cmd_init, cmd_view


def register_subparsers(subparsers):
    """Register all CLI subparsers

    Args:
        subparsers: argparse subparsers object from ArgumentParser.add_subparsers()

    Returns:
        None
    """
    # Register service subcommand
    register_service_subparser(subparsers)

    # Register config subcommand
    register_config_subparser(subparsers)


def register_service_subparser(subparsers):
    """Register service subcommand and its actions

    Args:
        subparsers: argparse subparsers object

    Returns:
        None
    """
    service_parser = subparsers.add_parser(
        'service',
        help='Manage systemd service installation'
    )
    service_subparsers = service_parser.add_subparsers(dest='service_action')

    # install action
    install_parser = service_subparsers.add_parser('install')
    install_parser.add_argument(
        '--force',
        action='store_true',
        help='Force overwrite existing service'
    )
    install_parser.add_argument(
        '-v', '--verbose',
        action='count',
        default=0,
        help='Increase verbosity (can be used: -v, -vv)'
    )
    install_parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview service file without installing'
    )
    install_parser.add_argument(
        '--config-level',
        choices=['user', 'local', 'system'],
        help='Configuration file level (user/local/system). If not specified, will be prompted.'
    )
    install_parser.set_defaults(func=cmd_install)

    # uninstall action
    uninstall_parser = service_subparsers.add_parser('uninstall')
    uninstall_parser.add_argument(
        '--purge',
        action='store_true',
        help='Also remove configuration file'
    )
    uninstall_parser.set_defaults(func=cmd_uninstall)


def register_config_subparser(subparsers):
    """Register config subcommand and its actions

    Args:
        subparsers: argparse subparsers object

    Returns:
        None
    """
    config_parser = subparsers.add_parser(
        'config',
        help='Manage gitwebhooks configuration'
    )
    config_subparsers = config_parser.add_subparsers(dest='config_action')

    # init action
    init_parser = config_subparsers.add_parser(
        'init',
        help='Initialize configuration file using interactive wizard'
    )
    init_parser.add_argument(
        'level',
        nargs='?',
        choices=['system', 'local', 'user'],
        help='Configuration level (system/local/user). If not specified, will be prompted.'
    )
    init_parser.set_defaults(func=cmd_init)

    # view action
    view_parser = config_subparsers.add_parser('view')
    view_parser.add_argument(
        '-c',
        '--config',
        dest='config',
        help='Path to configuration file (default: auto-detect)'
    )
    view_parser.set_defaults(func=cmd_view)
