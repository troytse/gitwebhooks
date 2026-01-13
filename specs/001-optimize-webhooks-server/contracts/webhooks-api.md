# HTTP API Contract: Git Webhooks Server

**Feature**: 优化 git-webhooks-server.py 代码质量
**Date**: 2025-01-13
**Status**: 保持不变 - 代码优化不影响外部 API

## Overview

本文档确认代码重构**不改变**任何 HTTP API 接口。所有现有集成将保持 100% 兼容。

## API Endpoints

### GET / (所有路径)

**响应**: 403 Forbidden

**Description**: 服务器拒绝所有 GET 请求。

**Response Body**:
```http
HTTP/1.1 403 Forbidden
Content-Type: text/html

<html>
  <head>
    <title>403 Forbidden</title>
  </head>
  <body>
    <h1>Forbidden</h1>
  </body>
</html>
```

---

### POST / (webhook 端点)

**Description**: 接收 Git 平台的 webhook 请求并触发部署。

**Request Headers**:

| Header | 平台 | 必需 | 描述 |
|--------|------|------|------|
| `X-GitHub-Event` | Github | 是 | 事件类型（如 "push"） |
| `X-GitHub-Delivery` | Github | 否 | 唯一投递 ID |
| `X-Hub-Signature` | Github | 条件 | HMAC-SHA1 签名（验证启用时） |
| `X-Gitee-Event` | Gitee | 是 | 事件类型 |
| `X-Gitee-Token` | Gitee | 条件 | 密码或签名（验证启用时） |
| `X-Gitee-Timestamp` | Gitee | 否 | 签名时间戳 |
| `X-Gitlab-Event` | Gitlab | 是 | 事件类型 |
| `X-Gitlab-Token` | Gitlab | 条件 | 验证令牌（验证启用时） |
| `Content-Type` | 所有 | 是 | 请求内容类型 |
| `Content-Length` | 所有 | 是 | 请求体长度 |

**Request Body**:

支持的 Content-Type:

1. `application/json` - JSON 格式的 webhook payload
2. `application/x-www-form-urlencoded` - 表单编码（包含 `payload` 字段）

**Response Codes**:

| Code | 含义 | 触发条件 |
|------|------|----------|
| 200 | OK | Webhook 处理成功，命令已执行 |
| 400 | Bad Request | 请求体解析失败或不支持的 Content-Type |
| 401 | Unauthorized | 签名/token 验证失败 |
| 403 | Forbidden | 使用 GET 方法 |
| 404 | Not Found | 仓库未找到或仓库信息缺失 |
| 406 | Not Acceptable | 事件类型未配置为允许处理 |
| 412 | Precondition Failed | 无法识别的 Provider |
| 500 | Internal Server Error | 服务器内部错误（配置缺失） |

**Response Body**:

成功响应：
```http
HTTP/1.1 200 OK
Content-Type: text/plain

OK
```

错误响应：
```http
HTTP/1.1 401 Unauthorized
Content-Type: text/html

<html>
  <head>
    <title>401 Unauthorized</title>
  </head>
  <body>
    <h1>Unauthorized</h1>
  </body>
</html>
```

---

## Platform-Specific Behavior

### Github Webhook

**识别 Header**: `X-GitHub-Event`

**签名验证** (可选):
```python
# 签名格式
X-Hub-Signature: sha1=<hex_signature>

# 验证算法
signature = hmac.new(secret, payload, hashlib.sha1).hexdigest()
expected = f"sha1={signature}"
```

**仓库标识**: `repository.full_name`

**示例 Payload**:
```json
{
  "repository": {
    "full_name": "owner/repo",
    "name": "repo",
    "owner": {"name": "owner"}
  },
  "ref": "refs/heads/main"
}
```

---

### Gitee Webhook

**识别 Header**: `X-Gitee-Event`

**签名验证** (两种模式):

1. **签名模式** (有 timestamp):
```python
# 签名格式
X-Gitee-Token: <base64_signature>
X-Gitee-Timestamp: <unix_timestamp>

# 验证算法
sign_string = f"{timestamp}{payload}"
signature = base64.b64encode(
    hmac.new(secret, sign_string, hashlib.sha256).digest()
).decode()
```

