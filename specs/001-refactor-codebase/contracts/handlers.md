# Handler Module Contract

**Module**: `gitwebhooks.handlers`
**Version**: 1.0.0
**Status**: Design Phase

## Overview

Webhook 处理器模块负责处理来自不同 Git 平台的 webhook 请求。每个处理器实现统一的接口，提供平台特定的签名验证和仓库标识符提取逻辑。

---

## Base Handler Interface

**Class**: `WebhookHandler`
**Module**: `gitwebhooks.handlers.base`
**Type**: Abstract Base Class (ABC)

```python
from abc import ABC, abstractmethod
from typing import Optional

from gitwebhooks.models.provider import Provider
from gitwebhooks.models.request import WebhookRequest
from gitwebhooks.models.result import SignatureVerificationResult
from gitwebhooks.config.models import ProviderConfig

class WebhookHandler(ABC):
    """Webhook 处理器基类

    所有平台特定的处理器必须继承此类并实现所有抽象方法。
    """

    @abstractmethod
    def get_provider(self) -> Provider:
        """返回此处理器支持的提供者类型

        Returns:
            Provider 枚举值
        """
        pass

    @abstractmethod
    def verify_signature(self, request: WebhookRequest,
                        config: ProviderConfig) -> SignatureVerificationResult:
        """验证 webhook 签名

        Args:
            request: Webhook 请求数据
            config: 提供者配置（包含 secret）

        Returns:
            签名验证结果

        Raises:
            SignatureValidationError: 验证失败时
        """
        pass

    @abstractmethod
    def extract_repository(self, request: WebhookRequest,
                          config: ProviderConfig) -> Optional[str]:
        """从请求中提取仓库标识符

        Args:
            request: Webhook 请求数据
            config: 提供者配置（可能包含 identifier_path）

        Returns:
            仓库标识符（如 'owner/repo'），未找到返回 None
        """
        pass

    @abstractmethod
    def is_event_allowed(self, event: Optional[str],
                        config: ProviderConfig) -> bool:
        """检查事件类型是否被允许处理

        Args:
            event: 事件类型（如 'push', 'merge_request'）
            config: 提供者配置（包含 handle_events 列表）

        Returns:
            True 如果事件被允许，False 否则
        """
        pass

    def handle_request(self, request: WebhookRequest,
                      config: ProviderConfig) -> Optional[str]:
        """处理完整的 webhook 请求

        这是模板方法，定义了请求处理的固定流程：
        1. 检查事件是否被允许
        2. 验证签名
        3. 提取仓库标识符

        Args:
            request: Webhook 请求数据
            config: 提供者配置

        Returns:
            仓库标识符，如果处理失败返回 None

        Raises:
            SignatureValidationError: 签名验证失败
            UnsupportedEventError: 事件类型不被允许
        """
        # 步骤 1: 检查事件
        if not self.is_event_allowed(request.event, config):
            raise UnsupportedEventError(f'Event not configured: {request.event}')

        # 步骤 2: 验证签名（如果需要）
        if config.verify:
            result = self.verify_signature(request, config)
            if not result.is_valid:
                raise SignatureValidationError(result.error_message or 'Verification failed')

        # 步骤 3: 提取仓库标识符
        return self.extract_repository(request, config)
```

---

## GitHub Handler Contract

**Class**: `GithubHandler`
**Module**: `gitwebhooks.handlers.github`
**Extends**: `WebhookHandler`

### Platform Specifics

**Header Identification**:
- Event Header: `X-GitHub-Event`
- Signature Header: `X-Hub-Signature`

**Signature Algorithm**:
- Method: HMAC-SHA1
- Format: `sha1=<hex_digest>`
- Calculation: `hmac.new(secret_bytes, payload, hashlib.sha1).hexdigest()`

**Repository Extraction**:
- JSON Path: `repository.full_name`
- Format: `owner/repo`

### Implementation Contract

```python
class GithubHandler(WebhookHandler):
    """Github webhook 处理器"""

    def get_provider(self) -> Provider:
        """返回 Provider.GITHUB"""
        return Provider.GITHUB

    def verify_signature(self, request: WebhookRequest,
                        config: ProviderConfig) -> SignatureVerificationResult:
        """验证 Github HMAC-SHA1 签名

        Implementation:
        1. 从 headers 获取 X-Hub-Signature
        2. 如果缺失，返回 failure('Missing signature')
        3. 如果 secret 为空，返回 failure('Secret not configured')
        4. 计算 expected_signature = 'sha1=' + hmac.new(secret, payload, sha1).hexdigest()
        5. 比较 request_signature 与 expected_signature
        6. 返回结果
        """
        pass

    def extract_repository(self, request: WebhookRequest,
                          config: ProviderConfig) -> Optional[str]:
        """从请求中提取 Github 仓库全名

        Implementation:
        1. 从 post_data 获取 repository 字典
        2. 返回 repository['full_name']
        3. 如果不存在或类型错误，返回 None
        """
        pass

    def is_event_allowed(self, event: Optional[str],
                        config: ProviderConfig) -> bool:
        """检查事件是否在 config.handle_events 列表中

        Implementation:
        - 调用 config.allows_event(event)
        """
        pass
```

