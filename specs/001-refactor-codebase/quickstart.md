# Quick Start Guide

**Feature**: 代码库重构 - 模块化拆分与项目结构重组
**Target Audience**: 开发者和贡献者
**Last Updated**: 2025-01-13

---

## 项目结构概览

```
gitwebhooks/
├── __init__.py          # 包初始化
├── cli.py               # 命令行入口
├── server.py            # HTTP 服务器
├── config/              # 配置管理
│   ├── __init__.py
│   ├── loader.py        # 配置加载器
│   ├── models.py        # 配置数据类
│   ├── server.py        # 服务器配置
│   └── registry.py      # 配置注册表
├── handlers/            # Webhook 处理器
│   ├── __init__.py
│   ├── base.py          # 处理器基类
│   ├── github.py        # Github 处理器
│   ├── gitee.py         # Gitee 处理器
│   ├── gitlab.py        # Gitlab 处理器
│   ├── custom.py        # 自定义处理器
│   ├── request.py       # HTTP 请求处理器
│   └── factory.py       # 处理器工厂
├── auth/                # 签名验证
│   ├── __init__.py
│   ├── verifier.py      # 验证器基类
│   ├── github.py        # Github HMAC-SHA1
│   ├── gitee.py         # Gitee HMAC-SHA256
│   ├── gitlab.py        # Gitlab Token
│   ├── custom.py        # 自定义 Token
│   └── factory.py       # 验证器工厂
├── models/              # 数据模型
│   ├── __init__.py
│   ├── provider.py      # Provider 枚举
│   ├── request.py       # WebhookRequest
│   └── result.py        # SignatureVerificationResult
├── utils/               # 工具模块
│   ├── __init__.py
│   ├── constants.py     # 常量定义
│   ├── exceptions.py    # 异常类
│   └── executor.py      # 命令执行器
└── logging/             # 日志配置
    ├── __init__.py
    └── setup.py         # 日志设置
```

---

## 快速开始

### 1. 运行服务器

```bash
# 使用默认配置
gitwebhooks-cli

# 指定配置文件
gitwebhooks-cli -c /path/to/config.ini

# 查看帮助
gitwebhooks-cli --help
```

### 2. 作为模块运行

```bash
python3 -m gitwebhooks.cli -c config.ini
```

### 3. 测试 Webhook

```bash
# Github webhook 测试
curl -X POST http://localhost:6789 \
  -H "Content-Type: application/json" \
  -H "X-GitHub-Event: push" \
  -H "X-Hub-Signature: sha1=..." \
  -d '{"repository":{"full_name":"owner/repo"}}'
```

---

## 开发指南

### 环境设置

```bash
# 克隆仓库
git clone https://github.com/yourusername/git-webhooks-server.git
cd git-webhooks-server

# 创建虚拟环境（可选）
python3 -m venv venv
source venv/bin/activate

# 无需安装依赖（仅使用标准库）
```

### 代码风格

项目遵循 `.editorconfig` 配置：

- **缩进**: 4 空格
- **编码**: UTF-8
- **换行**: LF
- **行尾**: 空行保留（Markdown）

### 导入约定

```python
# 标准库
import sys
from pathlib import Path
from typing import Dict, Optional

# 项目模块（绝对导入）
from gitwebhooks.models.provider import Provider
from gitwebhooks.config.loader import ConfigLoader
from gitwebhooks.handlers.base import WebhookHandler
```

### 添加新的 Git 平台

1. **创建处理器** (`gitwebhooks/handlers/newplatform.py`):

```python
from gitwebhooks.handlers.base import WebhookHandler
from gitwebhooks.models.provider import Provider

class NewPlatformHandler(WebhookHandler):
    def get_provider(self) -> Provider:
        return Provider.NEWPLATFORM

    # 实现其他抽象方法...
```

2. **创建验证器** (`gitwebhooks/auth/newplatform.py`):

```python
from gitwebhooks.auth.verifier import SignatureVerifier

class NewPlatformVerifier(SignatureVerifier):
    def verify(self, payload, signature, secret, **kwargs):
        # 实现验证逻辑
        pass
```

3. **更新枚举** (`gitwebhooks/models/provider.py`):

```python
@unique
class Provider(Enum):
    # ... 现有值
    NEWPLATFORM = 'newplatform'
```

4. **注册到工厂**:

```python
# handlers/factory.py
from gitwebhooks.handlers.newplatform import NewPlatformHandler

# auth/factory.py
from gitwebhooks.auth.newplatform import NewPlatformVerifier
```

5. **添加配置节**:

```ini
[newplatform]
verify = true
secret = your_secret
handle_events = push,release
```

---

## 架构概念

### 依赖注入模式

```python
# 创建配置
loader = ConfigLoader('/path/to/config.ini')
registry = ConfigurationRegistry(loader)

# 注入到服务器
server = WebhookServer(
    config_path='/path/to/config.ini',
    registry=registry
)
```

### 处理器选择流程

