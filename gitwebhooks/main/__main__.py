"""Main module entry point

Allows running the CLI with: python3 -m gitwebhooks.main
"""

import sys

# Import main from the same directory
from gitwebhooks.main import main

if __name__ == '__main__':
    sys.exit(main())
