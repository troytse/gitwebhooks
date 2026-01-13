"""Github HMAC-SHA1 签名验证器

验证 Github webhook 的 HMAC-SHA1 签名。
"""

import hashlib
import hmac

from gitwebhooks.auth.verifier import SignatureVerifier
from gitwebhooks.models.result import SignatureVerificationResult


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
