"""Gitee HMAC-SHA256/password verifier

Verifies signatures or passwords from Gitee webhooks.
"""

import base64
import hashlib
import hmac

from gitwebhooks.auth.verifier import SignatureVerifier
from gitwebhooks.models.result import SignatureVerificationResult


class GiteeSignatureVerifier(SignatureVerifier):
    """Gitee HMAC-SHA256/password verifier"""

    HASH_ALGORITHM = hashlib.sha256

    def verify(self, payload: bytes, signature: str, secret: str,
               **kwargs) -> SignatureVerificationResult:
        """Verify Gitee signature or password

        Args:
            payload: Raw request body bytes
            signature: X-Gitee-Token header value
            secret: Webhook secret/password
            **kwargs: May contain 'timestamp' key

        Returns:
            SignatureVerificationResult instance
        """
        if signature is None:
            return SignatureVerificationResult.failure('Missing signature or password')

        # Check for timestamp (signature mode)
        timestamp = kwargs.get('timestamp')
        if timestamp is not None:
            # Verify signature
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
            # Verify password
            if signature == secret:
                return SignatureVerificationResult.success()
            else:
                return SignatureVerificationResult.failure('Invalid password')
