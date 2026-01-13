"""
Webhook Signature Builder

This module provides signature builders for various Git platforms.
Used in tests to create valid webhook signatures.

According to Gitee official documentation:
https://help.gitee.com/webhook/how-to-verify-webhook-keys

Actual Gitee signature algorithm:
1. sign_string = timestamp + "\\n" + secret
2. hmac_sha256 = HmacSHA256(sign_string)
3. signature = base64(hmac_sha256)

Note: Gitee sends Base64 encoded signature in HTTP headers, NOT URL encoded.
The documentation mentions URL encode, but actual implementation sends raw Base64.
"""

import hmac
import hashlib
import base64
from typing import Union


class SignatureBuilder:
    """
    Builder for creating webhook signatures.

    Each platform uses a different signature algorithm:
    - GitHub: HMAC-SHA1 with "sha1=" prefix
    - Gitee: HMAC-SHA256 with timestamp + "\\n" + secret, Base64 encoded (NOT URL encoded)
    - GitLab: Simple token comparison (no signature)

    Usage:
        payload = b'{"test": "data"}'
        secret = "my_webhook_secret"

        # GitHub signature
        gh_sig = SignatureBuilder.github_signature(payload, secret)

        # Gitee signature (payload NOT used in signature)
        gt_sig = SignatureBuilder.gitee_signature(secret, timestamp=1234567890)
    """

    @staticmethod
    def github_signature(payload: bytes, secret: str) -> str:
        """
        Calculate GitHub webhook HMAC-SHA1 signature.

        GitHub uses HMAC-SHA1 with the webhook secret as the key.
        The signature is prefixed with "sha1=".

        Args:
            payload: Request body as bytes
            secret: Webhook secret string

        Returns:
            str: Signature in format "sha1=hexdigest"

        Example:
            >>> payload = b'{"ref": "main"}'
            >>> secret = "webhook_secret"
            >>> sig = SignatureBuilder.github_signature(payload, secret)
            >>> print(sig)
            sha1=abcdef1234567890...
        """
        # Create HMAC-SHA1 hash
        mac = hmac.new(secret.encode('utf-8'), payload, hashlib.sha1)
        signature = mac.hexdigest()

        # GitHub format: sha1=<hexdigest>
        return f"sha1={signature}"

    @staticmethod
    def gitee_signature(secret: str, timestamp: int) -> str:
        """
        Calculate Gitee webhook HMAC-SHA256 signature.

        According to Gitee official documentation:
        https://help.gitee.com/webhook/how-to-verify-webhook-keys

        Algorithm (actual implementation):
        1. sign_string = timestamp + "\\n" + secret
        2. hmac_sha256 = HmacSHA256(sign_string)
        3. signature = base64(hmac_sha256)

        Note: The request payload is NOT used in Gitee signature calculation.
        Gitee sends Base64 encoded signature, NOT URL encoded (despite documentation).

        Args:
            secret: Webhook secret string
            timestamp: Unix timestamp in milliseconds

        Returns:
            str: Base64 encoded signature (e.g., "KIUdWqRiZxFY6HZcBw0+nEXtSkAS6qKpzwMFfcC6tx4=")

        Example:
            >>> secret = "webhook_secret"
            >>> timestamp = 1705000000
            >>> sig = SignatureBuilder.gitee_signature(secret, timestamp)
            >>> print(sig)
            YWJjZGVmMTIzNDU2Nzg5MA==
        """
        # Gitee signs: timestamp + "\n" + secret
        # Reference: https://help.gitee.com/webhook/how-to-verify-webhook-keys
        sign_string = f"{timestamp}\n{secret}"

        # Create HMAC-SHA256 hash
        mac = hmac.new(secret.encode('utf-8'), sign_string.encode('utf-8'), hashlib.sha256)
        signature = mac.digest()

        # Base64 encode (Gitee sends Base64, NOT URL encoded)
        return base64.b64encode(signature).decode('utf-8')

    @staticmethod
    def gitlab_token(token: str) -> str:
        """
        Return GitLab token as-is (GitLab uses simple token comparison).

        GitLab doesn't use cryptographic signatures. It uses a simple
        token that is sent in the X-Gitlab-Token header.

        Args:
            token: Token string

        Returns:
            str: The same token string
        """
        return token

    @staticmethod
    def custom_token(token: str) -> str:
        """
        Return custom platform token as-is.

        Custom webhooks can use token-based authentication similar
        to GitLab.

        Args:
            token: Token string

        Returns:
            str: The same token string
        """
        return token

    @staticmethod
    def verify_github_signature(payload: bytes, secret: str,
                                 signature_header: str) -> bool:
        """
        Verify GitHub webhook signature.

        Args:
            payload: Request body as bytes
            secret: Webhook secret
            signature_header: Value from X-Hub-Signature header

        Returns:
            bool: True if signature is valid
        """
        expected = SignatureBuilder.github_signature(payload, secret)

        # Use constant-time comparison to prevent timing attacks
        return hmac.compare_digest(expected, signature_header)

    @staticmethod
    def verify_gitee_signature(secret: str, timestamp: int,
                                signature_header: str) -> bool:
        """
        Verify Gitee webhook signature.

        Note: payload is NOT used in Gitee signature verification.

        Args:
            secret: Webhook secret
            timestamp: Timestamp from X-Gitee-Timestamp header
            signature_header: Signature value from X-Gitee-Token header

        Returns:
            bool: True if signature is valid
        """
        expected = SignatureBuilder.gitee_signature(secret, timestamp)

        # Use constant-time comparison
        return hmac.compare_digest(expected, signature_header)

    @staticmethod
    def verify_gitlab_token(token: str, token_header: str) -> bool:
        """
        Verify GitLab webhook token.

        Args:
            token: Configured secret token
            token_header: Value from X-Gitlab-Token header

        Returns:
            bool: True if tokens match
        """
        return hmac.compare_digest(token, token_header)

    @staticmethod
    def generate_invalid_signature() -> str:
        """
        Generate an invalid signature for testing.

        Returns:
            str: An invalid signature string
        """
        return "sha1=invalid_signature_1234567890abcdef"


class SignatureError(Exception):
    """Exception raised for signature-related errors."""
    pass


def sign_payload(platform: str, payload: Union[bytes, str],
                 secret: str, **kwargs) -> str:
    """
    Convenience function to sign a payload for a specific platform.

    Note: For Gitee, the payload is NOT used in signature calculation.

    Args:
        platform: Platform name ('github', 'gitee', 'gitlab', 'custom')
        payload: Request payload (not used for Gitee)
        secret: Webhook secret
        **kwargs: Platform-specific arguments (e.g., timestamp for Gitee)

    Returns:
        str: Signature or token

    Raises:
        SignatureError: If platform is not supported

    Example:
        >>> sig = sign_payload('github', b'{"test": "data"}', 'secret')
        >>> print(sig)
        sha1=abc123...
    """
    if isinstance(payload, str):
        payload = payload.encode('utf-8')

    if platform == 'github':
        return SignatureBuilder.github_signature(payload, secret)
    elif platform == 'gitee':
        timestamp = kwargs.get('timestamp', 1705000000)
        # Note: Gitee signature does NOT use payload
        return SignatureBuilder.gitee_signature(secret, timestamp)
    elif platform == 'gitlab':
        return SignatureBuilder.gitlab_token(secret)
    elif platform == 'custom':
        return SignatureBuilder.custom_token(secret)
    else:
        raise SignatureError(f"Unsupported platform: {platform}")
