"""Custom webhook handler

Handles webhook requests from custom webhook sources.
"""

from typing import Optional

from gitwebhooks.handlers.base import WebhookHandler
from gitwebhooks.models.provider import Provider
from gitwebhooks.models.request import WebhookRequest
from gitwebhooks.models.result import SignatureVerificationResult
from gitwebhooks.config.models import ProviderConfig
from gitwebhooks.auth.factory import VerifierFactory


class CustomHandler(WebhookHandler):
    """Custom webhook handler"""

    def __init__(self):
        self._verifier = None  # Created dynamically based on configuration

    def get_provider(self) -> Provider:
        """Return Provider.CUSTOM"""
        return Provider.CUSTOM

    def verify_signature(self, request: WebhookRequest,
                        config: ProviderConfig) -> SignatureVerificationResult:
        """Verify custom token"""
        # Create verifier (verification enabled depends on whether header_token is configured)
        verify_enabled = bool(config.header_token)
        if not self._verifier:
            self._verifier = VerifierFactory.create_custom_verifier(verify_enabled)

        signature = request.headers.get(config.header_token) if config.header_token else ''
        return self._verifier.verify(request.payload, signature, config.secret)

    def extract_repository(self, request: WebhookRequest,
                          config: ProviderConfig) -> Optional[str]:
        """Extract repository identifier using JSON path"""
        if request.post_data is None or not config.identifier_path:
            return None

        # Split path by '.'
        path_parts = config.identifier_path.split('.')
        current = request.post_data

        # Traverse level by level
        for part in path_parts:
            if isinstance(current, dict):
                current = current.get(part)
            else:
                return None

        # Return final value (must be string)
        return current if isinstance(current, str) else None

    def is_event_allowed(self, event: Optional[str],
                        config: ProviderConfig) -> bool:
        """Check if event is allowed

        Args:
            event: Event type (already parsed from headers by caller)
            config: Provider configuration

        Returns:
            True if event is allowed, False otherwise
        """
        # If no event header configured, allow all events
        if not config.header_event:
            return config.allows_event(event)

        # Use the passed event parameter (already parsed from headers by caller)
        return config.allows_event(event)