### Test Cases

| Scenario | Input | Expected Output |
|----------|-------|-----------------|
| Valid signature | Valid X-Hub-Signature | success() |
| Missing signature | No X-Hub-Signature header | failure('Missing signature') |
| Invalid signature | Wrong X-Hub-Signature | failure('Invalid signature') |
| Valid repo | `{repository: {full_name: "owner/repo"}}` | "owner/repo" |
| Missing repo | `{repository: {}}` | None |
| Event allowed | handle_events=['push'], event='push' | True |
| Event not allowed | handle_events=['push'], event='release' | False |

---

## Gitee Handler Contract

**Class**: `GiteeHandler`
**Module**: `gitwebhooks.handlers.gitee`
**Extends**: `WebhookHandler`

### Platform Specifics

**Header Identification**:
- Event Header: `X-Gitee-Event`
- Token Header: `X-Gitee-Token`
- Timestamp Header: `X-Gitee-Timestamp` (optional, for signature mode)

**Signature Algorithm** (Two modes):

1. **Signature Mode** (with timestamp):
   - Method: HMAC-SHA256
   - Format: Base64 encoded
   - Calculation: `timestamp + payload`, then HMAC-SHA256, then Base64

2. **Password Mode** (without timestamp):
   - Method: Simple string comparison
   - Format: Plain text token

**Repository Extraction**:
- JSON Path: `repository.full_name`
- Format: `owner/repo`

### Implementation Contract

```python
class GiteeHandler(WebhookHandler):
    """Gitee webhook 处理器"""

    def verify_signature(self, request: WebhookRequest,
                        config: ProviderConfig) -> SignatureVerificationResult:
        """验证 Gitee 签名或密码

        Implementation:
        1. 从 headers 获取 X-Gitee-Token 和 X-Gitee-Timestamp
        2. 如果 token 缺失，返回 failure('Missing signature or password')
        3. 如果 timestamp 存在（签名模式）:
           a. 计算 sign_string = timestamp + payload.decode()
           b. signature = base64.b64encode(hmac.new(secret, sign_string, sha256).digest())
           c. 比较与 request token
        4. 如果 timestamp 不存在（密码模式）:
           a. 直接比较 token 与 secret
        5. 返回结果
        """
        pass

    # 其他方法类似 Github
```

### Test Cases

| Scenario | Input | Expected Output |
|----------|-------|-----------------|
| Valid signature (with timestamp) | Valid token + timestamp | success() |
| Valid password (no timestamp) | Matching token | success() |
| Invalid password | Wrong token | failure('Invalid password') |
| Valid repo | `{repository: {full_name: "owner/repo"}}` | "owner/repo" |

---

## GitLab Handler Contract

**Class**: `GitlabHandler`
**Module**: `gitwebhooks.handlers.gitlab`
**Extends**: `WebhookHandler`

### Platform Specifics

**Header Identification**:
- Event Header: `X-Gitlab-Event`
- Token Header: `X-Gitlab-Token`

**Signature Algorithm**:
- Method: Simple token comparison
- No HMAC calculation

**Repository Extraction**:
- JSON Path: `project.path_with_namespace`
- Format: `group/project` or `group/subgroup/project`

### Implementation Contract

```python
class GitlabHandler(WebhookHandler):
    """Gitlab webhook 处理器"""

    def verify_signature(self, request: WebhookRequest,
                        config: ProviderConfig) -> SignatureVerificationResult:
        """验证 Gitlab token

        Implementation:
        1. 从 headers 获取 X-Gitlab-Token
        2. 直接比较与 config.secret
        3. 返回 success() 或 failure('Invalid token')
        """
        pass

    def extract_repository(self, request: WebhookRequest,
                          config: ProviderConfig) -> Optional[str]:
        """从请求中提取 Gitlab 项目路径

        Implementation:
        1. 从 post_data 获取 project 字典
        2. 返回 project['path_with_namespace']
        3. 如果不存在或类型错误，返回 None
        """
        pass
```

### Test Cases

| Scenario | Input | Expected Output |
|----------|-------|-----------------|
| Valid token | Matching X-Gitlab-Token | success() |
| Invalid token | Wrong token | failure('Invalid token') |
| Valid project | `{project: {path_with_namespace: "group/project"}}` | "group/project" |
| Nested project | `{project: {path_with_namespace: "group/sub/project"}}` | "group/sub/project" |

---

## Custom Handler Contract

