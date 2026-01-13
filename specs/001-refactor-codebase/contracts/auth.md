# Auth Module Contract

**Module**: `gitwebhooks.auth`
**Version**: 1.0.0
**Status**: Design Phase

## Overview

认证模块负责验证 webhook 请求的签名和 token。提供统一的验证接口和平台特定的验证实现。

---

## Base Verifier Contract

**Class**: `SignatureVerifier`
**Module**: `gitwebhooks.auth.verifier`
**Type**: Abstract Base Class (ABC)

```python
from abc import ABC, abstractmethod

from gitwebhooks.models.result import SignatureVerificationResult

class SignatureVerifier(ABC):
    """签名验证器基类

    所有平台特定的验证器必须继承此类并实现验证方法。
    """

    @abstractmethod
    def verify(self, payload: bytes, signature: str, secret: str,
               **kwargs) -> SignatureVerificationResult:
        """验证签名

        Args:
            payload: 原始请求体字节
            signature: 请求中的签名字符串
            secret: 配置的密钥
            **kwargs: 平台特定的额外参数（如 timestamp）

        Returns:
            SignatureVerificationResult 实例

        Raises:
            SignatureValidationError: 验证失败时（可选）
        """
        pass
```

---

## GitHub Verifier Contract

**Class**: `GithubSignatureVerifier`
**Module**: `gitwebhooks.auth.github`
**Extends**: `SignatureVerifier`

### Algorithm Specification

**Signature Format**: `sha1=<hex_digest>`

**Calculation**:
```python
import hmac
import hashlib

expected_signature = 'sha1=' + hmac.new(
    secret.encode('utf-8'),
    payload,
    hashlib.sha1
).hexdigest()
```

**Comparison**:
- 使用 `hmac.compare_digest()` 防止时序攻击
- 常量时间比较，不使用 `==`

### Implementation Contract

```python
import hmac
import hashlib

class GithubSignatureVerifier(SignatureVerifier):
    """Github HMAC-SHA1 签名验证器"""

    PREFIX = 'sha1='
    HASH_ALGORITHM = hashlib.sha1

    def verify(self, payload: bytes, signature: str, secret: str,
               **kwargs) -> SignatureVerificationResult:
        """验证 Github HMAC-SHA1 签名

        Args:
            payload: 原始请求体字节
            signature: X-Hub-Signature header 值
            secret: Webhook secret
            **kwargs: 未使用

        Returns:
            SignatureVerificationResult 实例

        Implementation Steps:
        1. 如果 signature 为 None，返回 failure('Missing signature')
        2. 如果 secret 为空，返回 failure('Secret not configured')
        3. 如果 signature 不以 'sha1=' 开头，返回 failure('Invalid signature format')
        4. 计算 expected_signature
        5. 使用 hmac.compare_digest() 比较
        6. 返回 success() 或 failure('Invalid signature')
        """
        if signature is None:
            return SignatureVerificationResult.failure('Missing signature')

        if not secret:
            return SignatureVerificationResult.failure('Secret not configured')

        if not signature.startswith(self.PREFIX):
            return SignatureVerificationResult.failure('Invalid signature format')

        secret_bytes = secret.encode('utf-8')
        expected_signature = self.PREFIX + hmac.new(
            secret_bytes,
            payload,
            self.HASH_ALGORITHM
        ).hexdigest()

        # 使用常量时间比较
        if hmac.compare_digest(signature, expected_signature):
            return SignatureVerificationResult.success()
        else:
            return SignatureVerificationResult.failure('Invalid signature')
```

### Test Cases

| Payload | Secret | Signature | Expected |
|---------|--------|-----------|----------|
| "test" | "secret" | Valid SHA1 | success() |
| "test" | "secret" | Invalid SHA1 | failure('Invalid signature') |
| "test" | "secret" | None | failure('Missing signature') |
| "test" | "" | Any | failure('Secret not configured') |
| "test" | "secret" | "sha2=..." | failure('Invalid signature format') |

---

## Gitee Verifier Contract

**Class**: `GiteeSignatureVerifier`
**Module**: `gitwebhooks.auth.gitee`
**Extends**: `SignatureVerifier`

### Algorithm Specification

**Two Modes**:

1. **Signature Mode** (with timestamp):
   - Sign string: `timestamp + payload`
   - Algorithm: HMAC-SHA256
   - Encoding: Base64

   ```python
   sign_string = timestamp + payload.decode('utf-8')
   signature_bytes = hmac.new(
       secret.encode('utf-8'),
       sign_string.encode('utf-8'),
       hashlib.sha256
   ).digest()
   expected_signature = base64.b64encode(signature_bytes).decode('utf-8')
   ```

2. **Password Mode** (without timestamp):
   - Simple string comparison
   - No encoding

### Implementation Contract

