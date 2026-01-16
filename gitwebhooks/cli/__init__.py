"""CLI subcommands module

Provides subcommand registration and implementation for gitwebhooks-cli.
"""

from gitwebhooks.cli.config import cmd_init, cmd_view
from gitwebhooks.cli.help import cmd_help
from gitwebhooks.cli.serve import cmd_serve


def register_subparsers(subparsers):
    """Register all CLI subparsers

    Args:
        subparsers: argparse subparsers object from ArgumentParser.add_subparsers()

    Returns:
        None
    """
    # Register help subcommand
    register_help_subparser(subparsers)

    # Register serve subcommand
    register_serve_subparser(subparsers)

    # Register config subcommand
    register_config_subparser(subparsers)


def register_serve_subparser(subparsers):
    """Register serve subcommand and its actions

    Args:
        subparsers: argparse subparsers object

    Returns:
        None
    """
    serve_parser = subparsers.add_parser(
        'serve',
        add_help=False,
        help='Start webhook server or manage systemd service'
    )
    serve_parser.add_argument(
        '-c', '--config',
        dest='config',
        help='Path to configuration file (default: auto-discover)'
    )
    serve_subparsers = serve_parser.add_subparsers(dest='serve_action')

    # install action
    install_parser = serve_subparsers.add_parser('install', add_help=False)
    install_parser.add_argument(
        '--force',
        action='store_true',
        help='Force overwrite existing service'
    )
    install_parser.add_argument(
        '--verbose',
        action='count',
        default=0,
        help='Increase verbosity'
    )
    install_parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview mode without making changes'
    )
    install_parser.add_argument(
        '--config-level',
        choices=['user', 'local', 'system'],
        help='Configuration file level (user/local/system)'
    )
    install_parser.set_defaults(func=cmd_serve)

    # uninstall action
    uninstall_parser = serve_subparsers.add_parser('uninstall', add_help=False)
    uninstall_parser.add_argument(
        '--purge',
        action='store_true',
        help='Also remove configuration file'
    )
    uninstall_parser.set_defaults(func=cmd_serve)

    # Set default function for serve (when no action specified)
    serve_parser.set_defaults(func=cmd_serve)


def register_help_subparser(subparsers):
    """Register help subcommand

    Args:
        subparsers: argparse subparsers object

    Returns:
        None
    """
    help_parser = subparsers.add_parser(
        'help',
        add_help=False
    )
    help_parser.add_argument(
        'topic',
        nargs='?',
        help='Subcommand to show help for (serve, config)'
    )
    help_parser.set_defaults(func=cmd_help)


def register_config_subparser(subparsers):
    """Register config subcommand and its actions

    Args:
        subparsers: argparse subparsers object

    Returns:
        None
    """
    config_parser = subparsers.add_parser(
        'config',
        add_help=False,
        help='Manage gitwebhooks configuration'
    )
    config_subparsers = config_parser.add_subparsers(dest='config_action')

    # init action
    init_parser = config_subparsers.add_parser(
        'init',
        add_help=False,
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
    view_parser = config_subparsers.add_parser('view', add_help=False)
    view_parser.add_argument(
        '-c',
        '--config',
        dest='config',
        help='Path to configuration file (default: auto-detect)'
    )
    view_parser.set_defaults(func=cmd_view)
