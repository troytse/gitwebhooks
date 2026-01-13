"""CLI 主函数

命令行接口模块，提供与原 git-webhooks-server.py 兼容的接口。
"""

import getopt
import sys
from pathlib import Path
from typing import List

from gitwebhooks.server import WebhookServer
from gitwebhooks.utils.exceptions import ConfigurationError


def main(argv: List[str] = None) -> int:
    """主入口点

    Args:
        argv: 命令行参数列表（默认使用 sys.argv[1:]）

    Returns:
        退出码（0 = 成功，1 = 错误）

    Raises:
        SystemExit: 在错误时退出

    Command Line Arguments:
        -h, --help      显示帮助信息并退出
        -c, --config    指定配置文件路径

    Default Config Path:
        /usr/local/etc/git-webhooks-server.ini

    Examples:
        python3 -m gitwebhooks.cli -c /path/to/config.ini
        gitwebhooks-cli --config /etc/webhooks.ini
    """
    if argv is None:
        argv = sys.argv[1:]

    # 默认配置文件路径
    default_config = '/usr/local/etc/git-webhooks-server.ini'
    config_file = default_config

    # 解析命令行参数
    try:
        opts, _ = getopt.getopt(argv, 'hc:', ['config=', 'help'])
    except getopt.GetoptError:
        print_help()
        return 1

    for opt, value in opts:
        if opt in ('-h', '--help'):
            print_help()
            return 0
        elif opt in ('-c', '--config'):
            config_file = value

    # 检查配置文件存在
    if not Path(config_file).exists():
        print(f'Error: Configuration file not found: {config_file}', file=sys.stderr)
        return 1

    # 创建并运行服务器
    try:
        server = WebhookServer(config_path=config_file)
        server.run()
        return 0
    except ConfigurationError as e:
        print(f'Configuration error: {e}', file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print('\nServer stopped by user')
        return 0
    except Exception as e:
        print(f'Error: {e}', file=sys.stderr)
        return 1


def print_help() -> None:
    """打印帮助信息

    显示命令行使用说明
    """
    print('Git Webhooks Server - Automated deployment webhook handler')
    print()
    print('Usage:')
    print('  gitwebhooks-cli -c <configuration_file>')
    print('  gitwebhooks-cli --config=<configuration_file>')
    print('  gitwebhooks-cli --help')
    print()
    print('Options:')
    print('  -h, --help      Show this help message and exit')
    print('  -c, --config    Path to INI configuration file')
    print()
    print('Default configuration path:')
    print('  /usr/local/etc/git-webhooks-server.ini')
    print()
    print('Examples:')
    print('  gitwebhooks-cli -c /etc/webhooks.ini')
    print('  gitwebhooks-cli --config=./my-config.ini')
    print()
    print('Report bugs to: https://github.com/yourusername/git-webhooks-server/issues')


if __name__ == '__main__':
    sys.exit(main())
