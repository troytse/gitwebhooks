# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

这是一个用 Python 3 实现的 Git Webhooks 服务器，用于自动化 Git 仓库部署。支持 Github、Gitee、Gitlab 和自定义仓库的 Webhook 事件处理。

**架构特点**：
- 单文件 Python 应用 (`git-webhooks-server.py`)，约 300 行
- 使用标准库 `http.server` 实现 HTTP 服务器
- 通过 INI 配置文件管理多个仓库的部署命令
- 可作为 systemd 服务安装运行

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
# 手动运行（指定配置文件）
python3 git-webhooks-server.py -c /path/to/config.ini

# 或使用已安装的二进制
git-webhooks-server.py -c /usr/local/etc/git-webhooks-server.ini

# systemd 服务管理
systemctl start git-webhooks-server
systemctl stop git-webhooks-server
systemctl restart git-webhooks-server
systemctl status git-webhooks-server
```

### 测试开发
```bash
# 直接运行（开发模式）
python3 git-webhooks-server.py -c git-webhooks-server.ini.sample
```

## 架构说明

### 核心组件

**RequestHandler 类** (`git-webhooks-server.py:25-221`)
- 继承自 `BaseHTTPRequestHandler`
- `do_GET()`: 拒绝 GET 请求，返回 403
- `do_POST()`: 处理 Webhook POST 请求

**Provider 枚举** (`git-webhooks-server.py:18-23`)
- 定义支持的 Git 平台：Github、Gitee、Gitlab、Custom

**请求处理流程**：
1. `__parse_provider()`: 通过 HTTP Header 识别平台类型
2. `__parse_data()`: 解析 POST 请求体（支持 JSON 和 form-urlencoded）
3. 根据平台验证签名/token
4. 从请求数据中提取仓库名称
5. 在配置中查找对应的仓库配置
6. 执行配置的命令（通过 `subprocess.Popen`）

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

**Github** (`git-webhooks-server.py:90-111`)
- Header: `X-GitHub-Event`
- 签名验证: `X-Hub-Signature` (HMAC-SHA1)
- 仓库标识: `repository.full_name`

**Gitee** (`git-webhooks-server.py:113-146`)
- Header: `X-Gitee-Event`
- 支持签名验证或密码验证
- 仓库标识: `repository.full_name`

**Gitlab** (`git-webhooks-server.py:148-164`)
- Header: `X-Gitlab-Event`
- Token 验证: `X-Gitlab-Token`
- 仓库标识: `project.path_with_namespace`

**Custom** (`git-webhooks-server.py:166-191`)
- 自定义 Header 识别
- 通过 JSON 路径提取仓库标识（如 `project.path_with_namespace`）

## 代码规范

### 编辑器配置
项目使用 `.editorconfig`：
- UTF-8 编码
- LF 换行符
- 4 空格缩进
- 末尾插入空行
- Markdown 文件保留行尾空格

### Python 代码风格
- 遵循 Python 3 标准
- 使用 `logging` 模块记录日志
- 私有方法使用双下划线前缀（如 `__parse_provider`）
- 配置通过 `configparser.ConfigParser` 读取

### Shell 脚本
- `install.sh`: 交互式安装脚本
- `message.sh`: 提供 ANSI 颜色输出函数（INFO、WARN、ERR、QUES）

## 开发注意事项

### 命令执行
当前使用 `subprocess.Popen` 非阻塞执行命令（`git-webhooks-server.py:203`）。代码中有注释说明阻塞式执行会阻塞进程。

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
├── git-webhooks-server.py           # 主程序（单文件应用）
├── git-webhooks-server.ini.sample   # 配置文件模板
├── git-webhooks-server.service.sample # systemd 服务模板
├── install.sh                       # 安装/卸载脚本
├── message.sh                       # 颜色输出辅助脚本
├── README.md                        # 项目说明（英文）
├── README.zh.md                     # 项目说明（中文）
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
- 安装后的二进制: `/usr/local/bin/git-webhooks-server.py`
- systemd 服务: `/usr/lib/systemd/system/git-webhooks-server.service`

## Active Technologies
- Python 3.6+（与主项目一致） + Python 标准库（unittest, subprocess, tempfile, http.client, trace, ssl） (001-test-suite)
- 临时文件系统（tempfile 创建测试配置、目录和日志） (001-test-suite)
- Python 3.6+ (与主项目一致，使用标准库) + Python标准库 (unittest, subprocess, tempfile, http.client, trace, ssl) (001-fix-test-suite)
- INI配置文件 (configparser.ConfigParser) (001-fix-test-suite)
- Bash 4.0+ (macOS 和 Linux 兼容) + 标准 POSIX/Bash 工具（sudo, cp, sed, systemctl, flock, mkdir, rm） (001-optimize-install-script)
- 文件系统（installed.env, .install.lock） (001-optimize-install-script)
- Python 3.6+ (保持与原代码兼容) + Python 3 标准库仅 - 不引入新的外部依赖 (001-optimize-webhooks-server)
- INI 配置文件 (configparser) (001-optimize-webhooks-server)

## Recent Changes
- 001-test-suite: Added Python 3.6+（与主项目一致） + Python 标准库（unittest, subprocess, tempfile, http.client, trace, ssl）
