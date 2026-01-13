# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

这是一个用 Python 3 实现的 Git Webhooks 服务器，用于自动化 Git 仓库部署。支持 Github、Gitee、Gitlab 和自定义仓库的 Webhook 事件处理。

**架构特点**：
- 模块化 Python 包结构 (`gitwebhooks/`)
- 使用标准库 `http.server` 实现 HTTP 服务器
- 通过 INI 配置文件管理多个仓库的部署命令
- 可作为 systemd 服务安装运行
- 原地运行：CLI 从源码目录加载模块

## 常用命令

### 安装和卸载
```bash
# 安装（交互式）
./install.sh

# 卸载
./install.sh --uninstall
```

### 运行服务
```bash
# 方式1: 使用模块入口
python3 -m gitwebhooks.cli -c /path/to/config.ini

# 方式2: 使用 CLI 工具（安装后）
gitwebhooks-cli -c /path/to/config.ini

# systemd 服务管理
systemctl start git-webhooks-server
systemctl stop git-webhooks-server
systemctl restart git-webhooks-server
systemctl status git-webhooks-server
```

### 测试开发
```bash
# 直接运行（开发模式）
./gitwebhooks-cli -c git-webhooks-server.ini.sample

# 或使用模块方式
python3 -m gitwebhooks.cli -c git-webhooks-server.ini.sample

# 运行测试套件
python3 -m pytest tests/
```

## 架构说明

### 核心组件

**模块化包结构** (`gitwebhooks/`)
- `__init__.py`: 包入口，导出主要类
- `__main__.py`: 模块入口，支持 `python3 -m gitwebhooks`
- `cli.py`: 命令行入口点
- `server.py`: 主服务器类 `WebhookServer`

**子模块**：
- `models/`: 数据模型（Provider、WebhookRequest、验证结果等）
- `config/`: 配置加载和注册（ConfigLoader、ConfigurationRegistry）
- `auth/`: 签名验证模块（各平台的验证器工厂）
- `handlers/`: Webhook 处理器（按平台分离的处理器）
- `utils/`: 工具类（常量、异常、命令执行器）
- `logging/`: 日志配置

**CLI 工具** (`gitwebhooks-cli`)
- Bash 包装脚本，自动检测并加载 `gitwebhooks` 包
- 支持从源码目录运行或已安装的包运行

**Provider 枚举** (`gitwebhooks/models/provider.py`)
- 定义支持的 Git 平台：Github、Gitee、Gitlab、Custom

**请求处理流程**：
1. `WebhookRequestHandler.do_POST()`: 接收 POST 请求
2. `_parse_provider()`: 通过 HTTP Header 识别平台类型
3. `_parse_data()`: 解析 POST 请求体（支持 JSON 和 form-urlencoded）
4. 平台处理器验证签名/token
5. 从请求数据中提取仓库名称
6. 在配置中查找对应的仓库配置
7. 执行配置的命令（通过 `subprocess.Popen`）

### 配置结构

配置文件采用 INI 格式，主要分为几部分：

```ini
[server]          # 服务器配置：address、port、log_file
[ssl]             # SSL 配置：enable、key_file、cert_file
[github]          # Github 配置：handle_events、verify、secret
[gitee]           # Gitee 配置
[gitlab]          # Gitlab 配置
[custom]          # 自定义配置：header_name、header_value、identifier_path
[repo/name]       # 仓库配置：cwd、cmd
```

**仓库配置部分**：
- 每个仓库一节，节名为 `owner/repo` 格式
- `cwd`: 工作目录
- `cmd`: 收到 Webhook 时执行的 shell 命令

### 平台特定处理

**Github** (`gitwebhooks/handlers/github.py`)
- Header: `X-GitHub-Event`
- 签名验证: `X-Hub-Signature` (HMAC-SHA1)
- 仓库标识: `repository.full_name`
- 验证器: `auth/github.py`

**Gitee** (`gitwebhooks/handlers/gitee.py`)
- Header: `X-Gitee-Event`
- 支持签名验证或密码验证
- 仓库标识: `repository.full_name`
- 验证器: `auth/gitee.py`

**Gitlab** (`gitwebhooks/handlers/gitlab.py`)
- Header: `X-Gitlab-Event`
- Token 验证: `X-Gitlab-Token`
- 仓库标识: `project.path_with_namespace`
- 验证器: `auth/gitlab.py`

**Custom** (`gitwebhooks/handlers/custom.py`)
- 自定义 Header 识别
- 通过 JSON 路径提取仓库标识（如 `project.path_with_namespace`）
- 验证器: `auth/custom.py`

## 代码规范

### 编辑器配置
项目使用 `.editorconfig`：
- UTF-8 编码
- LF 换行符
- 4 空格缩进
- 末尾插入空行
- Markdown 文件保留行尾空格

