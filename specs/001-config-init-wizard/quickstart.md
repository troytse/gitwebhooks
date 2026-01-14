# Quickstart Guide: config init 交互式向导

**Feature**: 001-config-init-wizard
**Date**: 2025-01-14

## Overview

本指南提供 `config init` 交互式向导功能的快速上手说明。

## Prerequisites

- Python 3.7+
- 已安装 git-webhooks-server
- 对 Git webhook 概念有基本了解

## Basic Usage

### 1. 启动交互式向导

```bash
gitwebhooks-cli config init
```

### 2. 选择配置级别

向导会提示选择配置级别：

```
选择配置级别:
  1. system (/etc/gitwebhooks.ini)
  2. local (/usr/local/etc/gitwebhooks.ini)
  3. user (~/.gitwebhooks.ini)
输入选择 [1-3]:
```

| 级别 | 路径 | 适用场景 |
|------|------|---------|
| system | `/etc/gitwebhooks.ini` | 全局服务，需要 root |
| local | `/usr/local/etc/gitwebhooks.ini` | 单机部署，需要 root |
| user | `~/.gitwebhooks.ini` | 个人开发，无需 root |

### 3. 配置服务器参数

```
服务器监听地址 [默认: 0.0.0.0]:
服务器端口 [默认: 6789]:
日志文件路径 [默认: /var/log/git-webhooks-server.log]:
```

**提示**: 直接按回车使用默认值。

### 4. 选择 Git 平台

```
选择 Git 平台:
  1. github
  2. gitee
  3. gitlab
  4. custom
输入选择 [1-4]:
```

### 5. 配置平台参数

```
选择要处理的 webhook 事件（多个用逗号分隔，直接回车默认选 1）:
  1. push
  2. release
  3. pull_request
  4. tag
输入选择: 1,3
是否启用签名验证？ [y/N]: y
输入验证密钥: my-webhook-secret-123
```

**提示**:
- 多选事件用逗号分隔，如 `1,3`
- 直接回车默认选择 `push` 事件

### 6. 配置仓库信息

```
输入仓库名称 (格式: owner/repo): myuser/myproject
输入工作目录路径 (必须已存在): /home/myuser/projects/myproject
输入部署命令: git pull && npm install && npm run build
```

**注意**: 工作目录必须已存在，向导不会自动创建。

### 7. 完成配置

```
配置文件已生成: /home/myuser/.gitwebhooks.ini
后续步骤:
  1. 检查配置文件内容: gitwebhooks-cli config view /home/myuser/.gitwebhooks.ini
  2. 启动服务器: gitwebhooks-cli -c /home/myuser/.gitwebhooks.ini
  3. 或安装为服务: sudo gitwebhooks-cli service install
```

## Advanced Usage

### 直接指定配置级别

```bash
# 生成系统级配置
sudo gitwebhooks-cli config init system

# 生成本地级配置
sudo gitwebhooks-cli config init local

# 生成用户级配置
gitwebhooks-cli config init user
```

### 配置 Custom 平台

选择 `custom` 平台时，会额外询问：

```
输入识别 Header 名称 [默认: X-Webhook-Token]: X-My-Webhook
输入验证 Header 值: my-secret-token
输入仓库标识 JSON 路径 [默认: project.path_with_namespace]: repo.full_name
输入事件类型 Header 名称 [可选，直接回车跳过]: X-Event-Name
```

### 处理已存在的配置文件

如果目标位置已有配置文件：

```
配置文件 /etc/gitwebhooks.ini 已存在
选择操作:
  1. 覆盖（会删除原文件）
  2. 备份后覆盖（保存为 .bak）
  3. 取消操作
输入选择 [1-3]:
```

## Common Scenarios

### 场景 1: GitHub 仓库自动部署

```bash
gitwebhooks-cli config init user
# 选择: user
# 地址: [回车使用默认 0.0.0.0]
# 端口: [回车使用默认 6789]
# 日志: [回车使用默认]
# 平台: 1 (github)
# 事件: [回车默认 push]
# 验证: y
# 密钥: [输入 GitHub webhook secret]
# 仓库: username/my-repo
# 目录: /home/user/projects/my-repo
# 命令: git pull && ./deploy.sh
```

### 场景 2: Gitee 私有仓库

```bash
gitwebhooks-cli config init local
# ... 按提示输入 ...
```

### 场景 3: 配置多个仓库

向导只能创建一个仓库配置。添加更多仓库需要手动编辑配置文件：

```bash
# 使用向导创建初始配置
gitwebhooks-cli config init user

# 手动编辑添加更多仓库
vim ~/.gitwebhooks.ini
```

在配置文件中添加：
```ini
[repo/owner/repo1]
cwd = /path/to/repo1
cmd = deploy1.sh

[repo/owner/repo2]
cwd = /path/to/repo2
cmd = deploy2.sh
```

## Troubleshooting

### 权限不足

```
错误: 无法写入 /etc/gitwebhooks.ini（权限不足）
建议: 使用 sudo 或选择 user 级别
```

**解决方案**:
- 使用 `sudo gitwebhooks-cli config init system`
- 或选择 `user` 级别：`gitwebhooks-cli config init user`

### 工作目录不存在

```
错误: 目录不存在: /path/to/project
```

**解决方案**:
- 先创建目录：`mkdir -p /path/to/project`
- 然后重新运行向导

### 仓库名称格式错误

```
错误: 仓库名称格式不正确，应为 owner/repo 格式
```

**解决方案**:
- 输入正确的格式，如：`myusername/myproject`
- 不要包含 `https://` 或 `.git` 后缀

### 中断操作

按 `Ctrl+C` 可随时取消向导，已创建的部分文件会被清理。

## Best Practices

1. **先测试后部署**: 使用 `user` 级别配置测试，确认无误后再升级到 `system`
2. **备份现有配置**: 选择"备份后覆盖"选项保护原有配置
3. **验证生成的配置**: 使用 `gitwebhooks-cli config view` 检查配置内容
4. **启用签名验证**: 生产环境务必启用 webhook 签名验证
5. **工作目录权限**: 确保部署命令有足够权限访问工作目录

## Next Steps

配置完成后：

1. **查看配置**: `gitwebhooks-cli config view <config-file>`
2. **测试运行**: `gitwebhooks-cli -c <config-file>`
3. **配置 Git 平台 webhook**: 在 GitHub/Gitee/GitLab 上配置 webhook URL
4. **安装为服务**: `sudo gitwebhooks-cli service install`
