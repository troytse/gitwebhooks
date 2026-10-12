"""GitLab token verifier

Verifies tokens from GitLab webhooks.
"""

from gitwebhooks.auth.verifier import SignatureVerifier
from gitwebhooks.models.result import SignatureVerificationResult


class GitlabTokenVerifier(SignatureVerifier):
    """GitLab token verifier"""

    def verify(self, payload: bytes, signature: str, secret: str,
               **kwargs) -> SignatureVerificationResult:
        """Verify GitLab token

        Args:
            payload: Raw request body bytes (unused)
            signature: X-Gitlab-Token header value
            secret: Webhook token
            **kwargs: Unused

        Returns:
            SignatureVerificationResult instance
        """
        # An empty secret means verification is not actually configured.
        # Without this guard an empty token would match and let an
        # unauthenticated request through (which would run the deploy command).
        if not secret:
            return SignatureVerificationResult.failure('Secret not configured')

        if signature == secret:
            return SignatureVerificationResult.success()
        else:
            return SignatureVerificationResult.failure('Invalid token')
