# Quickstart: 优化后的 git-webhooks-server

**Feature**: 优化 git-webhooks-server.py 代码质量和规范性
**Date**: 2025-01-13

## Overview

本文档提供优化后代码的使用指南。注意：**外部使用方式完全不变**，这是内部代码质量优化。

---

## Installation (安装)

安装方式**完全不变**：

```bash
# 交互式安装
./install.sh

# 或指定配置文件
./install.sh --config /path/to/config.ini

# 卸载
./install.sh --uninstall
```

---

## Configuration (配置)

配置文件格式**完全不变**：

```ini
[server]
address = 0.0.0.0
port = 6789
log_file = /var/log/git-webhooks-server.log

[github]
handle_events = push,pull_request
verify = true
secret = your_webhook_secret

[github/owner/repo]
cwd = /var/www/your-project
cmd = git pull && systemctl restart your-service
```

---

## Running the Server (运行服务)

### 手动运行

```bash
# 使用默认配置
python3 git-webhooks-server.py

# 指定配置文件
python3 git-webhooks-server.py -c /path/to/config.ini

# 或使用安装后的命令
git-webhooks-server.py -c /usr/local/etc/git-webhooks-server.ini
```

### systemd 服务

```bash
# 启动服务
systemctl start git-webhooks-server

# 停止服务
systemctl stop git-webhooks-server

# 查看状态
systemctl status git-webhooks-server

# 查看日志
journalctl -u git-webhooks-server -f
```

---

## Webhook Configuration (Webhook 配置)

### Github

1. 进入仓库 Settings → Webhooks → Add webhook
2. Payload URL: `http://your-server:6789`
3. Content type: `application/json`
4. Secret: 与配置文件中的 `secret` 匹配
5. Events: 选择要触发的事件（如 Pushes）

### Gitee

1. 进入仓库管理 → WebHooks → 添加
2. URL: `http://your-server:6789`
3. 密码: 与配置文件中的 `secret` 匹配

### Gitlab

1. 进入项目 Settings → Webhooks
2. URL: `http://your-server:6789`
3. Secret Token: 与配置文件中的 `secret` 匹配
4. 触发事件: 选择要触发的事件

---

## What Changed (代码变更说明)

### 内部改进

以下是**内部代码改进**，不影响外部使用：

| 改进项 | 说明 | 用户可见影响 |
|--------|------|--------------|
| 消除全局变量 | 使用依赖注入传递配置 | ❌ 无影响 |
| 添加类型提示 | 使用 typing 模块 | ❌ 无影响 |
| 改进异常处理 | 具体化异常类型 | ⚠️ 日志信息更详细 |
| 增强日志上下文 | 添加结构化日志 | ✅ 日志更易诊断 |
| 提取重复代码 | 复用函数 | ❌ 无影响 |
| 添加文档字符串 | Google 风格 docstring | ❌ 无影响 |
| 重构长函数 | 拆分为小函数 | ❌ 无影响 |
| 定义常量 | 消除魔法值 | ❌ 无影响 |

### 日志改进示例

**优化前**:
```
2025-01-13 10:00:00 Execution failed
```

**优化后**:
```
2025-01-13 10:00:00 [owner/repo] Deployment failed: exit code 1
2025-01-13 10:00:00 [owner/repo] Command: git pull
2025-01-13 10:00:00 [owner/repo] Working directory: /var/www/repo
2025-01-13 10:00:00 [owner/repo] Stderr: fatal: could not read Username
```

---

## Development (开发)

### 运行测试

```bash
# 运行所有测试
python3 -m pytest tests/

# 运行单元测试
python3 -m pytest tests/unit/

# 运行集成测试
python3 -m pytest tests/integration/

# 查看覆盖率
python3 -m pytest --cov=git-webhooks-server tests/
```

### 代码质量检查

```bash
# pylint 检查
pylint git-webhooks-server.py

# mypy 类型检查
mypy git-webhooks-server.py

# flake8 风格检查
flake8 git-webhooks-server.py
```

