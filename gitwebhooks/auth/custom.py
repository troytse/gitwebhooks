"""Custom token verifier

Verifies tokens from custom webhooks.
"""

from gitwebhooks.auth.verifier import SignatureVerifier
from gitwebhooks.models.result import SignatureVerificationResult


class CustomTokenVerifier(SignatureVerifier):
    """Custom token verifier"""

    def __init__(self, verify_enabled: bool = True):
        """Initialize verifier

        Args:
            verify_enabled: Whether verification is enabled (False = always return success)
        """
        self.verify_enabled = verify_enabled

    def verify(self, payload: bytes, signature: str, secret: str,
               **kwargs) -> SignatureVerificationResult:
        """Verify custom token

        Args:
            payload: Raw request body bytes (unused)
            signature: Token value from custom header
            secret: Configured secret key
            **kwargs: Unused

        Returns:
            SignatureVerificationResult instance
        """
        if not self.verify_enabled:
            return SignatureVerificationResult.success()

        if signature == secret:
            return SignatureVerificationResult.success()
        else:
            return SignatureVerificationResult.failure('Invalid token')
