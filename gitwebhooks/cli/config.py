"""Configuration CLI commands

Provides configuration initialization and viewing commands.
"""

import argparse
import configparser
import os
import sys
from pathlib import Path
from typing import Dict, Optional

from gitwebhooks.cli.prompts import (
    ask_question,
    ask_yes_no,
    QUESTIONS,
    PLATFORM_QUESTIONS
)
from gitwebhooks.utils.constants import (
    CONFIG_SEARCH_PATHS,
    SENSITIVE_KEYWORDS,
    COLOR_SENSITIVE,
    COLOR_RESET
)


def cmd_init(args: argparse.Namespace) -> int:
    """Initialize configuration file

    Args:
        args: Parsed command-line arguments
            - output: Output configuration file path

    Returns:
        Exit code (0 = success, 1 = error)
    """
    # Expand output path
    output_path = Path(args.output).expanduser()

    # Check if file exists
    if output_path.exists():
        if not handle_existing_config(output_path):
            print('Configuration cancelled')
            return 0

    # Collect configuration
    try:
        config = run_interactive_questions()
    except KeyboardInterrupt:
        print('\nConfiguration cancelled')
        return 0

    # Write configuration file
    if not write_config_file(output_path, config):
        return 1

    # Set file permissions
    set_config_permissions(output_path)

    print(f'\nConfiguration file created: {output_path}')
    print('Permissions set: 0600 (user read/write only)')
    print()
    print('Next steps:')
    print('  1. Edit configuration file, add repository settings')
    print('  2. Run service: gitwebhooks-cli')
    print('  3. Or install as service: sudo gitwebhooks-cli service install')

    return 0


def run_interactive_questions() -> Dict[str, Dict[str, str]]:
    """Execute interactive question flow

    Returns:
        Configuration dictionary with sections and keys
    """
    print('=== Git Webhooks Server Configuration Initialization ===')
    print()

    config = {}

    # Collect server configuration
    config.update(collect_server_config())
    print()

    # Collect SSL configuration
    config.update(collect_ssl_config())
    print()

    # Collect webhook platform configurations
    config.update(collect_webhook_config())
    print()

    return config


def collect_server_config() -> Dict[str, Dict[str, str]]:
    """Collect server configuration

    Returns:
        Server configuration dictionary
    """
    server_config = {}

    for question in QUESTIONS:
        value = ask_question(
            question['prompt'],
            validator=question.get('validator'),
            default=question['default'],
            required=question.get('required', True)
        )

        # Map to server section
        if 'server' not in server_config:
            server_config['server'] = {}

        key = question['key'].replace('server_', '')
        server_config['server'][key] = str(value)

    return server_config


def collect_ssl_config() -> Dict[str, Dict[str, str]]:
    """Collect SSL configuration

    Returns:
        SSL configuration dictionary
    """
    ssl_config = {}

    # Ask if SSL should be enabled
    enable_ssl = ask_yes_no('Enable SSL? (y/N) [default: N]: ', default=False)

    ssl_config['ssl'] = {'enable': 'true' if enable_ssl else 'false'}

    if enable_ssl:
        # Ask for key file
        key_file = ask_question(
            'SSL key file path: ',
            validator=None,
            required=True
        )
        ssl_config['ssl']['key_file'] = key_file

        # Ask for certificate file
        cert_file = ask_question(
            'SSL certificate file path: ',
            validator=None,
            required=True
        )
        ssl_config['ssl']['cert_file'] = cert_file

    return ssl_config


def collect_webhook_config() -> Dict[str, Dict[str, str]]:
    """Collect webhook platform configuration

    Returns:
        Webhook configuration dictionary
    """
    webhook_config = {}

    # Configure GitHub
    if ask_yes_no('Configure GitHub webhook? (Y/n) [default: Y]: ', default=True):
        webhook_config.update(collect_platform_config('github'))
        print()

    # Configure Gitee
    if ask_yes_no('Configure Gitee webhook? (Y/n) [default: Y]: ', default=True):
        webhook_config.update(collect_platform_config('gitee'))
        print()

    # Configure GitLab
    if ask_yes_no('Configure GitLab webhook? (Y/n) [default: Y]: ', default=True):
        webhook_config.update(collect_platform_config('gitlab'))
        print()

    return webhook_config


def collect_platform_config(platform: str) -> Dict[str, Dict[str, str]]:
    """Collect configuration for a specific platform

    Args:
        platform: Platform name (github, gitee, gitlab)

    Returns:
        Platform configuration dictionary
    """
    platform_config = {}
    questions = PLATFORM_QUESTIONS.get(platform, [])

    print(f'Configure {platform.capitalize()} webhook:')

    for question in questions:
        value = ask_question(
            question['prompt'],
            validator=question.get('validator'),
            default=question['default'],
            required=question.get('required', False)
        )

        section = question['section']
        key = question['key']

        if section not in platform_config:
            platform_config[section] = {}

        platform_config[section][key] = str(value)

    return platform_config


def write_config_file(filepath: Path, config: Dict[str, Dict[str, str]]) -> bool:
    """Write configuration to INI file

    Args:
        filepath: Path to output file
        config: Configuration dictionary

    Returns:
        True if successful, False otherwise
    """
    try:
        # Create parent directories if needed
        filepath.parent.mkdir(parents=True, exist_ok=True)

        # Create ConfigParser
        parser = configparser.ConfigParser()

        # Add sections and keys
        for section, keys in config.items():
            parser[section] = keys

        # Write to file
        with filepath.open('w') as f:
            parser.write(f)

        return True

    except (IOError, OSError) as e:
        print(f'Error: Cannot write configuration file: {e}', file=sys.stderr)
        return False


def set_config_permissions(filepath: Path) -> None:
    """Set configuration file permissions to 0600

    Args:
        filepath: Path to configuration file

    Returns:
        None
    """
    try:
        os.chmod(filepath, 0o600)
    except OSError as e:
        print(f'Warning: Cannot set file permissions: {e}', file=sys.stderr)


def handle_existing_config(filepath: Path) -> bool:
    """Handle existing configuration file

    Args:
        filepath: Path to existing configuration file

    Returns:
        True if user wants to overwrite, False otherwise
    """
    print(f'Configuration file already exists: {filepath}')
    return ask_yes_no('Overwrite? (y/N) ', default=False)


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