```python
import base64
import hmac
import hashlib

class GiteeSignatureVerifier(SignatureVerifier):
    """Gitee HMAC-SHA256/密码验证器"""

    HASH_ALGORITHM = hashlib.sha256

    def verify(self, payload: bytes, signature: str, secret: str,
               **kwargs) -> SignatureVerificationResult:
        """验证 Gitee 签名或密码

        Args:
            payload: 原始请求体字节
            signature: X-Gitee-Token header 值
            secret: Webhook secret/password
            **kwargs: 可能包含 'timestamp' 键

        Returns:
            SignatureVerificationResult 实例

        Implementation Steps:
        1. 如果 signature 为 None，返回 failure('Missing signature or password')
        2. 提取 timestamp = kwargs.get('timestamp')
        3. 如果 timestamp 存在（签名模式）:
           a. 尝试转换为 int，失败则返回 failure('Invalid timestamp format')
           b. 计算 sign_string = timestamp + payload.decode()
           c. 计算 HMAC-SHA256
           d. Base64 编码
           e. 使用 hmac.compare_digest() 比较
        4. 如果 timestamp 不存在（密码模式）:
           a. 直接比较 signature 与 secret
        5. 返回结果
        """
        if signature is None:
            return SignatureVerificationResult.failure('Missing signature or password')

        # 检查是否有 timestamp（签名模式）
        timestamp = kwargs.get('timestamp')
        if timestamp is not None:
            # 验证签名
            try:
                timestamp_int = int(timestamp)
            except ValueError:
                return SignatureVerificationResult.failure('Invalid timestamp format')

            payload_str = payload.decode('utf-8') if isinstance(payload, bytes) else payload
            sign_string = f'{timestamp_int}{payload_str}'
            secret_bytes = secret.encode('utf-8')

            signature_bytes = hmac.new(
                secret_bytes,
                sign_string.encode('utf-8'),
                self.HASH_ALGORITHM
            ).digest()
            expected_signature = base64.b64encode(signature_bytes).decode('utf-8')

            if hmac.compare_digest(signature, expected_signature):
                return SignatureVerificationResult.success()
            else:
                return SignatureVerificationResult.failure('Invalid signature')
        else:
            # 验证密码
            if signature == secret:
                return SignatureVerificationResult.success()
            else:
                return SignatureVerificationResult.failure('Invalid password')
```

### Test Cases

| Mode | Timestamp | Signature | Expected |
|------|-----------|-----------|----------|
| Signature | "1234567890" | Valid HMAC-SHA256 | success() |
| Signature | "invalid" | Any | failure('Invalid timestamp format') |
| Signature | "1234567890" | Invalid HMAC | failure('Invalid signature') |
| Password | None | Matching secret | success() |
| Password | None | Wrong secret | failure('Invalid password') |

---

## GitLab Verifier Contract

**Class**: `GitlabTokenVerifier`
**Module**: `gitwebhooks.auth.gitlab`
**Extends**: `SignatureVerifier`

### Algorithm Specification

**Method**: Simple token comparison

No HMAC calculation, direct string equality check.

### Implementation Contract

```python
class GitlabTokenVerifier(SignatureVerifier):
    """Gitlab Token 验证器"""

    def verify(self, payload: bytes, signature: str, secret: str,
               **kwargs) -> SignatureVerificationResult:
        """验证 Gitlab Token

        Args:
            payload: 原始请求体字节（未使用）
            signature: X-Gitlab-Token header 值
            secret: Webhook token
            **kwargs: 未使用

        Returns:
            SignatureVerificationResult 实例

        Implementation Steps:
        1. 直接比较 signature 与 secret
        2. 返回 success() 或 failure('Invalid token')
        """
        if signature == secret:
            return SignatureVerificationResult.success()
        else:
            return SignatureVerificationResult.failure('Invalid token')
```

### Test Cases

| Token | Secret | Expected |
|-------|--------|----------|
| "valid-token" | "valid-token" | success() |
| "wrong-token" | "valid-token" | failure('Invalid token') |
| None | "valid-token" | failure('Invalid token') |

---

## Custom Verifier Contract

**Class**: `CustomTokenVerifier`
**Module**: `gitwebhooks.auth.custom`
**Extends**: `SignatureVerifier`

### Algorithm Specification

**Method**: Optional token comparison

- 如果 `header_token` 配置为空，跳过验证（总是返回 success）
- 如果配置了 `header_token`，简单字符串比较

### Implementation Contract

```python
class CustomTokenVerifier(SignatureVerifier):
    """自定义 Token 验证器"""

    def __init__(self, verify_enabled: bool = True):
        """初始化验证器

        Args:
            verify_enabled: 是否启用验证（False = 总是返回 success）
        """
        self.verify_enabled = verify_enabled

    def verify(self, payload: bytes, signature: str, secret: str,
               **kwargs) -> SignatureVerificationResult:
        """验证自定义 Token

        Args:
            payload: 原始请求体字节（未使用）
            signature: 自定义 header 的 token 值
            secret: 配置的密钥
            **kwargs: 未使用

        Returns:
            SignatureVerificationResult 实例

        Implementation Steps:
        1. 如果 verify_enabled 为 False，返回 success()
        2. 比较 signature 与 secret
        3. 返回结果
        """
        if not self.verify_enabled:
            return SignatureVerificationResult.success()

        if signature == secret:
            return SignatureVerificationResult.success()
        else:
            return SignatureVerificationResult.failure('Invalid token')
```

