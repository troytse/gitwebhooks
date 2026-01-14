"""CLI subcommands module

Provides subcommand registration and implementation for gitwebhooks-cli.
"""

from gitwebhooks.cli.service import cmd_install, cmd_uninstall
from gitwebhooks.cli.config import cmd_init


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
    init_parser = config_subparsers.add_parser('init')
    init_parser.add_argument(
        '--output',
        default='~/.gitwebhook.ini',
        help='Output configuration file path (default: ~/.gitwebhook.ini)'
    )
    init_parser.set_defaults(func=cmd_init)
