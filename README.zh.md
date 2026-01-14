# 简易 Git WebHooks 服务

[README](README.md) | [中文说明](README.zh.md)

## 目录
- [简介](#简介)
- [架构](#架构)
- [安装](#安装)
- [卸载](#卸载)
- [使用](#使用)
  - [Github](#github)
  - [Gitee](#gitee)
  - [Gitlab](#gitlab)
  - [自定义](#自定义)
- [配置](#配置)
- [项目结构](#项目结构)

## 简介

轻量级 Git webhook 自动部署服务器。

- 使用 Python 3.6+ 实现（仅标准库）
- 支持 Github、Gitee、Gitlab 及自定义仓库
- 支持为不同仓库指定工作目录和命令
- 可安装为 Systemd 服务
- 模块化架构，易于扩展和测试

## 架构

**2.0 版本** 采用模块化包结构：

```
gitwebhooks/
├── models/          # 数据模型（Provider, Request, Result）
├── config/          # 配置管理
├── auth/            # 签名验证
├── handlers/        # Webhook 处理器
├── utils/           # 工具函数
└── logging/         # 日志配置
```

**核心特性：**
- **依赖注入**：ConfigurationRegistry、VerifierFactory、HandlerFactory
- **抽象基类**：SignatureVerifier、WebhookHandler
- **零外部依赖**：100% Python 标准库
- **原地运行**：CLI 从源码目录运行

## 安装

### 前置要求

- Python 3.6 或更高版本
- pip（Python 包管理器）
- sudo/root 权限（用于安装 systemd 服务）

### 使用 pip 安装

```bash
# 从 PyPI 安装（发布后）
pip install gitwebhooks

# 或从源码安装
git clone https://github.com/troytse/git-webhooks-server.git
cd git-webhooks-server
pip install .
```

### 初始化配置

```bash
# 交互式配置设置（会提示配置级别）
gitwebhooks-cli config init

# 或直接指定配置级别
gitwebhooks-cli config init user      # 用户级（~/.gitwebhooks.ini）
gitwebhooks-cli config init local      # 本地级（/usr/local/etc/gitwebhooks.ini）
sudo gitwebhooks-cli config init system # 系统级（/etc/gitwebhooks.ini，需要 root）
```

向导会提示输入：
1. 配置级别（system/local/user）
2. 服务器配置（地址、端口、日志文件）
3. Git 平台（github/gitee/gitlab/custom）
4. 平台特定设置（webhook 事件、验证、密钥）
5. 仓库配置（名称、工作目录、部署命令）

这将创建具有安全权限（0600）的配置文件。

### 安装为 systemd 服务

```bash
# 安装并启动为 systemd 服务
sudo gitwebhooks-cli service install

# 卸载服务
sudo gitwebhooks-cli service uninstall
```

### 手动安装

如果不使用 pip：

```bash
# 添加执行权限
chmod +x gitwebhooks-cli

# 创建硬链接到系统路径
sudo ln "$(pwd)/gitwebhooks-cli" /usr/local/bin/gitwebhooks-cli
```

### 验证安装

```bash
gitwebhooks-cli --help
```

## 卸载

```bash
# 卸载 systemd 服务（如果已安装）
sudo gitwebhooks-cli service uninstall --purge

# 卸载包
pip uninstall gitwebhooks
```

## 使用

### 1. 配置仓库

编辑 `~/.gitwebhook.ini`：

```ini
[your_name/repository]
cwd=/path/to/your/repository
cmd=git fetch --all && git reset --hard origin/master && git pull
```

### 2. 重启服务

```bash
# 如果作为服务运行
systemctl restart git-webhooks-server

# 或直接运行：
gitwebhooks-cli
```

### 3. 添加 Webhook

#### Github

![github](doc/github.png)
![github-success](doc/github-success.png)

#### Gitee

![gitee](doc/gitee.png)
![gitee-success](doc/gitee-success.png)

#### Gitlab

![gitlab](doc/gitlab.png)
![gitlab-success](doc/gitlab-success.png)

#### 自定义

对于自定义 webhook 来源，配置如下：

```ini
[custom]
# 用于识别来源的请求头
header_name=X-Custom-Header
header_value=Custom-Git-Hookshot
# 用于 Token 验证的请求头
header_token=X-Custom-Token
# 仓库名称在 JSON 数据中的路径
identifier_path=project.path_with_namespace
verify=True
secret=123456
```

处理器接受 `application/json` 或 `application/x-www-form-urlencoded` 格式的 POST 请求。参考 [Github](https://developer.github.com/webhooks/event-payloads/#example-delivery) / [Gitee](https://gitee.com/help/articles/4186) / [Gitlab](https://gitlab.com/help/user/project/integrations/webhooks#push-events) 了解请求格式。

示例数据：
```json
{
  "project": {
    "path_with_namespace": "your_name/repository"
  }
}
```

![custom-header](doc/custom-header.png)
![custom-body](doc/custom-body.png)
![custom-response](doc/custom-response.png)

## 配置

默认配置文件位置：`~/.gitwebhook.ini`

### 初始化配置

```bash
# 交互式配置设置
gitwebhooks-cli config init

# 或直接指定配置级别
gitwebhooks-cli config init user
sudo gitwebhooks-cli config init system
```

### 查看配置

```bash
# 查看当前配置文件（自动检测位置）
gitwebhooks-cli config view

# 查看指定配置文件
gitwebhooks-cli config view -c /path/to/config.ini
```

`config view` 命令显示：
- 配置文件路径和来源（用户指定或自动检测）
- 按节组织的配置内容
- 敏感字段（包含：secret、password、token、key、passphrase）以黄色高亮显示

禁用颜色高亮：
```bash
NO_COLOR=1 gitwebhooks-cli config view
```

### 服务器配置

```ini
[server]
address=0.0.0.0          # 监听地址
port=6789                # 监听端口
log_file=~/.gitwebhook.log  # 日志文件（空值=仅标准输出）
```

### SSL 配置（可选）

```ini
[ssl]
enable=False
key_file=/path/to/key.pem
cert_file=/path/to/cert.pem
```

### 提供者配置

```ini
[github]
verify=True              # 启用签名验证
secret=your_webhook_secret
handle_events=push,pull_request  # 处理的事件（空值=全部）

[gitee]
verify=True
secret=your_webhook_secret

[gitlab]
verify=True
secret=your_webhook_token

[custom]
header_name=X-Custom-Header
header_value=Your-Identifier
header_token=X-Custom-Token
identifier_path=project.path_with_namespace
verify=True
secret=your_secret
```

### 仓库配置

```ini
[owner/repository]
cwd=/path/to/repo    # 工作目录
cmd=your_command     # 要执行的命令
```

## 项目结构

```
git-webhooks-server/
├── gitwebhooks/              # Python 包（模块化 v2.0）
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py                # CLI 入口点
│   ├── server.py             # HTTP 服务器
│   ├── models/               # 数据模型
│   ├── config/               # 配置管理
│   ├── auth/                 # 签名验证
│   ├── handlers/             # Webhook 处理器
│   ├── utils/                # 工具函数
│   └── logging/              # 日志配置
├── gitwebhooks-cli           # CLI 包装脚本
├── install.sh                # 安装脚本
├── git-webhooks-server.ini.sample
└── tests/                    # 测试套件
```

## 开发

### 从源码运行

```bash
# 方式1: 使用 CLI 工具（推荐）
./gitwebhooks-cli -c git-webhooks-server.ini.sample

# 方式2: 使用模块入口
python3 -m gitwebhooks.cli -c git-webhooks-server.ini.sample
```

### 运行测试

```bash
# 使用 pytest
python3 -m pytest tests/

# 或使用 unittest
python3 -m unittest discover tests/
```

## 许可证

MIT License