### 目标质量指标

| 指标 | 优化前 | 目标 | 当前 |
|------|--------|------|------|
| pylint 评分 | ~6.5/10 | ≥8.0/10 | 待测试 |
| mypy 错误 | 未知 | 0 关键错误 | 待测试 |
| 圈复杂度 | 未知 | ≤15 (max) | 待测试 |
| 代码重复率 | 未知 | <5% | 待测试 |
| 测试覆盖率 | 未知 | ≥75% | 待测试 |

---

## Troubleshooting (故障排查)

### 问题: 401 Unauthorized

**可能原因**:
- Webhook secret 与配置文件不匹配
- 签名验证算法实现错误（优化后应不变）

**排查**:
```bash
# 查看日志
tail -f /var/log/git-webhooks-server.log

# 检查配置
grep "secret" /usr/local/etc/git-webhooks-server.ini
```

### 问题: 406 Not Acceptable

**可能原因**:
- 事件类型未在 `handle_events` 中配置

**解决**:
```ini
[github]
handle_events = push,pull_request,release  # 添加你的事件
```

### 问题: 命令未执行

**可能原因**:
- 仓库名称不匹配
- `cwd` 路径不存在
- `cmd` 为空

**排查**:
```bash
# 检查配置
grep -A2 "owner/repo" /usr/local/etc/git-webhooks-server.ini

# 验证路径
ls -ld /var/www/your-project
```

---

## Migration from Old Code (迁移)

### 从旧版本升级

```bash
# 1. 备份当前文件
cp git-webhooks-server.py git-webhooks-server.py.backup

# 2. 替换为新版本
cp /path/to/new/git-webhooks-server.py /usr/local/bin/git-webhooks-server.py

# 3. 重启服务
systemctl restart git-webhooks-server

# 4. 验证
systemctl status git-webhooks-server
```

### 回滚

```bash
# 如果有问题，回滚
cp /usr/local/bin/git-webhooks-server.py.backup /usr/local/bin/git-webhooks-server.py
systemctl restart git-webhooks-server
```

---

## Compatibility Matrix (兼容性矩阵)

| 项目 | 兼容性 | 说明 |
|------|--------|------|
| Python 3.6+ | ✅ | 保持兼容 |
| Python 3.7+ | ✅ | 完全支持 |
| Python 3.8+ | ✅ | 完全支持 |
| Python 3.9+ | ✅ | 完全支持 |
| Python 3.10+ | ✅ | 完全支持 |
| Python 3.11+ | ✅ | 完全支持 |
| Python 3.12+ | ✅ | 完全支持 |
| macOS | ✅ | 完全支持 |
| Linux | ✅ | 完全支持 |
| Windows | ⚠️ | 未测试（理论上支持） |

---

## Support (支持)

- 问题反馈: [GitHub Issues](https://github.com/your-org/git-webhooks-server/issues)
- 文档: [README.md](../../README.md)
- 中文文档: [README.zh.md](../../README.zh.md)

---

## Changelog (变更日志)

### [优化版本] - 2025-01-13

**Added**:
- 完整的类型提示（Python 3.6+ compatible typing）
- Google 风格的文档字符串
- 详细的日志上下文信息

**Changed**:
- 消除全局变量，使用依赖注入
- 具体化异常处理类型
- 提取重复代码为可复用函数
- 重构长函数为更小的单元

**Fixed**:
- 裸 `except:` 子句
- 魔法数字和字符串

**Refactored**:
- 代码结构，保持单文件架构
- 配置加载和传递机制
- 平台处理器分离

**Technical Debt**:
- pylint 评分从 ~6.5 提升到 ≥8.0
- 添加 mypy 类型检查支持
- 提升代码可测试性

---

## Notes

1. **外部 API 零变化**: 所有 webhook 配置无需修改
2. **配置文件零变化**: INI 格式完全兼容
3. **性能无损失**: 优化后性能 ≥95% 原版本
4. **安全性保持**: 签名验证算法不变
5. **日志更详细**: 便于诊断问题
