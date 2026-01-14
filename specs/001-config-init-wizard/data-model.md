# Data Model: config init 交互式向导

**Feature**: 001-config-init-wizard
**Date**: 2025-01-14

## Overview

本文档定义 `config init` 交互式向导功能的数据模型。由于本功能是 CLI 向导，主要用于收集配置数据并生成 INI 文件，不涉及持久化数据存储。

## Core Entities

### 1. ConfigLevel（配置级别）

表示配置文件的作用域和存储位置。

| 属性 | 类型 | 描述 |
|------|------|------|
| `name` | str | 级别名称：`system`, `local`, `user` |
| `path` | str | 配置文件路径 |
| `requires_root` | bool | 是否需要 root 权限 |

**值映射**:
```python
CONFIG_LEVELS = {
    'system': {
        'path': '/etc/gitwebhooks.ini',
        'requires_root': True
    },
    'local': {
        'path': '/usr/local/etc/gitwebhooks.ini',
        'requires_root': True
    },
    'user': {
        'path': '~/.gitwebhooks.ini',
        'requires_root': False
    }
}
```

**验证规则**:
- name 必须是 `system`, `local`, `user` 之一
- user 级别的路径需要展开 `~` 为用户主目录

### 2. PlatformType（平台类型）

表示支持的 Git 平台。

| 属性 | 类型 | 描述 |
|------|------|------|
| `name` | str | 平台名称：`github`, `gitee`, `gitlab`, `custom` |
| `events` | List[str] | 支持的 webhook 事件类型 |
| `requires_secret` | bool | 是否需要配置密钥 |
| `custom_fields` | List[str] | custom 平台的额外字段 |

**平台定义**:
```python
PLATFORMS = {
    'github': {
        'events': ['push', 'release', 'pull_request', 'tag'],
        'requires_secret': True
    },
    'gitee': {
        'events': ['push', 'release', 'pull_request'],
        'requires_secret': True
    },
    'gitlab': {
        'events': ['push', 'release', 'tag'],
        'requires_secret': True
    },
    'custom': {
        'events': [],  # 自定义平台事件由用户指定
        'requires_secret': False,
        'custom_fields': ['header_name', 'header_value', 'identifier_path', 'header_event']
    }
}
```

### 3. ServerConfig（服务器配置）

服务器监听和日志配置。

| 属性 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| `address` | str | `0.0.0.0` | 监听地址 |
| `port` | int | `6789` | 监听端口 |
| `log_file` | str | *根据配置级别确定* | 日志文件路径 |

**验证规则**:
- address: 有效的 IP 地址或 `0.0.0.0`
- port: 1-65535 之间的整数
- log_file: 必须是有效的文件路径（目录需存在）

### 4. PlatformConfig（平台配置）

单个 Git 平台的 webhook 配置。

| 属性 | 类型 | 描述 |
|------|------|------|
| `platform` | str | 平台类型 |
| `handle_events` | List[str] | 要处理的事件列表 |
| `verify` | bool | 是否启用签名验证 |
| `secret` | str | 验证密钥（verify=True 时必需） |
| `custom_params` | dict | custom 平台的额外参数 |

**验证规则**:
- handle_events: 不能为空，至少包含一个事件
- secret: 当 verify=True 时不能为空

### 5. RepositoryConfig（仓库配置）

单个仓库的部署配置。

| 属性 | 类型 | 描述 |
|------|------|------|
| `name` | str | 仓库标识（owner/repo 格式） |
| `cwd` | str | 工作目录路径（必须已存在） |
| `cmd` | str | 部署命令 |

**验证规则**:
- name: 必须符合 `owner/repo` 格式（正则：`^[^/]+/[^/]+$`）
- cwd: 必须是已存在的目录路径
- cmd: 不能为空字符串

### 6. ConfigFile（配置文件）

完整的 INI 配置文件结构。

| 属性 | 类型 | 描述 |
|------|------|------|
| `server` | ServerConfig | 服务器配置 |
| `platforms` | List[PlatformConfig] | 平台配置列表 |
| `repositories` | List[RepositoryConfig] | 仓库配置列表 |

**INI 结构**:
```ini
[server]
address = 0.0.0.0
port = 6789
log_file = /var/log/git-webhooks-server.log

[github]
handle_events = push, release
verify = true
secret = my-webhook-secret

[repo/owner/name]
cwd = /path/to/repo
cmd = git pull && ./deploy.sh
```

## Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                        交互式向导流程                              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  选择配置级别    │ ──> ConfigLevel
                    └─────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │ 输入服务器配置   │ ──> ServerConfig
                    └─────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  选择平台类型    │ ──> PlatformType
                    └─────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │ 配置平台参数     │ ──> PlatformConfig
                    └─────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │ 配置仓库信息     │ ──> RepositoryConfig
                    └─────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  生成 INI 文件   │ ──> ConfigFile
                    └─────────────────┘
```

## Validation Summary

| 实体 | 验证点 |
|------|--------|
| ConfigLevel | name 在有效范围内，路径目录可写 |
| ServerConfig | port 范围，address 格式，log_file 路径有效 |
| PlatformConfig | handle_events 非空，secret 在 verify=True 时非空 |
| RepositoryConfig | name 格式正确，cwd 目录存在，cmd 非空 |
| ConfigFile | 所有嵌套配置均有效 |

## State Transitions

向导执行过程中的状态管理：

1. **INITIAL**: 初始状态，等待用户开始
2. **SELECTING_LEVEL**: 选择配置级别
3. **CONFIGURING_SERVER**: 配置服务器参数
4. **SELECTING_PLATFORM**: 选择平台类型
5. **CONFIGURING_PLATFORM**: 配置平台参数
6. **CONFIGURING_REPO**: 配置仓库信息
7. **CONFIRMING_WRITE**: 确认写入文件
8. **COMPLETE**: 完成，文件已生成

**错误恢复**: 任何状态下用户输入无效数据时，返回当前状态重新输入。

**中断恢复**: Ctrl+C 在任何状态下都触发清理和退出。
