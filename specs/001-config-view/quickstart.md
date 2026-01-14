# Quickstart: 配置文件查看命令

**Feature**: 001-config-view
**Date**: 2026-01-14

## Usage Overview

`config view` 命令用于查看当前生效的 Git Webhooks Server 配置文件位置和内容。

## Basic Usage

### 查看默认配置文件

```bash
gitwebhooks-cli config view
```

按优先级查找配置文件（`~/.gitwebhooks.ini` > `/usr/local/etc/gitwebhooks.ini` > `/etc/gitwebhooks.ini`），显示第一个找到的配置文件。

### 查看指定配置文件

```bash
gitwebhooks-cli config view -c /path/to/config.ini
```

显示指定的配置文件。

## Output Format

### 配置来源头部

```
Config File: /home/user/.gitwebhooks.ini (source: auto-detected)
```

或

```
Config File /custom/path/config.ini (source: user-specified)
```

### 配置内容显示

配置按节分组显示：

```
[server]
address = 0.0.0.0
port = 6789
log_file = /var/log/git-webhooks-server.log

[github]
handle_events = push
verify = true
secret = ******** (yellow highlighted)

[repo/example]
cwd = /var/www/example
cmd = git pull
```

### 敏感字段高亮

包含以下关键词的配置项将被黄色高亮显示：
- `secret`
- `password`
- `token`
- `key`
- `passphrase`

## Examples

### Example 1: 查看用户配置

```bash
$ gitwebhooks-cli config view
Config File: /home/user/.gitwebhooks.ini (source: auto-detected)

[server]
address = 0.0.0.0
port = 6789
log_file = /var/log/git-webhooks-server.log

[github]
handle_events = push
verify = true
secret = my_webhook_secret

[repo/myproject]
cwd = /var/www/myproject
cmd = git pull && ./deploy.sh
```

### Example 2: 查看系统配置

```bash
$ sudo gitwebhooks-cli config view -c /etc/gitwebhooks.ini
Config File: /etc/gitwebhooks.ini (source: user-specified)

[server]
address = 0.0.0.0
port = 6789
log_file = /var/log/git-webhooks-server.log

[ssl]
enable = true
key_file = /etc/ssl/private/server.key
cert_file = /etc/ssl/certs/server.crt
```

### Example 3: 配置文件不存在

```bash
$ gitwebhooks-cli config view
Error: No configuration file found.

Searched paths (in priority order):
  1. /home/user/.gitwebhooks.ini
  2. /usr/local/etc/gitwebhooks.ini
  3. /etc/gitwebhooks.ini

To create a configuration file, run:
  gitwebhooks-cli config init
```

### Example 4: 无效的配置格式

```bash
$ gitwebhooks-cli config view
Error: Failed to parse configuration file: /home/user/.gitwebhooks.ini

Parsing error: File contains parsing errors: /home/user/.gitwebhooks.ini
  [line 12]: 'invalid section'

Please check the file format and fix any syntax errors.
```

## Environment Variables

### NO_COLOR

设置 `NO_COLOR` 环境变量可禁用敏感字段颜色高亮：

```bash
NO_COLOR=1 gitwebhooks-cli config view
```

## Integration with Existing Commands

### 与 config init 配合使用

1. 创建配置：`gitwebhooks-cli config init`
2. 查看配置：`gitwebhooks-cli config view`
3. 编辑配置（手动）：`vim ~/.gitwebhooks.ini`
4. 验证配置：`gitwebhooks-cli config view`

### 与服务管理配合使用

```bash
# 查看当前配置
gitwebhooks-cli config view

# 重启服务以应用配置更改
sudo systemctl restart git-webhooks-server

# 查看服务状态
sudo systemctl status git-webhooks-server
```

## Troubleshooting

### 权限错误

如果遇到权限错误：

```bash
$ gitwebhooks-cli config view -c /etc/gitwebhooks.ini
Error: Permission denied: /etc/gitwebhooks.ini

Please check file permissions or run with appropriate privileges.
```

使用 `sudo` 或检查文件权限：

```bash
sudo gitwebhooks-cli config view -c /etc/gitwebhooks.ini
# 或
ls -l /etc/gitwebhooks.ini
```

### 符号链接

符号链接会被自动解析：

```bash
$ gitwebhooks-cli config view
Config File: /etc/gitwebhooks.ini -> /usr/local/etc/gitwebhooks.ini.prod (source: auto-detected)

[server]
...
```

## Testing

### 手动测试

1. 创建测试配置文件：
```bash
gitwebhooks-cli config init -o /tmp/test-config.ini
```

2. 查看配置：
```bash
gitwebhooks-cli config view -c /tmp/test-config.ini
```

3. 验证敏感字段高亮（检查黄色显示）

### 自动化测试

运行单元测试：

```bash
python -m pytest tests/unit/cli/test_config_view.py
```

运行集成测试：

```bash
python -m pytest tests/integration/test_config_view_integration.py
```
