"""Interactive prompt utilities

Provides functions for interactive user input and validation.
"""

import sys

from gitwebhooks.utils.constants import ConfigLevel


# Question template for configuration initialization
QUESTIONS = [
    # Server configuration
    {
        'key': 'server_address',
        'prompt': 'Server listen address [default: 0.0.0.0]: ',
        'default': '0.0.0.0',
        'validator': None,
        'required': True
    },
    {
        'key': 'server_port',
        'prompt': 'Server port [default: 6789]: ',
        'default': '6789',
        'validator': 'validate_port',
        'required': True
    },
    {
        'key': 'log_file',
        'prompt': 'Log file path [default: ~/.gitwebhook.log]: ',
        'default': '~/.gitwebhook.log',
        'validator': None,
        'required': False
    },
]


# Platform-specific questions
PLATFORM_QUESTIONS = {
    'github': [
        {
            'section': 'github',
            'key': 'verify',
            'prompt': '  Enable signature verification? (Y/n) [default: Y]: ',
            'default': 'true',
            'validator': None,
            'required': False
        },
        {
            'section': 'github',
            'key': 'secret',
            'prompt': '  Webhook secret (leave empty to skip): ',
            'default': '',
            'validator': None,
            'required': False
        },
    ],
    'gitee': [
        {
            'section': 'gitee',
            'key': 'verify',
            'prompt': '  Enable signature verification? (Y/n) [default: Y]: ',
            'default': 'true',
            'validator': None,
            'required': False
        },
        {
            'section': 'gitee',
            'key': 'secret',
            'prompt': '  Webhook secret (leave empty to skip): ',
            'default': '',
            'validator': None,
            'required': False
        },
    ],
    'gitlab': [
        {
            'section': 'gitlab',
            'key': 'verify',
            'prompt': '  Enable token verification? (Y/n) [default: Y]: ',
            'default': 'true',
            'validator': None,
            'required': False
        },
        {
            'section': 'gitlab',
            'key': 'secret',
            'prompt': '  Webhook token (leave empty to skip): ',
            'default': '',
            'validator': None,
            'required': False
        },
    ],
}


def ask_yes_no(prompt: str, default: bool = False) -> bool:
    """Ask a yes/no question

    Args:
        prompt: Question prompt
        default: Default answer if user just presses Enter

    Returns:
        True for yes, False for no
    """
    # Set default indicator
    default_indicator = 'Y' if default else 'N'
    if not default:
        prompt = prompt.replace('(y/N)', f'[{default_indicator}]')
    else:
        prompt = prompt.replace('(Y/n)', f'[{default_indicator}]')

    while True:
        try:
            response = input(prompt).strip().lower()

            # Use default if empty input
            if not response:
                return default

            # Parse response
            if response in ('y', 'yes'):
                return True
            elif response in ('n', 'no'):
                return False
            else:
                print('Please enter y or n')

        except KeyboardInterrupt:
            if ask_yes_no('Confirm exit? Unsaved changes will be lost (y/N) ', default=False):
                print('Configuration cancelled')
                sys.exit(0)


def validate_port(value: str) -> int:
    """Validate port number

    Args:
        value: String input to validate

    Returns:
        Integer port number

    Raises:
        ValueError: If port is invalid
    """
    try:
        port = int(value)
        if not 1 <= port <= 65535:
            raise ValueError('Port must be between 1 and 65535')
        return port
    except ValueError as e:
        if 'must be between' in str(e):
            raise
        raise ValueError('Port must be a number')


def ask_config_level() -> ConfigLevel:
    """Ask user to select configuration file level

    Displays an interactive menu for selecting configuration file level
    with descriptions of each option.

    Returns:
        Selected ConfigLevel enum value

    Raises:
        KeyboardInterrupt: If user confirms exit on Ctrl+C
    """
    print('Select configuration file level for the service:')
    print('  1. User level (~/.gitwebhooks.ini) - Single user, highest priority')
    print('  2. Local level (/usr/local/etc/gitwebhooks.ini) - Local system, medium priority')
    print('  3. System level (/etc/gitwebhooks.ini) - Global system, lowest priority')
    print()

    choice_map = {
        '1': ConfigLevel.USER,
        '2': ConfigLevel.LOCAL,
        '3': ConfigLevel.SYSTEM,
    }

    while True:
        try:
            response = input('Enter choice [1-3] (default: 1): ').strip()

            # Use default if empty input
            if not response:
                return ConfigLevel.USER

            # Validate and map response
            if response in choice_map:
                return choice_map[response]

            # Invalid input
            print('Invalid choice. Please enter a number between 1 and 3.')

        except KeyboardInterrupt:
            if ask_yes_no('Confirm exit? (y/N) ', default=False):
                print('\nService installation cancelled')
                sys.exit(0)
