# Research: CLI Service Installation

**Feature**: 001-cli-service-install
**Date**: 2026-01-14
**Status**: Complete

## Overview

本文档记录了将 `install.sh` 脚本功能迁移到 CLI 子命令所需的技术研究和设计决策。

---

## 1. CLI 子命令最佳实践

### Decision: 使用 `argparse` 子命令解析器

**Rationale**:
- Python 标准库，符合"无外部依赖"原则
- 原生支持子命令结构（`add_subparsers()`）
- 自动生成帮助信息
- 兼容 Python 3.6+

**Alternatives Considered**:
1. `click` - 功能强大但需要外部依赖
2. `typer` - 现代化但需要 Python 3.7+ 和外部依赖
3. 手动解析 - 复杂且易出错

**Implementation Pattern**:
```python
parser = argparse.ArgumentParser()
subparsers = parser.add_subparsers(dest='command')

# service subcommand
service_parser = subparsers.add_parser('service')
service_subparsers = service_parser.add_subparsers(dest='service_action')
service_subparsers.add_parser('install')
service_subparsers.add_parser('uninstall')

# config subcommand
config_parser = subparsers.add_parser('config')
config_subparsers = config_parser.add_subparsers(dest='config_action')
config_subparsers.add_parser('init')
```

**Help Information Format**:
- 保持与现有 `print_help()` 风格一致
- 三级帮助：主命令、子命令、操作
  - `gitwebhooks-cli --help` (主命令)
  - `gitwebhooks-cli service --help` (service 子命令)
  - `gitwebhooks-cli service install --help` (install 操作)

---

## 2. systemd 服务文件规范

### Decision: 使用标准 systemd 单元文件格式

**Rationale**:
- systemd 是 Linux 服务管理标准
- 符合宪法原则 V（Service Integration）
- 与现有 `install.sh` 生成的服务文件兼容

**Standard Configuration**:
```ini
[Unit]
Description=Git WebHooks Server
After=network-online.target

[Service]
Type=simple
User=                    # 留空，使用当前用户
ExecStart=/usr/local/bin/gitwebhooks-cli -c ~/.gitwebhook.ini
Restart=on-failure
RestartSec=1min

[Install]
WantedBy=multi-user.target
```

**Key Changes from install.sh**:
1. **默认配置路径**: 从 `/usr/local/etc/git-webhooks-server.ini` 改为 `~/.gitwebhook.ini`
2. **ExecStart**: 直接调用 `gitwebhooks-cli`（不再需要硬链接到源码目录）
3. **WorkingDirectory**: 不再需要（pip 安装的包可以直接导入）

**Service File Location**:
- 标准: `/etc/systemd/system/` (优先)
- 或: `/usr/lib/systemd/system/`
- 服务名: `git-webhooks-server.service`

---

## 3. 交互式 CLI 模式

### Decision: 使用标准库 `input()` + 自定义验证

**Rationale**:
- Python 标准库，无外部依赖
- 完全控制输入验证流程
- 支持 Ctrl+C 处理

**Input Validation Pattern**:
```python
def ask_question(prompt: str, validator=None, default=None):
    """交互式提问，带验证和默认值"""
    while True:
        try:
            response = input(prompt).strip()
            if not response and default is not None:
                return default
            if validator:
                result = validator(response)
                return result
            return response
        except KeyboardInterrupt:
            # 询问是否退出
            if ask_yes_no("确认退出？未保存的修改将丢失 (y/N)", default=False):
                sys.exit(0)
        except ValueError as e:
            print(f"输入无效: {e}")
            print("请重新输入")
```

**Ctrl+C Handling**:
- 使用 `try/except KeyboardInterrupt` 捕获中断
- 询问用户确认退出（避免误操作）
- 未保存的修改不写入文件

**Question Types**:
1. **文本输入**: 服务器地址、路径等
2. **端口号验证**: 1-65535 范围检查
3. **是/否确认**: `[Y/n]` 或 `[y/N]` 格式
4. **密码输入**: 使用 `getpass` 模块（可选）

---

## 4. 配置文件默认值

### Decision: 基于 `git-webhooks-server.ini.sample` 确定默认值

**研究现有配置文件**:

| Section | Key | 默认值 | 说明 |
|---------|-----|--------|------|
| `[server]` | `address` | `0.0.0.0` | 监听所有接口 |
| `[server]` | `port` | `6789` | 默认端口 |
| `[server]` | `log_file` | `~/.gitwebhook.log` | 日志文件（改为用户目录） |
| `[ssl]` | `enable` | `false` | 默认禁用 SSL |
| `[github]` | `verify` | `true` | 默认验证签名 |
| `[gitee]` | `verify` | `true` | 默认验证签名 |
| `[gitlab]` | `verify` | `true` | 默认验证签名 |

