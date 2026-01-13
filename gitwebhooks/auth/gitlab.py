"""Gitlab Token 验证器

验证 Gitlab webhook 的 token。
"""

from gitwebhooks.auth.verifier import SignatureVerifier
from gitwebhooks.models.result import SignatureVerificationResult


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
        """
        if signature == secret:
            return SignatureVerificationResult.success()
        else:
            return SignatureVerificationResult.failure('Invalid token')
