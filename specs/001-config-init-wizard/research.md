# Research: config init 交互式向导

**Feature**: 001-config-init-wizard
**Date**: 2025-01-14
**Status**: Complete

## Overview

本文档记录 `config init` 交互式向导功能的技术研究和决策。

## Research Topics

### 1. Python 标准库交互式输入方案

**问题**: 如何在 Python 标准库中实现用户友好的交互式输入？

**研究选项**:
1. `input()` - 基础输入函数，需要手动实现提示和验证
2. `argparse` - 参数解析，不适合交互式场景
3. `cmd` 模块 - 命令行框架，过于重量级
4. 自建轻量级向导类 - 使用 `input()` 封装

**决策**: **自建轻量级向导类**，使用 `input()` 封装

**理由**:
- `argparse` 不适合交互式多步骤向导
- `cmd` 模块过于复杂，违背简单性原则
- 自建类可以完全控制用户体验，保持代码简洁
- 符合 constitution 原则 I：简单性

**实现要点**:
- 创建 `Wizard` 类管理向导流程
- 支持带默认值的输入（空输入使用默认值）
- 支持输入验证和重试
- 支持复选框式选择（多个选项）
- 支持 Ctrl+C 优雅退出

### 2. INI 配置文件生成方案

**问题**: 如何确保生成的 INI 文件格式正确且兼容现有配置加载器？

**研究选项**:
1. 使用字符串拼接直接写入
2. 使用 `configparser.ConfigParser` 生成
3. 使用模板引擎

**决策**: **使用 `configparser.ConfigParser` 生成**

**理由**:
- `configparser` 是 Python 标准库，零外部依赖
- 自动处理转义和格式化
- 与现有 `ConfigLoader` 兼容
- 可以验证生成的配置格式

**实现要点**:
```python
import configparser

config = configparser.ConfigParser()
config['server'] = {
    'address': '0.0.0.0',
    'port': '6789',
    'log_file': '/var/log/git-webhooks-server.log'
}
# 添加其他部分...
with open(path, 'w') as f:
    config.write(f)
```

### 3. 配置文件路径和权限处理

**问题**: 不同配置级别（system/local/user）对应不同路径和权限要求，如何处理？

**路径映射**:
| 级别 | 路径 | 权限要求 |
|------|------|---------|
| system | `/etc/gitwebhooks.ini` | 需要 root 或 sudo |
| local | `/usr/local/etc/gitwebhooks.ini` | 需要 root 或 sudo |
| user | `~/.gitwebhooks.ini` | 用户目录，无需特殊权限 |

**决策**: **在写入前检测权限，失败时提示用户**

**实现要点**:
- 使用 `os.access(path, os.W_OK)` 检测目录写权限
- 对于 `~` 路径，使用 `os.path.expanduser()` 展开
- 对于系统路径，提示使用 `sudo` 或切换到 user 级别

### 4. 输入验证和错误处理

**问题**: 如何验证用户输入并给出友好的错误提示？

**验证规则**:
| 输入项 | 验证规则 |
|--------|---------|
| 仓库名称 | `owner/repo` 格式（正则：`^[^/]+/[^/]+$`） |
| 本地路径 | 目录存在（`os.path.isdir()`） |
| 部署命令 | 非空字符串 |
| 端口号 | 1-65535 之间的整数 |
| address | 有效的 IP 地址或 `0.0.0.0` |

**决策**: **封装验证逻辑到独立函数，支持重试**

**实现要点**:
```python
def validate_repo_name(value: str) -> bool:
    return bool(re.match(r'^[^/]+/[^/]+$', value))

def validate_existing_path(value: str) -> bool:
    return os.path.isdir(value)

def validate_non_empty(value: str) -> bool:
    return bool(value.strip())
```

### 5. 复选框式事件选择

**问题**: 如何实现 webhook 事件的复选列表选择？

**选项**: push, release, pull_request, tag

**决策**: **使用数字索引选择，逗号分隔多选**

**交互示例**:
```
选择要处理的 webhook 事件（多个用逗号分隔，直接回车默认选 1）:
  1. push
  2. release
  3. pull_request
  4. tag
>
```

**实现要点**:
- 空输入默认选择 `push`
- 解析逗号分隔的数字索引
- 将选择转换为逗号分隔的事件字符串

### 6. 自定义平台配置

**问题**: custom 平台需要额外参数（header_name、header_value、identifier_path、header_event），如何提供示例值？

**默认示例值**:
| 参数 | 示例值 | 说明 |
|------|--------|------|
| header_name | `X-Webhook-Token` | 自定义 header 名称 |
| header_value | `my-secret-token` | 验证用的 header 值 |
| identifier_path | `project.path_with_namespace` | JSON 路径提取仓库标识 |
| header_event | `X-Webhook-Event` | 事件类型 header（可选） |

**决策**: **提供示例值作为默认，允许空输入跳过可选参数**

### 7. 配置文件覆盖处理

**问题**: 当目标配置文件已存在时，如何处理？

**选项**:
1. 直接覆盖（危险）
2. 总是询问
3. 提供备份选项

**决策**: **提供三个选项：覆盖/备份后覆盖/取消**

**交互示例**:
```
配置文件 /etc/gitwebhooks.ini 已存在
选择操作:
  1. 覆盖（会删除原文件）
  2. 备份后覆盖（保存为 .bak）
  3. 取消操作
>
```

### 8. 信号处理和优雅退出

**问题**: 如何处理 Ctrl+C 中断？

**决策**: **使用 `try-except KeyboardInterrupt`，清理部分文件**

**实现要点**:
```python
try:
    # 向导逻辑
    pass
except KeyboardInterrupt:
    print("\n操作已取消")
    # 清理已创建的部分文件
    if os.path.exists(temp_file):
        os.remove(temp_file)
    sys.exit(0)
```

## 技术决策总结

| 决策点 | 选择 | 理由 |
|--------|------|------|
| 交互式输入 | 自建轻量级 Wizard 类 | 完全控制，保持简单 |
| INI 生成 | configparser.ConfigParser | 标准库，格式兼容 |
| 权限检测 | os.access() + 提示 | 提前发现问题 |
| 输入验证 | 独立验证函数 + 重试 | 代码清晰，易测试 |
| 事件选择 | 数字索引，逗号分隔 | 简单直观 |
| 文件覆盖 | 三选一（覆盖/备份/取消） | 安全友好 |
| 信号处理 | KeyboardInterrupt 捕获 | 优雅退出 |

## 依赖清单

- **Python 标准库**: `configparser`, `os`, `sys`, `re`, `pathlib`
- **项目内部模块**: `gitwebhooks.config`（现有配置结构）
- **无外部依赖** ✅

## 未解决问题

无。所有技术决策已明确。
