# API Contracts: config init 交互式向导

**Feature**: 001-config-init-wizard
**Date**: 2025-01-14

## Overview

本文档定义 `config init` 交互式向导功能的 API 合约。由于本功能是 CLI 命令，"API" 指的是向导类的公共接口。

## Wizard Class API

### `Wizard`

交互式配置向导类，负责收集用户配置并生成 INI 文件。

#### Methods

##### `__init__(self, level: Optional[str] = None)`

初始化向导实例。

**Parameters**:
- `level` (Optional[str]): 配置级别，`system`/`local`/`user` 或 None（交互式选择）

**Behavior**:
- 如果 level 为 None，将在运行时询问用户选择
- 如果 level 提供且无效，抛出 `ValueError`

---

##### `run(self) -> str`

运行向导流程，返回生成的配置文件路径。

**Returns**:
- `str`: 生成的配置文件的绝对路径

**Raises**:
- `KeyboardInterrupt`: 用户按 Ctrl+C 中断
- `PermissionError`: 目标目录无写权限
- `FileExistsError`: 用户选择不覆盖已存在的文件

**Flow**:
1. 确定配置级别（如果未指定）
2. 检查目标目录写权限
3. 收集服务器配置
4. 收集平台配置
5. 收集仓库配置
6. 确认文件覆盖（如需要）
7. 生成 INI 文件
8. 显示完成信息

---

##### `_select_level(self) -> str`

交互式选择配置级别。

**Returns**:
- `str`: 选择的级别名称（`system`/`local`/`user`）

**User Interaction**:
```
选择配置级别:
  1. system (/etc/gitwebhooks.ini)
  2. local (/usr/local/etc/gitwebhooks.ini)
  3. user (~/.gitwebhooks.ini)
输入选择 [1-3]:
```

---

##### `_collect_server_config(self) -> ServerConfig`

收集服务器配置参数。

**Returns**:
- `ServerConfig`: 服务器配置对象

**User Interaction**:
```
服务器监听地址 [默认: 0.0.0.0]:
服务器端口 [默认: 6789]:
日志文件路径 [默认: /var/log/git-webhooks-server.log]:
```

---

##### `_select_platform(self) -> str`

选择 Git 平台类型。

**Returns**:
- `str`: 平台名称（`github`/`gitee`/`gitlab`/`custom`）

**User Interaction**:
```
选择 Git 平台:
  1. github
  2. gitee
  3. gitlab
  4. custom
输入选择 [1-4]:
```

---

##### `_collect_platform_config(self, platform: str) -> PlatformConfig`

收集平台配置参数。

**Parameters**:
- `platform` (str): 平台名称

**Returns**:
- `PlatformConfig`: 平台配置对象

**User Interaction**:
```
选择要处理的 webhook 事件（多个用逗号分隔，直接回车默认选 1）:
  1. push
  2. release
  3. pull_request
  4. tag
输入选择:
是否启用签名验证？ [y/N]:
输入验证密钥:
```

对于 custom 平台，额外询问：
```
输入识别 Header 名称 [默认: X-Webhook-Token]:
输入验证 Header 值:
输入仓库标识 JSON 路径 [默认: project.path_with_namespace]:
输入事件类型 Header 名称 [可选，直接回车跳过]:
```

---

##### `_collect_repository_config(self) -> RepositoryConfig`

收集仓库配置参数。

**Returns**:
- `RepositoryConfig`: 仓库配置对象

**User Interaction**:
```
输入仓库名称 (格式: owner/repo):
输入工作目录路径 (必须已存在):
输入部署命令:
```

---

##### `_confirm_overwrite(self, path: str) -> bool`

确认是否覆盖已存在的配置文件。

**Parameters**:
- `path` (str): 已存在的文件路径

**Returns**:
- `bool`: True 表示继续覆盖，False 表示取消

**User Interaction**:
```
配置文件 /etc/gitwebhooks.ini 已存在
选择操作:
  1. 覆盖（会删除原文件）
  2. 备份后覆盖（保存为 .bak）
  3. 取消操作
输入选择 [1-3]:
```

---

##### `_generate_config(self, server: ServerConfig, platform: PlatformConfig, repo: RepositoryConfig) -> configparser.ConfigParser`

生成配置对象。

**Parameters**:
- `server` (ServerConfig): 服务器配置
- `platform` (PlatformConfig): 平台配置
- `repo` (RepositoryConfig): 仓库配置

**Returns**:
- `configparser.ConfigParser`: 配置对象

**Behavior**:
- 创建 INI 配置结构
- 填充 [server] 部分
- 填充平台部分（[github]/[gitee]/[gitlab]/[custom]）
- 填充仓库部分（[repo/owner/name]）

---

##### `_write_config(self, config: configparser.ConfigParser, path: str, backup: bool = False)`

写入配置文件。

**Parameters**:
- `config` (ConfigParser): 配置对象
- `path` (str): 目标文件路径
- `backup` (bool): 是否备份原文件

**Behavior**:
- 如果 backup=True 且文件存在，先重命名为 `.bak`
- 写入配置到文件
- 设置文件权限为 0600（用户读写）

---

##### `_show_completion(self, path: str)`

显示完成信息。

**Parameters**:
- `path` (str): 生成的文件路径

**User Output**:
```
配置文件已生成: /etc/gitwebhooks.ini
后续步骤:
  1. 检查配置文件内容: gitwebhooks-cli config view /etc/gitwebhooks.ini
  2. 启动服务器: gitwebhooks-cli -c /etc/gitwebhooks.ini
  3. 或安装为服务: sudo gitwebhooks-cli service install
```

## CLI Command Interface

### `config init` 子命令

#### Usage

```bash
gitwebhooks-cli config init [level]
```

#### Arguments

- `level` (optional): 配置级别
  - Values: `system`, `local`, `user`
  - Default: 交互式选择

#### Exit Codes

| Code | 含义 |
|------|------|
| 0 | 成功生成配置文件 |
| 1 | 用户取消操作（Ctrl+C 或选择取消覆盖） |
| 2 | 权限不足 |
| 3 | 输入验证失败 |

#### Examples

```bash
# 交互式选择配置级别
gitwebhooks-cli config init

# 直接生成系统级配置
gitwebhooks-cli config init system

# 生成用户级配置
gitwebhooks-cli config init user
```

## Module Structure

```
gitwebhooks/
├── cli/
│   ├── __init__.py
│   ├── service.py      # 现有的 service 子命令
│   ├── config.py       # 现有的 config 子命令（view）
│   └── init_wizard.py  # 新增：交互式向导实现
```

## Integration Points

### Existing Modules

| 模块 | 用途 |
|------|------|
| `gitwebhooks.config.loader` | 配置加载（用于验证生成的配置） |
| `gitwebhooks.models.provider` | Provider 枚举（平台类型） |
| `gitwebhooks.config.models` | 配置数据类 |

### New Module

| 模块 | 职责 |
|------|------|
| `gitwebhooks.cli.init_wizard` | 交互式向导类和辅助函数 |
