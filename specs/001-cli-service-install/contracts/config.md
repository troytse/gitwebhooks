# CLI Contract: config 子命令

**Feature**: 001-cli-service-install
**Date**: 2026-01-14

## config init 命令

### 命令格式

```bash
gitwebhooks-cli config init [--output PATH]
```

### 参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--output` | string | 否 | `~/.gitwebhook.ini` | 输出配置文件路径 |

### 行为规范

#### 正常流程

1. **检查输出路径**
   - 展开路径中的 `~` 和环境变量
   - 检查目录是否存在，不存在则创建

2. **检查文件是否已存在**
   - 如果配置文件已存在，询问用户是否覆盖
   - 用户确认后继续，否则退出

3. **启动问答流程**
   - 按顺序询问用户配置项
   - 显示默认值（用户直接回车使用默认值）
   - 验证用户输入

4. **生成配置文件**
   - 将收集的配置写入 INI 文件
   - 设置文件权限为 0600

5. **输出结果**
   - 显示配置文件创建成功信息

#### 问答流程

##### 基本配置

| 问题 | 键 | 默认值 | 验证 |
|------|-----|--------|------|
| 服务器监听地址 | `server.address` | `0.0.0.0` | IP 或 hostname |
| 服务器端口 | `server.port` | `6789` | 1-65535 |
| 日志文件路径 | `server.log_file` | `~/.gitwebhook.log` | 可写路径 |

##### SSL 配置

| 问题 | 键 | 默认值 | 条件 |
|------|-----|--------|------|
| 是否启用 SSL | `ssl.enable` | `false` | 是/否 |
| SSL 密钥文件 | `ssl.key_file` | (必填) | enable=true |
| SSL 证书文件 | `ssl.cert_file` | (必填) | enable=true |

##### Webhook 平台配置

对每个平台（GitHub, Gitee, GitLab, Custom）：

| 问题 | 键 | 默认值 |
|------|-----|--------|
| 是否配置 {平台} | - | 是/否 |
| 启用签名验证 | `{platform}.verify` | `true` |
| Webhook secret/token | `{platform}.secret` | (可选) |

##### Custom 平台额外配置

| 问题 | 键 | 默认值 |
|------|-----|--------|
| Header 名称 | `custom.header_name` | (必填) |
| Header 值 | `custom.header_value` | (必填) |
| Token Header | `custom.header_token` | (可选) |
| 标识路径 | `custom.identifier_path` | (必填) |

#### 输入验证

| 输入类型 | 验证规则 | 错误提示 |
|----------|----------|----------|
| IP 地址 | 有效 IPv4 格式 | `无效的 IP 地址` |
| 端口 | 1-65535 整数 | `端口号必须在 1-65535 之间` |
| 路径 | 可写或可创建 | `路径不可写` |
| 布尔值 | y/Y/n/N | `请输入 y 或 n` |
| 文件存在性 | 文件存在 | `文件不存在` |

#### 中断处理

1. **Ctrl+C 捕获**
   - 显示确认提示：`确认退出？未保存的修改将丢失 (y/N)`
   - 用户确认后退出，否则继续问答

2. **EOF (Ctrl+D) 处理**
   - 使用当前输入的默认值
   - 继续下一个问题

#### 错误处理

| 错误场景 | 退出码 | 输出 |
|----------|--------|------|
| 输出路径不可写 | 1 | `错误: 无法写入配置文件` |
| 用户中断（确认退出） | 0 | `配置已取消` |
| 验证失败 | 0 | 重新询问当前问题 |

### 输出格式

#### 问答输出

```
=== Git Webhooks Server 配置初始化 ===

服务器监听地址 [默认: 0.0.0.0]:
服务器端口 [默认: 6789]:
日志文件路径 [默认: ~/.gitwebhook.log]:

是否启用 SSL? (y/N) [默认: N]:

配置 GitHub webhook:
  启用签名验证? (Y/n) [默认: Y]:
  Webhook secret (留空跳过):


配置 Gitee webhook:
  是否配置 Gitee? (Y/n) [默认: Y]:
  ...

配置文件已创建: ~/.gitwebhook.ini
权限已设置: 0600 (仅用户可读写)
```

#### 成功输出

```
配置文件已创建: ~/.gitwebhook.ini

下一步:
  1. 编辑配置文件，添加仓库配置
  2. 运行服务: gitwebhooks-cli
  3. 或安装为服务: sudo gitwebhooks-cli service install
```

#### 文件已存在输出

```
配置文件已存在: ~/.gitwebhook.ini
是否覆盖? (y/N):
```

### 帮助信息

```
Usage: gitwebhooks-cli config init [--output PATH]

Initialize a new configuration file interactively.

Options:
  --output PATH  Output configuration file path
                 (default: ~/.gitwebhook.ini)

Examples:
  gitwebhooks-cli config init
  gitwebhooks-cli config init --output /etc/webhooks.ini
```

---

## config --help 命令

### 输出格式

```
Usage: gitwebhooks-cli config <command>

Manage gitwebhooks configuration.

Commands:
  init    Initialize a new configuration file

Options:
  -h, --help  Show this help message

Examples:
  gitwebhooks-cli config init
  gitwebhooks-cli config init --output /path/to/config.ini
```