### Python 代码风格
- 遵循 Python 3.6+ 标准
- 使用 `logging` 模块记录日志
- 私有方法使用单下划线前缀（如 `_parse_provider`）
- 公有 API 不使用下划线前缀
- 配置通过 `configparser.ConfigParser` 读取
- 类型提示使用 `typing` 模块
- 自定义异常继承自 `Exception`

### Shell 脚本
- `install.sh`: 交互式安装脚本
- `message.sh`: 提供 ANSI 颜色输出函数（INFO、WARN、ERR、QUES）

## 开发注意事项

### 命令执行
当前使用 `subprocess.Popen` 非阻塞执行命令（`gitwebhooks/utils/executor.py`）。命令在后台运行，不阻塞服务器进程。

### 日志配置
- 日志文件位置在配置文件的 `server.log_file` 指定
- 日志同时输出到文件和标准输出（如果配置了日志文件）

### SSL 支持
- 通过配置文件的 `[ssl]` 部分启用
- 需要提供证书文件和密钥文件路径

### 自定义平台
使用 `[custom]` 配置可以支持任意 Webhook 源：
- `header_name/header_value`: 识别请求来源
- `header_token`: token 验证的 header 名称
- `identifier_path`: JSON 路径，用于提取仓库标识
- `header_event`: 可选，事件类型 header 名称

## 文件结构

```
git-webhooks-server/
├── gitwebhooks-cli                  # CLI 命令行工具
├── gitwebhooks/                     # 主包目录
│   ├── __init__.py                  # 包入口
│   ├── __main__.py                  # 模块入口
│   ├── cli.py                       # CLI 实现
│   ├── server.py                    # 主服务器类
│   ├── auth/                        # 签名验证模块
│   │   ├── __init__.py
│   │   ├── factory.py               # 验证器工厂
│   │   ├── verifier.py              # 验证器基类
│   │   ├── github.py                # GitHub 验证器
│   │   ├── gitee.py                 # Gitee 验证器
│   │   ├── gitlab.py                # GitLab 验证器
│   │   └── custom.py                # 自定义验证器
│   ├── config/                      # 配置模块
│   │   ├── __init__.py
│   │   ├── loader.py                # 配置加载器
│   │   ├── registry.py              # 配置注册表
│   │   ├── models.py                # 配置数据类
│   │   └── server.py                # 服务器配置
│   ├── handlers/                    # Webhook 处理器
│   │   ├── __init__.py
│   │   ├── request.py               # 请求处理器基类
│   │   ├── factory.py               # 处理器工厂
│   │   ├── github.py                # GitHub 处理器
│   │   ├── gitee.py                 # Gitee 处理器
│   │   ├── gitlab.py                # GitLab 处理器
│   │   └── custom.py                # 自定义处理器
│   ├── models/                      # 数据模型
│   │   ├── __init__.py
│   │   ├── provider.py              # Provider 枚举
│   │   ├── request.py               # 请求数据类
│   │   └── result.py                # 验证结果类
│   ├── utils/                       # 工具模块
│   │   ├── __init__.py
│   │   ├── constants.py             # 常量定义
│   │   ├── exceptions.py            # 自定义异常
│   │   └── executor.py              # 命令执行器
│   └── logging/                     # 日志模块
│       └── setup.py                 # 日志配置
├── tests/                           # 测试套件
│   ├── unit/                        # 单元测试
│   ├── integration/                 # 集成测试
│   ├── utils/                       # 测试工具
│   └── conftest.py                  # pytest 配置
├── git-webhooks-server.ini.sample   # 配置文件模板
├── git-webhooks-server.service.sample # systemd 服务模板
├── install.sh                       # 安装/卸载脚本
├── message.sh                       # 颜色输出辅助脚本
├── README.md                        # 项目说明（英文）
├── README.zh.md                     # 项目说明（中文）
├── CLAUDE.md                        # Claude Code 项目指南
├── .editorconfig                    # 编辑器配置
├── .gitignore                       # Git 忽略文件
├── doc/                             # 文档截图目录
└── .specify/                        # SpecKit 工作流模板目录
    ├── templates/                   # 功能规格、计划、任务模板
    ├── scripts/                     # 辅助脚本
    └── memory/                      # 工作流记忆存储
```

## 配置文件位置

- 默认配置路径: `/usr/local/etc/git-webhooks-server.ini`
- 日志文件: `/var/log/git-webhooks-server.log`
- 安装后的 CLI: `/usr/local/bin/gitwebhooks-cli`
- systemd 服务: `/usr/lib/systemd/system/git-webhooks-server.service`

## Active Technologies
- Python 3.6+ + Python 标准库（无外部依赖）
- 模块化包结构 (`gitwebhooks/`)
- INI 配置文件 (configparser.ConfigParser)
- http.server (HTTP 服务器)
- subprocess (命令执行)
- ssl (HTTPS 支持)
- pytest (测试框架)
- Bash 4.0+ (安装脚本)

## Recent Changes
- 001-refactor-codebase: 重构为模块化包结构，保持向后兼容
