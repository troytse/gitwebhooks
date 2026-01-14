# Data Model: CLI Service Installation

**Feature**: 001-cli-service-install
**Date**: 2026-01-14
**Status**: Complete

## Overview

本文档描述 CLI 服务安装功能涉及的数据结构和实体。

---

## 1. CLI 命令结构

### 命令层次结构

```
gitwebhooks-cli
├── (无子命令)          # 启动服务器 (兼容原有行为)
│   └── -c, --config   # 指定配置文件路径
│   └── -h, --help     # 显示帮助
│
├── service             # 服务管理子命令
│   ├── install        # 安装 systemd 服务
│   ├── uninstall      # 卸载 systemd 服务
│   └── --help         # 显示 service 子命令帮助
│
├── config              # 配置管理子命令
│   ├── init           # 初始化配置文件
│   └── --help         # 显示 config 子命令帮助
│
└── --help              # 显示主命令帮助
```

### 命令参数定义

| 命令 | 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|------|--------|------|
| `gitwebhooks-cli` | `-c, --config` | string | N | `~/.gitwebhook.ini` | 配置文件路径 |
| `service install` | `--force` | flag | N | false | 强制覆盖已存在的服务 |
| `service uninstall` | `--purge` | flag | N | false | 同时删除配置文件 |
| `config init` | `--output` | string | N | `~/.gitwebhook.ini` | 输出文件路径 |

---

## 2. 配置文件结构

### INI 格式规范

```ini
[server]
address = <监听地址>        # 默认: 0.0.0.0
port = <端口号>             # 默认: 6789
log_file = <日志路径>       # 默认: ~/.gitwebhook.log

[ssl]
enable = <true/false>      # 默认: false
key_file = <密钥路径>       # 可选
cert_file = <证书路径>      # 可选

[github]
verify = <true/false>      # 默认: true
secret = <webhook secret>   # 可选

[gitee]
verify = <true/false>      # 默认: true
secret = <webhook secret>   # 可选

[gitlab]
verify = <true/false>      # 默认: true
secret = <webhook token>    # 可选

[custom]
header_name = <header名>    # 必填
header_value = <header值>   # 必填
header_token = <token header> # 可选
identifier_path = <JSON路径> # 必填
verify = <true/false>      # 默认: false
secret = <secret>          # 可选

[<owner>/<repo>]           # 仓库配置
cwd = <工作目录>            # 必填
cmd = <执行命令>            # 必填
```

### 配置文件验证规则

| Section | Key | 验证规则 | 错误提示 |
|---------|-----|----------|----------|
| `[server]` | `address` | 有效 IP 或 hostname | "无效的服务器地址" |
| `[server]` | `port` | 1-65535 整数 | "端口号必须在 1-65535 之间" |
| `[server]` | `log_file` | 可写路径 | "日志文件路径不可写" |
| `[ssl]` | `enable` | true/false | "enable 必须是 true 或 false" |
| `[ssl]` | `key_file` | 文件存在（当 enable=true） | "密钥文件不存在" |
| `[ssl]` | `cert_file` | 文件存在（当 enable=true） | "证书文件不存在" |

---

## 3. systemd 服务文件结构

### 服务单元模板

```ini
[Unit]
Description = Git Webhooks Server
Documentation = https://github.com/troytse/git-webhooks-server
After = network-online.target
Wants = network-online.target

[Service]
Type = simple
ExecStart = /usr/local/bin/gitwebhooks-cli -c ~/.gitwebhook.ini
Restart = on-failure
RestartSec = 1min
StandardOutput = journal
StandardError = journal

# 安全设置
NoNewPrivileges = true
PrivateTmp = true

[Install]
WantedBy = multi-user.target
```

### 服务文件元数据

| 属性 | 值 | 说明 |
|------|-----|------|
| 文件名 | `git-webhooks-server.service` | 服务单元文件名 |
| 安装位置 | `/etc/systemd/system/` | 系统级服务目录 |
| 服务名 | `git-webhooks-server` | systemctl 管理名称 |
| 用户 | 当前用户（不指定 User） | 服务运行用户 |

---

## 4. 问答流程数据结构

### 问答状态机