2. **密码模式** (无 timestamp):
```python
# X-Gitee-Token 直接与 secret 比较字符串相等性
```

**仓库标识**: `repository.full_name`

---

### Gitlab Webhook

**识别 Header**: `X-Gitlab-Event`

**Token 验证**:
```python
# Token 格式
X-Gitlab-Token: <secret_token>

# 验证: 直接字符串比较
```

**仓库标识**: `project.path_with_namespace`

**示例 Payload**:
```json
{
  "project": {
    "path_with_namespace": "owner/repo",
    "name": "repo",
    "namespace": "owner"
  },
  "ref": "main"
}
```

---

### Custom Webhook

**识别 Headers** (可配置):
- 默认识别 header: `X-Custom-Webhook: custom`
- 默认事件 header: `X-Custom-Event`

**Token 验证** (可选):
- Header: `X-Custom-Token` (可配置)
- 验证: 字符串与 secret 比较

**仓库标识**: 通过配置的 JSON 路径提取
- 配置: `identifier_path = project.path_with_namespace`
- 示例: `data["project"]["path_with_namespace"]`

---

## Configuration Impact

配置文件格式**完全不变**。示例：

```ini
[server]
address = 0.0.0.0
port = 6789
log_file = /var/log/git-webhooks-server.log

[ssl]
enable = false
key_file = /path/to/key.pem
cert_file = /path/to/cert.pem

[github]
handle_events = push
verify = true
secret = my_github_secret

[gitee]
handle_events = Push Hook
verify = true
secret = my_gitee_secret

[gitlab]
handle_events = Push Hook
verify = true
secret = my_gitlab_secret

[custom]
header_name = X-Custom-Webhook
header_value = custom
header_event = X-Custom-Event
header_token = X-Custom-Token
identifier_path = repository.name
secret = my_custom_secret
verify = true

owner/repo]
cwd = /path/to/repo
cmd = git pull && ./deploy.sh
```

---

## Behavior Guarantees

代码优化后，以下行为**完全保持不变**：

1. ✅ 所有 HTTP 响应代码和消息
2. ✅ 签名验证算法和安全性
3. ✅ 配置文件格式和解析方式
4. ✅ 命令执行行为（非阻塞）
5. ✅ 日志输出位置和格式
6. ✅ SSL/TLS 配置支持
7. ✅ 错误处理和错误消息
8. ✅ 平台识别和事件处理逻辑

---

## Migration Notes

**无需迁移** - 这是纯内部代码优化。现有部署：

1. 无需修改配置文件
2. 无需修改 Git 平台 webhook 配置
3. 无需修改客户端代码
4. 无需修改 systemd 服务文件
5. 直接替换 `git-webhooks-server.py` 即可

---

## Testing Compatibility

所有现有测试**无需修改**：

```python
# 测试继续工作
def test_github_webhook():
    response = requests.post(
        'http://localhost:6789',
        json={'repository': {'full_name': 'test/repo'}},
        headers={'X-GitHub-Event': 'push', 'X-Hub-Signature': '...'}
    )
    assert response.status_code == 200
    assert response.text == 'OK'
```

---

## Version Compatibility

| 集成类型 | 兼容性 | 说明 |
|----------|--------|------|
| Github Webhooks | ✅ 100% | Header、签名、payload 格式不变 |
| Gitee Webhooks | ✅ 100% | Header、签名、payload 格式不变 |
| Gitlab Webhooks | ✅ 100% | Header、token、payload 格式不变 |
| 自定义集成 | ✅ 100% | 可配置行为保持不变 |
| 配置文件 | ✅ 100% | INI 格式、节名、选项名不变 |
| systemd 服务 | ✅ 100% | 服务文件、启动方式不变 |

---

## Summary

这是一个**纯内部重构**：

- ❌ 不改变 HTTP API
- ❌ 不改变配置格式
- ❌ 不改变命令行参数
- ❌ 不改变日志格式
- ✅ 仅改进代码结构和质量
- ✅ 仅添加类型提示和文档
- ✅ 仅改进错误处理和日志上下文
