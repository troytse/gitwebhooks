"""Python 模块入口点

支持使用 `python3 -m gitwebhooks.cli` 运行服务器。
"""

from gitwebhooks.cli import main
import sys

if __name__ == '__main__':
    sys.exit(main())
