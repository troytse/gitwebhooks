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
- sudo/root 权限（用于安装）

### 从源码安装

```bash
# 克隆或下载仓库
git clone https://github.com/troytse/git-webhooks-server.git
cd git-webhooks-server

# 运行安装脚本
./install.sh
```

安装程序将：
1. 在 `/usr/local/bin` 创建 `gitwebhooks-cli` 硬链接
2. 复制配置文件到 `/usr/local/etc/git-webhooks-server.ini`
3. 可选：安装为 systemd 服务

![install](doc/install.png)

### 手动安装

如果不使用安装脚本：

```bash
# 添加执行权限
chmod +x gitwebhooks-cli

# 创建硬链接到系统路径
sudo ln "$(pwd)/gitwebhooks-cli" /usr/local/bin/gitwebhooks-cli

# 复制配置文件
sudo cp git-webhooks-server.ini.sample /usr/local/etc/git-webhooks-server.ini
```

### 验证安装

```bash
gitwebhooks-cli --help
```

## 卸载

```bash
cd git-webhooks-server
./install.sh --uninstall
```

![uninstall](doc/uninstall.png)

## 使用

### 1. 配置仓库

编辑 `/usr/local/etc/git-webhooks-server.ini`：

```ini
[your_name/repository]
cwd=/path/to/your/repository
cmd=git fetch --all && git reset --hard origin/master && git pull
```

### 2. 重启服务

```bash
systemctl restart git-webhooks-server
# 或直接运行：
gitwebhooks-cli -c /usr/local/etc/git-webhooks-server.ini
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

默认配置文件位置：`/usr/local/etc/git-webhooks-server.ini`

### 服务器配置

```ini
[server]
address=0.0.0.0          # 监听地址
port=6789                # 监听端口
log_file=/var/log/git-webhooks-server.log  # 日志文件（空值=仅标准输出）
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
