"""Help command module

Provides help information display functionality for gitwebhooks-cli.
"""

import argparse
import sys


def cmd_help(args: argparse.Namespace) -> int:
    """Handle help subcommand.

    Displays main help or subcommand-specific help depending on the topic.

    Args:
        args: Parsed command-line arguments
            - topic: Optional subcommand name to show help for

    Returns:
        Exit code (0 = success)

    Examples:
        >>> args = argparse.Namespace(topic=None)
        >>> cmd_help(args)  # doctest: +SKIP
        0
        >>> args = argparse.Namespace(topic='serve')
        >>> cmd_help(args)  # doctest: +SKIP
        0
    """
    # Import here to avoid circular dependency
    from gitwebhooks.main import get_parser

    parser = get_parser()

    if hasattr(args, 'topic') and args.topic:
        # Show subcommand help
        show_subcommand_help(parser, args.topic)
    else:
        # Show main help
        show_main_help(parser)

    return 0


def show_main_help(parser: argparse.ArgumentParser) -> None:
    """Display main help information.

    Args:
        parser: The main argument parser

    Returns:
        None
    """
    # Custom help output
    help_text = """Git Webhooks Server - Automated deployment webhook handler

Usage:
  gitwebhooks-cli [-v] [-c CONFIG] <command> [<args>]

Commands:
  serve       Start webhook server or manage systemd service
  config      Manage configuration file
  help        Show help information

Options:
  -v, --version  Show version information
  -c, --config   Path to configuration file (default: auto-discover)

Examples:
  gitwebhooks-cli serve                    # Start server
  gitwebhooks-cli serve install            # Install systemd service
  gitwebhooks-cli config init              # Initialize configuration
  gitwebhooks-cli help serve               # Show serve command help

For more information on a specific command:
  gitwebhooks-cli help <command>
"""
    print(help_text)


def show_subcommand_help(parser: argparse.ArgumentParser, topic: str) -> None:
    """Display help for a specific subcommand.

    Args:
        parser: The main argument parser
        topic: Subcommand name

    Returns:
        None
    """
    # Map topic to help text
    help_texts = {
        'serve': """Command: serve
Start webhook server or manage systemd service

Usage:
  gitwebhooks-cli serve [-c CONFIG]
  gitwebhooks-cli serve install [--force] [--dry-run] [--verbose]
  gitwebhooks-cli serve uninstall [--purge]

Subcommands:
  (none)        Start the webhook server
  install       Install systemd service
  uninstall     Uninstall systemd service

Options:
  -c, --config   Path to configuration file

Install options:
  --force        Force overwrite existing service
  --dry-run      Preview mode, don't make changes
  --verbose      Increase verbosity

Uninstall options:
  --purge        Also remove configuration file

Examples:
  gitwebhooks-cli serve                         # Start server
  gitwebhooks-cli serve -c /etc/webhooks.ini    # Start with custom config
  gitwebhooks-cli serve install                 # Install service
  gitwebhooks-cli serve install --force         # Force overwrite
  gitwebhooks-cli serve uninstall               # Uninstall service
""",
        'config': """Command: config
Manage configuration file

Usage:
  gitwebhooks-cli config init [level]
  gitwebhooks-cli config view [-c CONFIG]

Subcommands:
  init          Initialize configuration file
  view          View configuration file

Init arguments:
  level         Configuration level (system, local, user)

View options:
  -c, --config  Path to configuration file

Examples:
  gitwebhooks-cli config init              # Interactive init
  gitwebhooks-cli config init user         # User-level config
  gitwebhooks-cli config init system       # System-level config (requires sudo)
  gitwebhooks-cli config view              # View current config
""",
    }

    if topic in help_texts:
        print(help_texts[topic])
    else:
        print(f"Error: Unknown command '{topic}'", file=sys.stderr)
        print("Available commands: serve, config", file=sys.stderr)
        print()
        print("Use 'gitwebhooks-cli help' to see main help", file=sys.stderr)