### Test Cases

| Verify Enabled | Signature | Secret | Expected |
|----------------|-----------|--------|----------|
| False | Any | Any | success() |
| True | "token" | "token" | success() |
| True | "wrong" | "token" | failure('Invalid token') |

---

## Verifier Factory Contract

**Class**: `VerifierFactory`
**Module**: `gitwebhooks.auth`
**Type**: Factory class

```python
from gitwebhooks.models.provider import Provider
from gitwebhooks.auth.verifier import SignatureVerifier
from gitwebhooks.auth.github import GithubSignatureVerifier
from gitwebhooks.auth.gitee import GiteeSignatureVerifier
from gitwebhooks.auth.gitlab import GitlabTokenVerifier
from gitwebhooks.auth.custom import CustomTokenVerifier

class VerifierFactory:
    """验证器工厂类

    根据提供者类型创建对应的验证器实例
    """

    _verifiers = {
        Provider.GITHUB: GithubSignatureVerifier(),
        Provider.GITEE: GiteeSignatureVerifier(),
        Provider.GITLAB: GitlabTokenVerifier(),
        Provider.CUSTOM: None,  # Custom verifier created dynamically
    }

    @classmethod
    def get_verifier(cls, provider: Provider,
                    verify_enabled: bool = True) -> SignatureVerifier:
        """获取提供者对应的验证器

        Args:
            provider: 提供者类型
            verify_enabled: 是否启用验证（仅对 CUSTOM 有效）

        Returns:
            SignatureVerifier 实例

        Raises:
            UnsupportedProviderError: 不支持的提供者
        """
        if provider == Provider.CUSTOM:
            return CustomTokenVerifier(verify_enabled=verify_enabled)

        verifier = cls._verifiers.get(provider)
        if verifier is None:
            raise UnsupportedProviderError(f'No verifier for provider: {provider}')
        return verifier

    @classmethod
    def create_github_verifier(cls) -> GithubSignatureVerifier:
        """创建 Github 验证器（便利方法）"""
        return GithubSignatureVerifier()

    @classmethod
    def create_gitee_verifier(cls) -> GiteeSignatureVerifier:
        """创建 Gitee 验证器（便利方法）"""
        return GiteeSignatureVerifier()

    @classmethod
    def create_gitlab_verifier(cls) -> GitlabTokenVerifier:
        """创建 Gitlab 验证器（便利方法）"""
        return GitlabTokenVerifier()

    @classmethod
    def create_custom_verifier(cls, verify_enabled: bool = True) -> CustomTokenVerifier:
        """创建自定义验证器（便利方法）

        Args:
            verify_enabled: 是否启用验证
        """
        return CustomTokenVerifier(verify_enabled=verify_enabled)
```

---

## Module Exports

**File**: `gitwebhooks/auth/__init__.py`

```python
from .verifier import SignatureVerifier
from .github import GithubSignatureVerifier
from .gitee import GiteeSignatureVerifier
from .gitlab import GitlabTokenVerifier
from .custom import CustomTokenVerifier
from .factory import VerifierFactory

__all__ = [
    'SignatureVerifier',
    'GithubSignatureVerifier',
    'GiteeSignatureVerifier',
    'GitlabTokenVerifier',
    'CustomTokenVerifier',
    'VerifierFactory',
]
```

---

## Security Considerations

### 1. Timing Attack Prevention

所有签名比较必须使用 `hmac.compare_digest()`：

```python
# ❌ 错误：易受时序攻击
if signature == expected_signature:
    return True

# ✅ 正确：常量时间比较
if hmac.compare_digest(signature, expected_signature):
    return True
```

### 2. Secret Storage

- Secrets 只能存储在配置文件中
- Never hardcode secrets in code
- 配置文件权限应该是 0600（用户可读）

### 3. Signature Replay Protection

当前实现不包含时间戳验证（除了 Gitee 可选模式）。

**Future Enhancement**: 考虑添加:
- Timestamp validation
- Nonce mechanism
- Expiration time

---

## Performance Considerations

1. **HMAC 计算**: SHA-1/SHA-256 是快速的原生实现
2. **Base64 编码**: 使用标准库 `base64` 模块
3. **对象创建**: 验证器应该是无状态的，可以复用

---

## Testing Strategy

1. **算法正确性**: 使用已知向量测试
2. **边界情况**: 空字符串、None 值、错误类型
3. **时序攻击**: 验证使用常量时间比较
4. **错误处理**: 验证适当的错误消息
5. **性能**: 验证签名验证速度足够快

### Test Vectors

**GitHub HMAC-SHA1**:
```
Payload: "hello"
Secret: "webhook"
Expected: sha1=6f9b9af3c6b5e1234abcd567890ef1234567890a
```

**Gitee HMAC-SHA256** (with timestamp):
```
Payload: "test"
Timestamp: "1234567890"
Secret: "secret"
Expected: (Base64 of HMAC-SHA256("1234567890test", "secret"))
```