**问答流程设计**:

1. **基本配置**（必须）:
   - 服务器监听地址 (默认: 0.0.0.0)
   - 服务器端口 (默认: 6789)
   - 日志文件路径 (默认: ~/.gitwebhook.log)

2. **SSL 配置**（可选）:
   - 是否启用 SSL (默认: false)
   - 如果启用：密钥文件路径、证书文件路径

3. **Webhook 平台配置**（逐个）:
   - 是否配置 GitHub webhook? (y/N)
   - 如果是：secret（可选）
   - 重复 Gitee、GitLab、Custom

**Question Prompts 示例**:
```
=== Git Webhooks Server 配置初始化 ===

服务器监听地址 [默认: 0.0.0.0]:
服务器端口 [默认: 6789]:
日志文件路径 [默认: ~/.gitwebhook.log]:

是否启用 SSL? (y/N) [默认: N]:

配置 GitHub webhook:
  启用签名验证? (Y/n) [默认: Y]:
  Webhook secret (留空跳过):

配置 Gitee webhook:
  ...
```

---

## 5. 权限检测

### Decision: 使用 `os.geteuid()` 和 `subprocess` 检测 sudo

**Rationale**:
- 跨平台兼容（Linux/Unix）
- 清晰提示用户需要 sudo
- 不自动调用 sudo（让用户明确操作）

**Implementation**:
```python
import os
import subprocess

def check_root_required() -> bool:
    """检测是否需要 root 权限"""
    return os.geteuid() != 0

def run_with_sudo(cmd: list):
    """使用 sudo 执行命令"""
    subprocess.run(['sudo'] + cmd, check=True)
```

**Error Message**:
```
错误: 此操作需要 root 权限
请使用: sudo gitwebhooks-cli service install
```

---

## 6. 配置文件权限

### Decision: 新建配置文件权限设为 0600

**Rationale**:
- 符合宪法安全要求（Security Requirements）
- 配置文件包含敏感信息（webhook secrets）
- 仅用户本人可读写

**Implementation**:
```python
import os

def set_secure_permissions(filepath: str):
    """设置文件权限为仅用户可读写"""
    os.chmod(filepath, 0o600)
```

---

## 7. 向后兼容性

### Decision: 保持原有 `-c/--config` 选项兼容

**Rationale**:
- 不破坏现有用户的使用方式
- 支持从 pip 安装后直接运行
- 默认配置路径改为 `~/.gitwebhook.ini`

**CLI 参数结构**:
```bash
# 原有方式（继续支持）
gitwebhooks-cli -c /path/to/config.ini
gitwebhooks-cli --config=/path/to/config.ini

# 新增子命令
gitwebhooks-cli service install
gitwebhooks-cli service uninstall
gitwebhooks-cli config init

# 不带参数运行（使用默认配置路径）
gitwebhooks-cli  # 等同于 gitwebhooks-cli -c ~/.gitwebhook.ini
```

---

## 8. 服务文件模板

### Decision: 内嵌服务文件模板到 Python 代码

**Rationale**:
- 不依赖外部文件
- pip 安装后立即可用
- 简化部署

**Implementation**:
```python
SERVICE_TEMPLATE = """[Unit]
Description=Git WebHooks Server
After=network-online.target

[Service]
Type=simple
ExecStart={cli_path} -c {config_path}
Restart=on-failure
RestartSec=1min

[Install]
WantedBy=multi-user.target
"""

def generate_service_file(cli_path: str, config_path: str) -> str:
    """生成服务文件内容"""
    return SERVICE_TEMPLATE.format(
        cli_path=cli_path,
        config_path=config_path
    )
```

**CLI Path Detection**:
```python
import sys
from pathlib import Path

def get_cli_path() -> str:
    """获取 gitwebhooks-cli 的绝对路径"""
    return str(Path(sys.executable).parent / 'gitwebhooks-cli')
```

---

## Summary

| 研究领域 | 决策 | 依赖 |
|----------|------|------|
| CLI 子命令 | argparse (标准库) | 无 |
| systemd 服务 | 标准单元文件格式 | systemctl |
| 交互式输入 | input() + 自定义验证 | 无 |
| 配置默认值 | 基于 sample 文件 | 无 |
| 权限检测 | os.geteuid() | 无 |
| 文件权限 | os.chmod(0o600) | 无 |
| 服务模板 | 内嵌 Python 字符串 | 无 |

所有技术选型均使用 Python 标准库，符合项目"无外部依赖"原则。
