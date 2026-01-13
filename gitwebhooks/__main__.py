"""Python module entry point

Supports running the server using `python3 -m gitwebhooks.cli`.
"""

from gitwebhooks.cli import main
import sys

if __name__ == '__main__':
    sys.exit(main())