```
HTTP Request
    ↓
提取 Headers
    ↓
HandlerFactory.from_headers()
    ↓
检查 X-GitHub-Event → GithubHandler
检查 X-Gitee-Event → GiteeHandler
检查 X-Gitlab-Event → GitlabHandler
检查自定义 header → CustomHandler
    ↓
返回 Handler 实例
```

### 请求处理流程

```
do_POST()
    ↓
_parse_request() → WebhookRequest
    ↓
_identify_provider() → Provider
    ↓
HandlerFactory.from_handler_type() → Handler
    ↓
Handler.handle_request()
    ├─ is_event_allowed() → bool
    ├─ verify_signature() → SignatureVerificationResult
    └─ extract_repository() → repo_name
    ↓
RepositoryConfig.for_name(repo_name)
    ↓
_execute_deployment()
```

---

## 调试技巧

### 启用详细日志

```ini
[server]
log_file = /var/log/git-webhooks-server.log
```

### 运行测试

```bash
# 运行所有测试
python3 -m unittest discover tests/

# 运行特定模块测试
python3 -m unittest tests.test_handlers.test_github

# 详细输出
python3 -m unittest tests.test_handlers.test_github -v
```

### 手动测试签名验证

```python
from gitwebhooks.auth.github import GithubSignatureVerifier

verifier = GithubSignatureVerifier()
payload = b'{"test": "data"}'
secret = 'my_secret'

# 生成签名
import hmac, hashlib, base64
signature = 'sha1=' + hmac.new(secret.encode(), payload, hashlib.sha1).hexdigest()

# 验证
result = verifier.verify(payload, signature, secret)
print(f'Valid: {result.is_valid}')
```

---

## 常见问题

### Q: 如何添加新的配置选项？

A: 编辑相应的 `models.py` 数据类，更新 `from_config_parser()` 方法：

```python
@dataclass
class ProviderConfig:
    # ... 现有字段
    new_option: str = ''  # 新字段

    @classmethod
    def from_config_parser(cls, parser, provider):
        # ... 现有代码
        config.new_option = parser.get(section, 'new_option', fallback='')
        return config
```

### Q: 如何处理不同平台的事件格式？

A: 在处理器中实现平台特定的解析：

```python
def extract_repository(self, request, config):
    # 平台特定的 JSON 路径
    if self.provider == Provider.GITHUB:
        return request.post_data.get('repository', {}).get('full_name')
    elif self.provider == Provider.GITLAB:
        return request.post_data.get('project', {}).get('path_with_namespace')
```

### Q: 如何测试本地更改？

A: 使用 `-c` 参数指向本地配置：

```bash
# 创建测试配置
cat > test-config.ini << EOF
[server]
address = 127.0.0.1
port = 6789
log_file =

[github]
verify = false
secret =

[test/repo]
cwd = $(pwd)
cmd = echo "Deploy triggered"
EOF

# 运行服务器
python3 -m gitwebhooks.cli -c test-config.ini
```

---

## 性能优化

### 当前瓶颈

1. **单线程处理**: HTTPServer 默认使用 `ThreadingMixIn`
2. **命令执行**: 使用 `subprocess.Popen` 异步执行

### 优化建议

1. **使用进程池**: 处理大量并发请求
2. **缓存配置**: 避免重复解析配置文件
3. **日志缓冲**: 减少磁盘 I/O

---

## 安全最佳实践

1. **文件权限**:
   ```bash
   chmod 600 /usr/local/etc/git-webhooks-server.ini
   ```

2. **SSL/TLS**: 始终在生产环境启用
   ```ini
   [ssl]
   enable = true
   key_file = /path/to/server.key
   cert_file = /path/to/server.crt
   ```

3. **Secret 管理**:
   - 不要在代码中硬编码
   - 使用强密码
   - 定期轮换密钥

---

## 贡献指南

### 提交代码

1. 遵循代码风格规范
2. 添加单元测试
3. 更新相关文档
4. 提交 PR 到 GitHub

### 提交信息格式

```
类型: 简短描述

详细说明（可选）

类型可以是：
- feat: 新功能
- fix: 修复
- docs: 文档
- refactor: 重构
- test: 测试
- chore: 构建/工具
```

### 测试要求

所有新功能必须包含：
- 单元测试
- 集成测试（如适用）
- 文档更新

---

## 相关资源

- **主文档**: [README.md](../../README.md)
- **配置示例**: [git-webhooks-server.ini.sample](../../git-webhooks-server.ini.sample)
- **服务配置**: [git-webhooks-server.service.sample](../../git-webhooks-server.service.sample)
- **安装脚本**: [install.sh](../../install.sh)
- **宪法**: [.specify/memory/constitution.md](../../.specify/memory/constitution.md)

---

## 下一步

- 阅读 [data-model.md](data-model.md) 了解数据模型
- 阅读 [contracts/](contracts/) 目录了解模块接口
- 查看 [research.md](research.md) 了解技术决策