**Class**: `CustomHandler`
**Module**: `gitwebhooks.handlers.custom`
**Extends**: `WebhookHandler`

### Platform Specifics

**Header Identification**:
- Configurable via `ProviderConfig`:
  - `header_name`: Identification header name (default: `X-Custom-Webhook`)
  - `header_value`: Expected header value (default: `custom`)
  - `header_event`: Event header name (default: `X-Custom-Event`)
  - `header_token`: Token header name (default: `X-Custom-Token`)

**Signature Algorithm**:
- Method: Simple token comparison
- Token header name configurable

**Repository Extraction**:
- JSON Path: Configurable via `identifier_path`
- Format: Dot-notation path (e.g., `project.repo.id`)

### Implementation Contract

```python
class CustomHandler(WebhookHandler):
    """自定义 webhook 处理器"""

    def verify_signature(self, request: WebhookRequest,
                        config: ProviderConfig) -> SignatureVerificationResult:
        """验证自定义 token

        Implementation:
        1. 如果 config.header_token 为空，返回 success()（不验证）
        2. 从 headers 获取 config.header_token 的值
        3. 比较与 config.secret
        4. 返回结果
        """
        pass

    def extract_repository(self, request: WebhookRequest,
                          config: ProviderConfig) -> Optional[str]:
        """使用 JSON 路径提取仓库标识符

        Implementation:
        1. 如果 config.identifier_path 为空，返回 None
        2. 按 '.' 分割 identifier_path
        3. 逐层遍历 post_data 字典
        4. 返回最终值（必须是字符串）
        5. 如果路径不存在或值不是字符串，返回 None
        """
        pass

    def is_event_allowed(self, event: Optional[str],
                        config: ProviderConfig) -> bool:
        """检查事件是否被允许

        Implementation:
        - 如果 config.header_event 为空，允许所有事件
        - 否则从 headers 获取 config.header_event 的值
        - 调用 config.allows_event(event)
        """
        pass
```

### Test Cases

| Scenario | Input | Expected Output |
|----------|-------|-----------------|
| Token verification enabled | header_token='X-Token', matching token | success() |
| Token verification disabled | header_token='' | success() |
| Valid path extraction | identifier_path='a.b.c', {a:{b:{c:'value'}}} | 'value' |
| Invalid path | identifier_path='x.y.z', {a:{b:{c:'value'}}} | None |
| Non-string value | identifier_path='a.b', {a:{b:123}} | None |

---

## Handler Factory

**Class**: `HandlerFactory`
**Module**: `gitwebhooks.handlers`
**Type**: Factory class

```python
class HandlerFactory:
    """处理器工厂类

    根据请求 headers 创建对应的处理器实例
    """

    @staticmethod
    def from_headers(headers: Dict[str, str],
                    configs: Dict[Provider, ProviderConfig]) -> WebhookHandler:
        """根据请求 headers 创建处理器

        Args:
            headers: HTTP 请求头字典
            configs: 提供者配置字典

        Returns:
            对应的 WebhookHandler 实例

        Raises:
            UnsupportedProviderError: 无法识别的平台

        Implementation:
        1. 检查 X-GitHub-Event → return GithubHandler()
        2. 检查 X-Gitee-Event → return GiteeHandler()
        3. 检查 X-Gitlab-Event → return GitlabHandler()
        4. 检查自定义 header (从 configs[Provider.CUSTOM]) → return CustomHandler()
        5. 抛出 UnsupportedProviderError
        """
        pass
```

---

## Module Exports

**File**: `gitwebhooks/handlers/__init__.py`

```python
from .base import WebhookHandler
from .github import GithubHandler
from .gitee import GiteeHandler
from .gitlab import GitlabHandler
from .custom import CustomHandler
from .factory import HandlerFactory

__all__ = [
    'WebhookHandler',
    'GithubHandler',
    'GiteeHandler',
    'GitlabHandler',
    'CustomHandler',
    'HandlerFactory',
]
```

---

## Error Handling

所有处理器方法应该：

1. **明确抛出异常**: 使用特定的异常类（`SignatureValidationError`, `UnsupportedEventError`）
2. **返回详细结果**: `SignatureVerificationResult` 包含错误描述
3. **不吞没异常**: 让调用者处理错误
4. **记录日志**: 使用 `logging` 模块记录失败原因

---

## Performance Considerations

1. **签名验证**: 使用 `hmac.compare_digest()` 防止时序攻击
2. **路径提取**: 避免深层嵌套循环，使用迭代方式
3. **对象创建**: 处理器应该是无状态的，可以复用

---

## Testing Strategy

每个处理器需要：

1. **单元测试**: 测试每个方法的独立行为
2. **签名测试**: 使用已知的有效/无效签名测试
3. **边界情况**: 测试缺失字段、错误类型等
4. **集成测试**: 测试完整的请求处理流程
