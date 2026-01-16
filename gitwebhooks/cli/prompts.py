"""Interactive prompt utilities

Provides functions for interactive user input and validation.
"""

import sys
from typing import Any, Callable, Optional, Dict, List, Tuple

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


def ask_question(prompt: str,
                 validator: Optional[Callable[[str], Any]] = None,
                 default: Optional[Any] = None,
                 required: bool = True) -> Any:
    """Ask a question with optional validation and default value

    Args:
        prompt: Question prompt to display
        validator: Optional validation function that raises ValueError on invalid input
        default: Optional default value if user provides empty input
        required: Whether a value is required (defaults to True)

    Returns:
        Validated user input or default value

    Raises:
        KeyboardInterrupt: If user confirms exit on Ctrl+C
    """
    while True:
        try:
            response = input(prompt).strip()

            # Use default if empty input provided
            if not response and default is not None:
                return default

            # Validate if validator provided
            if validator:
                if isinstance(validator, str):
                    # Validator is a string name, look up function
                    validator_func = globals().get(validator)
                    if validator_func:
                        return validator_func(response)
                else:
                    return validator(response)

            return response

        except KeyboardInterrupt:
            # Ask for confirmation before exiting
            if ask_yes_no('Confirm exit? Unsaved changes will be lost (y/N) ', default=False):
                print('Configuration cancelled')
                sys.exit(0)
        except ValueError as e:
            print(f'Invalid input: {e}')
            print('Please try again')


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


def validate_address(value: str) -> str:
    """Validate server address

    Args:
        value: String input to validate

    Returns:
        Validated address string

    Raises:
        ValueError: If address is empty
    """
    if not value:
        raise ValueError('Server address cannot be empty')
    return value


def validate_path(value: str) -> str:
    """Validate file path

    Args:
        value: String input to validate

    Returns:
        Validated path string

    Raises:
        ValueError: If path is empty
    """
    if not value:
        raise ValueError('Path cannot be empty')
    return value


def validate_bool(value: str) -> bool:
    """Validate boolean input

    Args:
        value: String input to validate

    Returns:
        True or False

    Raises:
        ValueError: If input is not a boolean value
    """
    value_lower = value.lower()
    if value_lower in ('y', 'yes', 'true', '1'):
        return True
    elif value_lower in ('n', 'no', 'false', '0'):
        return False
    else:
        raise ValueError('Please enter yes/no or y/n')


def validate_text(value: str) -> str:
    """Validate text input (non-empty)

    Args:
        value: String input to validate

    Returns:
        Validated text string

    Raises:
        ValueError: If text is empty
    """
    if not value:
        raise ValueError('Input cannot be empty')
    return value


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
