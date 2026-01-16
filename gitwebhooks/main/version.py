"""Version display module

Provides version information display functionality for gitwebhooks-cli.
"""

import sys


def print_version() -> None:
    """Print version information and exit.

    Displays version in the format: gitwebhooks-cli x.x.x

    Returns:
        None

    Examples:
        >>> print_version()  # doctest: +SKIP
        gitwebhooks-cli 2.2.0
    """
    # Import __version__ from package
    from gitwebhooks import __version__

    print(f'gitwebhooks-cli {__version__}')
