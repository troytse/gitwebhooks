"""GitHub HMAC-SHA1 signature verifier

Verifies HMAC-SHA1 signatures from GitHub webhooks.
"""

import hashlib
import hmac

from gitwebhooks.auth.verifier import SignatureVerifier
from gitwebhooks.models.result import SignatureVerificationResult


class GithubSignatureVerifier(SignatureVerifier):
    """GitHub HMAC-SHA1 signature verifier"""

    PREFIX = 'sha1='
    HASH_ALGORITHM = hashlib.sha1

    def verify(self, payload: bytes, signature: str, secret: str,
               **kwargs) -> SignatureVerificationResult:
        """Verify GitHub HMAC-SHA1 signature

        Args:
            payload: Raw request body bytes
            signature: X-Hub-Signature header value
            secret: Webhook secret
            **kwargs: Unused

        Returns:
            SignatureVerificationResult instance
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

        # Use constant-time comparison
        if hmac.compare_digest(signature, expected_signature):
            return SignatureVerificationResult.success()
        else:
            return SignatureVerificationResult.failure('Invalid signature')
