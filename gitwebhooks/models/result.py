"""Signature verification result dataclass

Represents the result status of signature verification.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class SignatureVerificationResult:
    """Signature verification result

    Attributes:
        is_valid: Whether verification passed
        error_message: Error description when verification fails
    """
    is_valid: bool
    error_message: Optional[str] = None

    @classmethod
    def success(cls) -> 'SignatureVerificationResult':
        """Create a successful verification result

        Returns:
            Result object with is_valid=True
        """
        return cls(is_valid=True)

    @classmethod
    def failure(cls, message: str) -> 'SignatureVerificationResult':
        """Create a failed verification result

        Args:
            message: Error description

        Returns:
            Result object with is_valid=False and error message
        """
        return cls(is_valid=False, error_message=message)
