# Data Model: 配置文件查看命令

**Feature**: 001-config-view
**Date**: 2026-01-14

## Overview

`config view` 命令主要涉及配置文件的读取和显示，不引入新的持久化数据模型。本功能使用现有的配置加载基础设施。

## Entities

### ConfigFileLocator

配置文件定位器，负责按优先级查找配置文件。

**Attributes**:
- `search_paths`: List[str] - 配置文件搜索路径列表（按优先级排序）
- `user_specified_path`: Optional[str] - 用户通过 `-c` 参数指定的路径

**Methods**:
- `find_config_file() -> Optional[Path]` - 查找第一个存在的配置文件
- `get_source_type(path: Path) -> str` - 返回配置来源类型（"user-specified" 或 "auto-detected"）

**State Transitions**:
```
Initial → Searching → Found / Not Found
```

### ConfigDisplayFormatter

配置显示格式化器，负责将配置内容格式化为可读输出。

**Attributes**:
- `sensitive_keywords`: Set[str] - 敏感字段关键词集合
- `use_color`: bool - 是否启用颜色高亮

**Methods**:
- `format_header(path: Path, source: str) -> str` - 格式化配置来源头部
- `format_config(parser: ConfigParser) -> str` - 格式化配置内容
- `format_sensitive_field(key: str, value: str) -> str` - 格式化敏感字段
- `is_sensitive_key(key: str) -> bool` - 判断键名是否为敏感字段

**Validation Rules**:
- 敏感关键词：`secret`, `password`, `token`, `key`, `passphrase`（小写匹配）
- 颜色支持：检测 `NO_COLOR` 环境变量和 `TERM` 环境变量

### ConfigParser (Existing)

使用 Python 标准库的 `configparser.ConfigParser` 类。

**Relationships**:
- `ConfigFileLocator` 返回的路径用于初始化 `ConfigParser`
- `ConfigDisplayFormatter` 接受 `ConfigParser` 实例进行格式化

## Data Flow

```
User Input (args)
    ↓
ConfigFileLocator.find_config_file()
    ↓
ConfigParser.read(path)
    ↓
ConfigDisplayFormatter.format_*()
    ↓
Output to stdout
```

## Edge Cases Handling

| Case | Detection | Response |
|------|-----------|----------|
| 配置文件不存在 | `Path.exists()` returns False | 列出所有搜索路径，提示使用 `config init` |
| 空配置文件 | `ConfigParser.sections()` is empty | 显示文件路径，提示文件为空或无有效配置节 |
| 无效的 INI 格式 | `configparser.Error` exception | 显示完整错误信息，包括行号和问题描述 |
| 无读取权限 | `PermissionError` exception | 显示权限错误，说明需要的权限级别 |
| 符号链接 | `Path.is_symlink()` | 显示链接路径和实际文件路径 |
| 路径包含特殊字符 | `Path` 对象处理 | 正确转义和显示路径 |
| 终端不支持颜色 | `NO_COLOR` env var or `TERM=dumb` | 禁用颜色高亮 |

## Configuration Path Constants

新增配置文件路径常量（将添加到 `gitwebhooks/utils/constants.py`）：

```python
# Configuration file paths (in priority order)
CONFIG_PATH_USER = "~/.gitwebhooks.ini"
CONFIG_PATH_LOCAL = "/usr/local/etc/gitwebhooks.ini"
CONFIG_PATH_SYSTEM = "/etc/gitwebhooks.ini"
CONFIG_SEARCH_PATHS = [CONFIG_PATH_USER, CONFIG_PATH_LOCAL, CONFIG_PATH_SYSTEM]

# Sensitive field keywords
SENSITIVE_KEYWORDS = {"secret", "password", "token", "key", "passphrase"}

# ANSI color codes for sensitive field highlighting
COLOR_SENSITIVE = "\033[33m"  # Yellow
COLOR_RESET = "\033[0m"
```

## Validation Rules

### Input Validation
- `-c` 参数路径必须为有效字符串
- 路径可以是相对路径、绝对路径或包含 `~` 的路径

### Output Validation
- 配置文件必须存在且可读
- 配置文件必须是有效的 INI 格式
- 敏感字段检测使用子字符串匹配（不区分大小写）
