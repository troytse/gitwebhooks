# CLI Module Contract

**Module**: `gitwebhooks.cli`
**Version**: 1.0.0
**Status**: Design Phase

## Overview

CLI（命令行接口）模块负责解析命令行参数、初始化服务器并启动服务。提供与原 `git-webhooks-server.py` 兼容的接口。

---

## Main Entry Point Contract

**Function**: `main`
**Module**: `gitwebhooks.cli`
**Type**: Entry point function

```python
import sys
import getopt
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
```

---

## CLI Wrapper Script Contract

**File**: `gitwebhooks-cli` (installed to `/usr/local/bin/`)
**Type**: Executable shell script or Python wrapper

### Option 1: Shell Wrapper (Recommended)

```bash
#!/bin/bash
# gitwebhooks-cli - Git Webhooks Server CLI wrapper

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 运行 Python 模块
exec python3 -m gitwebhooks.cli "$@"
```

### Option 2: Python Wrapper

```python
#!/usr/bin/env python3
# gitwebhooks-cli - Git Webhooks Server CLI wrapper

import sys
import os

# 添加包路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gitwebhooks.cli import main

if __name__ == '__main__':
    sys.exit(main())
```

---

## Command Line Compatibility

### Backward Compatibility Matrix

| Old Command | New Command | Compatible? |
|-------------|-------------|-------------|
| `python3 git-webhooks-server.py -c config.ini` | `gitwebhooks-cli -c config.ini` | ✅ Yes |
| `python3 git-webhooks-server.py --config=config.ini` | `gitwebhooks-cli --config=config.ini` | ✅ Yes |
| `python3 git-webhooks-server.py -h` | `gitwebhooks-cli --help` | ✅ Yes |
| Default config path | `/usr/local/etc/git-webhooks-server.ini` | ✅ Same |

### Argument Parsing

使用标准库 `getopt` 模块（与原代码一致）：

```python
import getopt

# 短选项：h, c:
# 长选项：help, config=
opts, args = getopt.getopt(argv, 'hc:', ['help', 'config='])
```

---

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Error (config file not found, parse error, etc.) |
| 130 | SIGINT (KeyboardInterrupt) - default shell behavior |

---

## Error Messages

### Standard Error Format

```bash
$ gitwebhooks-cli -c nonexistent.ini
Error: Configuration file not found: nonexistent.ini
$ echo $?
1
```

### Configuration Error

```bash
$ gitwebhooks-cli -c invalid.ini
Configuration error: Failed to parse config: [Errno 2] No such file or directory: invalid.ini
$ echo $?
1
```

### Success (Server Running)

```bash
$ gitwebhooks-cli -c /etc/webhooks.ini
2025-01-13 10:30:00 Serving on 0.0.0.0 port 6789...
# Server runs until interrupted
^C
Server stopped by user
```

---

## Installation Integration

### Install Script Updates

**File**: `install.sh`

```bash
# 原有安装代码
# install -m 755 git-webhooks-server.py /usr/local/bin/git-webhooks-server.py

# 新的安装代码
cat > /usr/local/bin/gitwebhooks-cli << 'EOF'
#!/bin/bash
exec python3 -m gitwebhooks.cli "$@"
EOF
chmod +x /usr/local/bin/gitwebhooks-cli
```

### Systemd Service Integration

**File**: `git-webhooks-server.service`

```ini
[Unit]
Description=Git Webhooks Server
After=network.target

[Service]
Type=simple
User=webhooks
Group=webhooks
ExecStart=/usr/local/bin/gitwebhooks-cli -c /usr/local/etc/git-webhooks-server.ini
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

---

## Environment Variables

当前实现不使用环境变量，所有配置通过 INI 文件。

**Future Enhancement**: 考虑支持环境变量覆盖：

```bash
export GITWEBHOOKS_CONFIG=/etc/webhooks.ini
export GITWEBHOOKS_PORT=8080
```

---

## Module Exports

**File**: `gitwebhooks/__init__.py`

```python
# CLI 不是库的一部分，不导出
# 但可以通过模块调用：
# python3 -m gitwebhooks.cli
```

---

## Testing Strategy

### Unit Tests

```python
import unittest
from unittest.mock import patch, MagicMock
from gitwebhooks.cli import main

class TestCLI(unittest.TestCase):
    """CLI 模块测试"""

    @patch('gitwebhooks.cli.WebhookServer')
    def test_config_argument(self, mock_server):
        """测试 -c 参数"""
        mock_instance = MagicMock()
        mock_server.return_value = mock_instance

        result = main(['-c', '/path/to/config.ini'])

        mock_server.assert_called_once_with(config_path='/path/to/config.ini')
        mock_instance.run.assert_called_once()
        self.assertEqual(result, 0)

    @patch('gitwebhooks.cli.WebhookServer')
    def test_help_argument(self, mock_server):
        """测试 -h 参数"""
        result = main(['-h'])

        self.assertEqual(result, 0)
        mock_server.assert_not_called()

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_print_help(self, mock_stdout):
        """测试帮助输出"""
        from gitwebhooks.cli import print_help

        print_help()
        output = mock_stdout.getvalue()

        self.assertIn('Git Webhooks Server', output)
        self.assertIn('--config', output)
```

### Integration Tests

```bash
#!/bin/bash
# test_cli.sh

# 测试 1: 帮助信息
gitwebhooks-cli --help | grep -q "Usage:"
assert $? -eq 0

# 测试 2: 缺少配置文件
gitwebhooks-cli -c /nonexistent.ini 2>&1 | grep -q "not found"
assert $? -eq 0

# 测试 3: 成功启动（后台运行）
gitwebhooks-cli -c test-config.ini &
PID=$!
sleep 2
kill -0 $PID  # 检查进程运行
assert $? -eq 0
kill $PID
```

---

## Documentation

### Man Page (Optional)

**File**: `gitwebhooks-cli.1`

```groff
.TH GITWEBHOOKS-CLI 1 "2025-01-13" "Git Webhooks Server" "User Commands"
.SH NAME
gitwebhooks-cli \- Git webhook deployment server
.SH SYNOPSIS
.B gitwebhooks-cli
[\-c config_file]
.SH DESCRIPTION
Git Webhooks Server receives webhook events from Git platforms
and triggers deployment commands.
.SH OPTIONS
.TP
.B \-h, \-\-help
Display help information.
.TP
.B \-c, \-\-config=FILE
Use specified configuration file.
.SH FILES
.TP
.I /usr/local/etc/git-webhooks-server.ini
Default configuration file.
.SH SEE ALSO
gitwebhooks-server.ini(5)
```

---

## Migration Guide

### For Users

**Old Way**:
```bash
python3 git-webhooks-server.py -c /etc/webhooks.ini
```

**New Way**:
```bash
gitwebhooks-cli -c /etc/webhooks.ini
# or
python3 -m gitwebhooks.cli -c /etc/webhooks.ini
```

### For Developers

**Testing**:
```python
# Old: 直接导入主文件
import git-webhooks-server  # 无效

# New: 导入模块
from gitwebhooks.cli import main
from gitwebhooks.server import WebhookServer
```
