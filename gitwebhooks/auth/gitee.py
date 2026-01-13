"""Gitee HMAC-SHA256/password verifier

Verifies signatures or passwords from Gitee webhooks.

According to Gitee official documentation:
https://help.gitee.com/webhook/how-to-verify-webhook-keys

Signature generation algorithm:
1. sign_string = timestamp + "\\n" + secret
2. hmac_sha256 = HmacSHA256(sign_string)
3. signature = base64(urlEncode(hmac_sha256))

Note: The Gitee signature does NOT include the request payload.
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

        Gitee sends X-Gitee-Timestamp in both signature and password modes.
        To distinguish between them:
        1. First try password validation (direct comparison)
        2. If password fails and timestamp exists, try signature validation

        This approach works because:
        - Passwords are typically short plaintext without special chars
        - Signatures are Base64 encoded, containing chars like '+', '/', '='

        Args:
            payload: Raw request body bytes (not used in Gitee signature)
            signature: X-Gitee-Token header value
            secret: Webhook secret/password
            **kwargs: May contain 'timestamp' key

        Returns:
            SignatureVerificationResult instance
        """
        if signature is None:
            return SignatureVerificationResult.failure('Missing signature or password')

        # Step 1: Try password validation first (direct comparison)
        if hmac.compare_digest(signature, secret):
            return SignatureVerificationResult.success()

        # Step 2: If password failed, try signature validation
        timestamp = kwargs.get('timestamp')
        if timestamp is not None:
            # Verify signature
            try:
                timestamp_int = int(timestamp)
            except ValueError:
                return SignatureVerificationResult.failure('Invalid timestamp format')

            # Gitee signature: timestamp + "\n" + secret
            # Reference: https://help.gitee.com/webhook/how-to-verify-webhook-keys
            sign_string = f'{timestamp_int}\n{secret}'
            secret_bytes = secret.encode('utf-8')

            signature_bytes = hmac.new(
                secret_bytes,
                sign_string.encode('utf-8'),
                self.HASH_ALGORITHM
            ).digest()
            # Gitee sends Base64 encoded signature (NOT URL encoded)
            expected_signature = base64.b64encode(signature_bytes).decode('utf-8')

            if hmac.compare_digest(signature, expected_signature):
                return SignatureVerificationResult.success()
            else:
                return SignatureVerificationResult.failure('Invalid signature')

        # Password validation failed and no timestamp for signature validation
        return SignatureVerificationResult.failure('Invalid password')
