"""自定义 Token 验证器

验证自定义 webhook 的 token。
"""

from gitwebhooks.auth.verifier import SignatureVerifier
from gitwebhooks.models.result import SignatureVerificationResult


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
        """
        if not self.verify_enabled:
            return SignatureVerificationResult.success()

        if signature == secret:
            return SignatureVerificationResult.success()
        else:
            return SignatureVerificationResult.failure('Invalid token')