```
START → 服务器地址 → 端口 → 日志路径 → SSL配置 → GitHub → Gitee → GitLab → Custom → 完成
        ↓           ↓         ↓          ↓           ↓        ↓        ↓        ↓
      [验证]     [验证]    [验证]     [可选]       [可选]   [可选]   [可选]   [可选]
        ↓           ↓         ↓          ↓           ↓        ↓        ↓        ↓
    [重新输入] [重新输入] [重新输入] [跳过/输入]  [跳过/输入] ...
```

### 问答问题定义

```python
QUESTIONS = [
    {
        'key': 'server_address',
        'prompt': '服务器监听地址',
        'default': '0.0.0.0',
        'validator': validate_address,
        'required': True
    },
    {
        'key': 'server_port',
        'prompt': '服务器端口',
        'default': '6789',
        'validator': validate_port,
        'required': True
    },
    {
        'key': 'log_file',
        'prompt': '日志文件路径',
        'default': '~/.gitwebhook.log',
        'validator': validate_path,
        'required': False
    },
    # ... 更多问题
]
```

### 用户输入类型

| 类型 | 验证器 | 示例 |
|------|--------|------|
| 文本 | `validate_text()` | 任意字符串 |
| 端口 | `validate_port()` | 6789 |
| 路径 | `validate_path()` | `/var/log/webhook.log` |
| 布尔 | `validate_bool()` | y/Y/n/N |
| 是/否 | `validate_yes_no()` | `[Y/n]` 或 `[y/N]` |

---

## 5. 服务状态枚举

### 安装状态

```python
enum ServiceStatus:
    NOT_INSTALLED    # 服务未安装
    INSTALLED        # 服务已安装
    RUNNING          # 服务正在运行
    STOPPED          # 服务已停止
    ERROR            # 服务状态错误
```

### 操作结果

```python
enum OperationResult:
    SUCCESS          # 操作成功
    PERMISSION_DENIED # 权限不足
    ALREADY_EXISTS   # 已存在
    NOT_FOUND        # 未找到
    VALIDATION_ERROR # 验证失败
    SYSTEM_ERROR     # 系统错误
```

---

## 6. 配置初始化数据流

### 输入收集

```
用户输入
    ↓
验证器 (validator)
    ↓
类型转换 (str → 实际类型)
    ↓
默认值填充 (如果为空)
    ↓
配置字典 {key: value}
    ↓
INI 生成
    ↓
写入文件
```

### 配置字典示例

```python
config = {
    'server': {
        'address': '0.0.0.0',
        'port': '6789',
        'log_file': '~/.gitwebhook.log'
    },
    'ssl': {
        'enable': 'false'
    },
    'github': {
        'verify': 'true',
        'secret': ''
    },
    # ... 更多 sections
}
```

---

## 7. 错误处理数据

### 错误代码

| 代码 | 描述 | 用户友好消息 |
|------|------|--------------|
| `E_PERM` | 权限不足 | "需要 root 权限，请使用 sudo" |
| `E_EXISTS` | 已存在 | "服务已存在，使用 --force 强制覆盖" |
| `E_NOT_FOUND` | 未找到 | "服务未安装" |
| `E_INVALID` | 输入无效 | "无效的端口号，请输入 1-65535" |
| `E_WRITE` | 写入失败 | "无法写入配置文件" |
| `E_SYSTEMD` | systemd 不可用 | "此系统不支持 systemd" |

---

## 8. 路径解析规则

### 路径展开

| 模式 | 展开规则 | 示例 |
|------|----------|------|
| `~` | 用户主目录 | `~/.gitwebhook.ini` → `/home/user/.gitwebhook.ini` |
| `$HOME` | 环境变量 | `$HOME/config.ini` → `/home/user/config.ini` |
| 相对路径 | 当前工作目录 | `./config.ini` → `/current/dir/config.ini` |
| 绝对路径 | 保持不变 | `/etc/config.ini` |

### 实现

```python
from pathlib import Path

def expand_path(path: str) -> str:
    """展开路径中的 ~ 和环境变量"""
    return str(Path(path).expanduser())
```

---

## Summary

| 数据结构 | 用途 | 存储 |
|----------|------|------|
| CLI 命令树 | 命令解析 | argparse |
| 配置字典 | 运行时配置 | 内存 |
| INI 文件 | 持久化配置 | ~/.gitwebhook.ini |
| 服务单元 | systemd 配置 | /etc/systemd/system/ |
| 问答状态 | 配置初始化 | 内存 |

所有数据结构均使用 Python 标准库实现，无外部依赖。
