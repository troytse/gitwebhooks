"""Configuration CLI commands

Provides configuration initialization and viewing commands.
"""

import argparse
import configparser
import os
import sys
from pathlib import Path
from typing import Optional

from gitwebhooks.cli.init_wizard import Wizard
from gitwebhooks.utils.constants import (
    CONFIG_SEARCH_PATHS,
    SENSITIVE_KEYWORDS,
    COLOR_SENSITIVE,
    COLOR_RESET
)


def cmd_init(args: argparse.Namespace) -> int:
    """Initialize configuration file using interactive wizard

    Args:
        args: Parsed command-line arguments
            - level: Configuration level (system/local/user), optional

    Returns:
        Exit code (0 = success, 1 = error)
    """
    try:
        # Create and run wizard
        level = getattr(args, 'level', None)
        wizard = Wizard(level=level)
        config_path = wizard.run()
        return 0

    except ValueError as e:
        print(f"错误: {e}", file=sys.stderr)
        return 1
    except PermissionError as e:
        print(f"错误: {e}", file=sys.stderr)
        return 2
    except FileExistsError:
        print("操作已取消", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\n操作已取消")
        return 0


def locate_config_file(args: argparse.Namespace) -> Optional[Path]:
    """Locate configuration file based on arguments or default priority

    Args:
        args: Parsed command-line arguments
            - config: User-specified configuration file path (optional)

    Returns:
        Path to configuration file, or None if not found
    """
    # If user specified a config file with -c, use it
    if hasattr(args, 'config') and args.config:
        config_path = Path(args.config).expanduser()
        if config_path.exists():
            return config_path
        return None

    # Otherwise, search in priority order
    for path_str in CONFIG_SEARCH_PATHS:
        config_path = Path(path_str).expanduser()
        if config_path.exists():
            return config_path

    return None


def cmd_view(args: argparse.Namespace) -> int:
    """View configuration file content

    Args:
        args: Parsed command-line arguments
            - config: User-specified configuration file path (optional)

    Returns:
        Exit code (0 = success, 1 = error)
    """
    # Locate configuration file
    config_path = locate_config_file(args)

    if config_path is None:
        # Handle file not found
        if hasattr(args, 'config') and args.config:
            print(f'Error: Configuration file not found: {args.config}', file=sys.stderr)
        else:
            print('Error: No configuration file found.', file=sys.stderr)
            print('\nSearched paths (in priority order):', file=sys.stderr)
            for i, path_str in enumerate(CONFIG_SEARCH_PATHS, 1):
                expanded = Path(path_str).expanduser()
                print(f'  {i}. {expanded}', file=sys.stderr)
            print('\nTo create a configuration file, run:', file=sys.stderr)
            print('  gitwebhooks-cli config init', file=sys.stderr)
        return 1

    # Read and parse configuration
    try:
        parser = configparser.ConfigParser()
        parser.read(config_path, encoding='utf-8')
    except configparser.Error as e:
        print(f'Error: Failed to parse configuration file: {config_path}', file=sys.stderr)
        print(f'\nParsing error: {e}', file=sys.stderr)
        print('\nPlease check the file format and fix any syntax errors.', file=sys.stderr)
        return 1
    except PermissionError:
        print(f'Error: Permission denied: {config_path}', file=sys.stderr)
        print('\nPlease check file permissions or run with appropriate privileges.', file=sys.stderr)
        return 1

    # Determine source type
    source = 'user-specified' if (hasattr(args, 'config') and args.config) else 'auto-detected'

    # Format and display output
    print(format_config_header(config_path, source))
    print()
    print(format_config_content(parser))

    return 0


def format_config_header(config_path: Path, source: str) -> str:
    """Format configuration file header

    Args:
        config_path: Path to configuration file
        source: Source type ('user-specified' or 'auto-detected')

    Returns:
        Formatted header string
    """
    # Handle symlinks
    display_path = str(config_path)
    if config_path.is_symlink():
        target = config_path.resolve()
        display_path = f'{config_path} -> {target}'

    return f'Config File: {display_path} (source: {source})'


def format_config_content(parser: configparser.ConfigParser) -> str:
    """Format configuration content by sections

    Args:
        parser: ConfigParser instance with loaded configuration

    Returns:
        Formatted configuration content
    """
    if not parser.sections():
        return '(Configuration file is empty or has no valid sections)'

    lines = []
    for section in parser.sections():
        lines.append(f'[{section}]')
        for key, value in parser.items(section):
            formatted_value = format_sensitive_field(key, value)
            lines.append(f'{key} = {formatted_value}')
        lines.append('')  # Empty line between sections

    return '\n'.join(lines)


def is_sensitive_key(key: str) -> bool:
    """Check if a configuration key is sensitive

    Args:
        key: Configuration key name

    Returns:
        True if key contains sensitive keyword, False otherwise
    """
    key_lower = key.lower()
    return any(keyword in key_lower for keyword in SENSITIVE_KEYWORDS)


def should_use_color() -> bool:
    """Check if color output should be used

    Returns:
        True if color should be used, False otherwise
    """
    # Check NO_COLOR environment variable
    if os.getenv('NO_COLOR'):
        return False

    # Check TERM environment variable
    term = os.getenv('TERM', '')
    if term == 'dumb':
        return False

    return True


def format_sensitive_field(key: str, value: str) -> str:
    """Format a configuration field with sensitive field highlighting

    Args:
        key: Configuration key name
        value: Configuration value

    Returns:
        Formatted value with color if sensitive
    """
    if is_sensitive_key(key) and should_use_color():
        return f'{COLOR_SENSITIVE}{value}{COLOR_RESET}'
    return value
