"""Signature verifier base class

Defines the abstract interface for signature verification.
"""

from abc import ABC, abstractmethod

from gitwebhooks.models.result import SignatureVerificationResult


class SignatureVerifier(ABC):
    """Signature verifier base class

    All platform-specific verifiers must inherit from this class and implement the verification method.
    """

    @abstractmethod
    def verify(self, payload: bytes, signature: str, secret: str,
               **kwargs) -> SignatureVerificationResult:
        """Verify signature

        Args:
            payload: Raw request body bytes
            signature: Signature string from request
            secret: Configured secret key
            **kwargs: Platform-specific additional parameters (e.g., timestamp)

        Returns:
            SignatureVerificationResult instance

        Raises:
            SignatureValidationError: When verification fails (optional)
        """
        pass
