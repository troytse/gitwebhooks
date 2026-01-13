"""Gitee webhook handler

Handles webhook requests from Gitee.
"""

from typing import Optional

from gitwebhooks.handlers.base import WebhookHandler
from gitwebhooks.models.provider import Provider
from gitwebhooks.models.request import WebhookRequest
from gitwebhooks.models.result import SignatureVerificationResult
from gitwebhooks.config.models import ProviderConfig
from gitwebhooks.auth.factory import VerifierFactory


class GiteeHandler(WebhookHandler):
    """Gitee webhook handler"""

    def __init__(self):
        self._verifier = VerifierFactory.create_gitee_verifier()

    def get_provider(self) -> Provider:
        """Return Provider.GITEE"""
        return Provider.GITEE

    def verify_signature(self, request: WebhookRequest,
                        config: ProviderConfig) -> SignatureVerificationResult:
        """Verify Gitee signature or password"""
        signature = request.headers.get('X-Gitee-Token')
        timestamp = request.headers.get('X-Gitee-Timestamp')
        return self._verifier.verify(
            request.payload,
            signature,
            config.secret,
            timestamp=timestamp
        )

    def extract_repository(self, request: WebhookRequest,
                          config: ProviderConfig) -> Optional[str]:
        """Extract Gitee repository full name from request"""
        if request.post_data is None:
            return None
        repo = request.post_data.get('repository', {})
        return repo.get('full_name') if isinstance(repo, dict) else None

    def is_event_allowed(self, event: Optional[str],
                        config: ProviderConfig) -> bool:
        """Check if event is in config.handle_events list"""
        return config.allows_event(event)
