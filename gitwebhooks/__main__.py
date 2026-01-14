"""Python module entry point

Supports running the server using `python3 -m gitwebhooks`.
"""

from gitwebhooks.main import main
import sys

if __name__ == '__main__':
    sys.exit(main())
