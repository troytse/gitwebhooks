# CLI Contract: service 子命令

**Feature**: 001-cli-service-install
**Date**: 2026-01-14

## service install 命令

### 命令格式

```bash
gitwebhooks-cli service install [--force]
```

### 参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--force` | flag | 否 | false | 强制覆盖已存在的服务 |

### 行为规范

#### 正常流程

1. **检测权限**
   - 检查是否有 root 权限
   - 如果没有，输出错误信息并退出（退出码 1）

2. **检查 systemd 可用性**
   - 检测 systemctl 命令是否存在
   - 如果不存在，输出不支持的提示

3. **检查服务是否已安装**
   - 检查 `/etc/systemd/system/git-webhooks-server.service` 是否存在
   - 如果存在且未指定 `--force`，询问用户是否覆盖
   - 用户确认后继续，否则退出

4. **生成服务文件**
   - 使用模板生成 systemd 单元文件
   - ExecStart 指向 `/usr/local/bin/gitwebhooks-cli -c ~/.gitwebhook.ini`

5. **安装服务文件**
   - 复制服务文件到 `/etc/systemd/system/`
   - 执行 `systemctl daemon-reload`

6. **启用并启动服务**
   - 询问用户是否启用并启动服务
   - 如果用户确认，执行：
     - `systemctl enable git-webhooks-server`
     - `systemctl start git-webhooks-server`

7. **输出结果**
   - 显示安装成功信息
   - 显示服务状态提示

#### 错误处理

| 错误场景 | 退出码 | 输出 |
|----------|--------|------|
| 无 root 权限 | 1 | `错误: 此操作需要 root 权限` |
| systemd 不可用 | 1 | `错误: 此系统不支持 systemd` |
| 服务已存在 (无 --force) | 1 | `错误: 服务已安装，使用 --force 强制覆盖` |
| 写入服务文件失败 | 1 | `错误: 无法写入服务文件` |
| systemctl 命令失败 | 0 | `警告: systemctl daemon-reload 失败`（继续安装） |

### 输出格式

#### 成功输出

```
Installing systemd service...
Service file: /etc/systemd/system/git-webhooks-server.service
Reloading systemd daemon...
Enabling service...
Starting service...

Installation complete!
Service status: systemctl status git-webhooks-server
```

#### 错误输出

```
错误: 此操作需要 root 权限
请使用: sudo gitwebhooks-cli service install
```

### 帮助信息

```
Usage: gitwebhooks-cli service install [--force]

Install gitwebhooks as a systemd service.

Options:
  --force    Force overwrite existing service

Examples:
  sudo gitwebhooks-cli service install
  sudo gitwebhooks-cli service install --force
```

---

## service uninstall 命令

### 命令格式

```bash
gitwebhooks-cli service uninstall [--purge]
```

### 参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--purge` | flag | 否 | false | 同时删除配置文件 |

### 行为规范

#### 正常流程

1. **检测权限**
   - 检查是否有 root 权限
   - 如果没有，输出错误信息并退出

2. **检查服务是否已安装**
   - 检查服务文件是否存在
   - 如果不存在，输出提示信息

3. **停止并禁用服务**
   - 执行 `systemctl stop git-webhooks-server`
   - 执行 `systemctl disable git-webhooks-server`

4. **删除服务文件**
   - 删除 `/etc/systemd/system/git-webhooks-server.service`
   - 执行 `systemctl daemon-reload`

5. **处理配置文件**
   - 如果指定了 `--purge`，删除 `~/.gitwebhook.ini`
   - 否则，保留配置文件

6. **输出结果**
   - 显示卸载成功信息

#### 错误处理

| 错误场景 | 退出码 | 输出 |
|----------|--------|------|
| 无 root 权限 | 1 | `错误: 此操作需要 root 权限` |
| 服务未安装 | 1 | `错误: 服务未安装` |
| systemctl 命令失败 | 0 | `警告: systemctl stop 失败`（继续卸载） |

### 输出格式

#### 成功输出

```
Uninstalling systemd service...
Stopping service...
Disabling service...
Removing service file...
Reloading systemd daemon...

Uninstallation complete!
```

#### 带配置清理

```
Uninstalling systemd service...
...
Removing configuration file: ~/.gitwebhook.ini

Uninstallation complete!
```

### 帮助信息

```
Usage: gitwebhooks-cli service uninstall [--purge]

Uninstall the gitwebhooks systemd service.

Options:
  --purge    Also remove configuration file

Examples:
  sudo gitwebhooks-cli service uninstall
  sudo gitwebhooks-cli service uninstall --purge
```

---

## service --help 命令

### 输出格式

```
Usage: gitwebhooks-cli service <command>

Manage systemd service installation.

Commands:
  install    Install as systemd service
  uninstall  Uninstall systemd service

Options:
  -h, --help  Show this help message

Examples:
  sudo gitwebhooks-cli service install
  sudo gitwebhooks-cli service uninstall
```
