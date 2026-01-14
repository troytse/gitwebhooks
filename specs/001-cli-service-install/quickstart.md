# Quickstart Guide: CLI Service Installation

**Feature**: 001-cli-service-install
**Date**: 2026-01-14

## 开发环境设置

### 1. 激活虚拟环境

```bash
cd /Users/troy/develop/git-webhooks-server
source venv/bin/activate
```

### 2. 安装开发依赖

```bash
pip install -e ".[dev]"
```

### 3. 运行现有测试

```bash
python3 -m pytest tests/ -v
```

---

## 新增子命令使用示例

### service install 命令

```bash
# 基本安装（需要 sudo）
sudo gitwebhooks-cli service install

# 强制覆盖已存在的服务
sudo gitwebhooks-cli service install --force

# 查看帮助
gitwebhooks-cli service install --help
```

### service uninstall 命令

```bash
# 基本卸载
sudo gitwebhooks-cli service uninstall

# 卸载并删除配置文件
sudo gitwebhooks-cli service uninstall --purge
```

### config init 命令

```bash
# 使用默认路径初始化
gitwebhooks-cli config init

# 指定输出路径
gitwebhooks-cli config init --output /etc/webhooks.ini
```

---

## 测试指南

### 单元测试

```bash
# 运行所有测试
pytest tests/unit/ -v

# 运行特定模块测试
pytest tests/unit/test_cli.py -v
pytest tests/unit/test_service.py -v
pytest tests/unit/test_config.py -v
```

### 集成测试

```bash
# 运行集成测试（需要 root 权限）
sudo pytest tests/integration/test_service_install.py -v
sudo pytest tests/integration/test_config_init.py -v
```

### 测试覆盖范围

| 模块 | 测试文件 | 覆盖内容 |
|------|----------|----------|
| `gitwebhooks/cli/` | `test_cli.py` | 命令解析、帮助信息 |
| `gitwebhooks/cli/service.py` | `test_service.py` | 服务安装/卸载 |
| `gitwebhooks/cli/config.py` | `test_config.py` | 配置初始化 |
| `gitwebhooks/utils/systemd.py` | `test_systemd.py` | 服务文件生成 |

### Mock 使用

```python
# 示例：mock systemctl 命令
from unittest.mock import patch, MagicMock

@patch('subprocess.run')
def test_service_install(mock_run):
    mock_run.return_value = MagicMock(returncode=0)
    # 执行测试
    ...
```

---

## 开发工作流程

### 1. 实现新功能

```bash
# 创建新模块
mkdir -p gitwebhooks/cli
touch gitwebhooks/cli/__init__.py
touch gitwebhooks/cli/service.py
touch gitwebhooks/cli/config.py
touch gitwebhooks/cli/prompts.py
touch gitwebhooks/utils/systemd.py
```

### 2. 模块职责

| 文件 | 职责 | 导出 |
|------|------|------|
| `cli/__init__.py` | CLI 子命令入口 | `register_subparsers()` |
| `cli/service.py` | service 子命令实现 | `cmd_install()`, `cmd_uninstall()` |
| `cli/config.py` | config 子命令实现 | `cmd_init()` |
| `cli/prompts.py` | 交互式问答 | `ask_question()`, 问答模板 |
| `utils/systemd.py` | systemd 工具 | `generate_service_file()`, `check_systemd()` |

### 3. 代码规范

```python
# 文件头示例
"""Service installation CLI commands

Provides systemd service installation and removal functionality.
"""

import argparse
import sys
from typing import List

def cmd_install(args: argparse.Namespace) -> int:
    """Install systemd service

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 = success, 1 = error)
    """
    # 实现逻辑
    ...
```

### 4. 调试技巧

```bash
# 直接运行模块
python3 -m gitwebhooks.cli service --help

# 使用 pytest 断点
pytest tests/unit/test_service.py -vv --pdb

# 查看日志
export GITWEBHOOKS_DEBUG=1
gitwebhooks-cli service install
```

---

## 手动测试步骤

### 测试服务安装

```bash
# 1. 确保没有已安装的服务
sudo systemctl status git-webhooks-server 2>/dev/null || echo "服务未安装"

# 2. 运行安装命令
sudo gitwebhooks-cli service install

# 3. 验证服务文件
cat /etc/systemd/system/git-webhooks-server.service

# 4. 检查服务状态
sudo systemctl status git-webhooks-server

# 5. 查看日志
sudo journalctl -u git-webhooks-server -n 50
```

### 测试配置初始化

```bash
# 1. 备份现有配置（如果存在）
cp ~/.gitwebhook.ini ~/.gitwebhook.ini.bak 2>/dev/null || true

# 2. 运行配置初始化
gitwebhooks-cli config init

# 3. 查看生成的配置
cat ~/.gitwebhook.ini

# 4. 验证配置有效
gitwebhooks-cli --help

# 5. 测试服务器启动
gitwebhooks-cli
```

### 测试服务卸载

```bash
# 1. 停止服务
sudo systemctl stop git-webhooks-server

# 2. 运行卸载命令
sudo gitwebhooks-cli service uninstall

# 3. 验证服务文件已删除
ls /etc/systemd/system/git-webhooks-server.service 2>/dev/null || echo "服务文件已删除"
```

---

## 常见问题

### Q: 如何模拟 systemd 不可用？

```python
# 在测试中 mock
@patch('gitwebhooks.utils.systemd.check_systemd', return_value=False)
def test_without_systemd(mock_check):
    result = cmd_service_install(args)
    assert result == 1
```

### Q: 如何测试需要 root 的操作？

```bash
# 使用 fakeroot (如果可用)
fakeroot gitwebhooks-cli service install

# 或在测试中 mock
@patch('os.geteuid', return_value=0)
@patch('subprocess.run')
def test_install_as_root(mock_run, mock_euid):
    ...
```

### Q: 如何验证配置文件格式？

```python
import configparser

def test_config_file_format():
    config = configparser.ConfigParser()
    config.read('~/.gitwebhook.ini')
    assert config.has_section('server')
    assert config.get('server', 'port') == '6789'
```

---

## 发布检查清单

- [ ] 所有单元测试通过
- [ ] 集成测试通过
- [ ] 代码符合项目风格指南
- [ ] 帮助信息完整且正确
- [ ] 错误消息友好且有用
- [ ] 文档已更新（README.md, README.zh.md）
- [ ] install.sh 已移除
- [ ] 原有功能未受影响（向后兼容）

---

## 相关文档

- [Feature Spec](../spec.md) - 功能规格
- [Research](../research.md) - 技术研究
- [Data Model](../data-model.md) - 数据模型
- [Service Contract](contracts/service.md) - service 子命令契约
- [Config Contract](contracts/config.md) - config 子命令契约
