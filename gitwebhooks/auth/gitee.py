"""Gitee HMAC-SHA256/密码验证器

验证 Gitee webhook 的签名或密码。
"""

import base64
import hashlib
import hmac

from gitwebhooks.auth.verifier import SignatureVerifier
from gitwebhooks.models.result import SignatureVerificationResult


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
