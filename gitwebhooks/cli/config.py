"""Configuration initialization CLI command

Provides interactive configuration file initialization.
"""

import argparse
import configparser
import os
import sys
from pathlib import Path
from typing import Dict, Any

from gitwebhooks.cli.prompts import (
    ask_question,
    ask_yes_no,
    QUESTIONS,
    PLATFORM_QUESTIONS
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
