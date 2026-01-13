"""GitLab webhook handler

Handles webhook requests from GitLab.
"""

from typing import Optional

from gitwebhooks.handlers.base import WebhookHandler
from gitwebhooks.models.provider import Provider
from gitwebhooks.models.request import WebhookRequest
from gitwebhooks.models.result import SignatureVerificationResult
from gitwebhooks.config.models import ProviderConfig
from gitwebhooks.auth.factory import VerifierFactory


class GitlabHandler(WebhookHandler):
    """GitLab webhook handler"""

    def __init__(self):
        self._verifier = VerifierFactory.create_gitlab_verifier()

    def get_provider(self) -> Provider:
        """Return Provider.GITLAB"""
        return Provider.GITLAB

    def verify_signature(self, request: WebhookRequest,
                        config: ProviderConfig) -> SignatureVerificationResult:
        """Verify GitLab token"""
        signature = request.headers.get('X-Gitlab-Token')
        return self._verifier.verify(request.payload, signature, config.secret)

    def extract_repository(self, request: WebhookRequest,
                          config: ProviderConfig) -> Optional[str]:
        """Extract GitLab project path from request"""
        if request.post_data is None:
            return None
        project = request.post_data.get('project', {})
        return project.get('path_with_namespace') if isinstance(project, dict) else None

    def is_event_allowed(self, event: Optional[str],
                        config: ProviderConfig) -> bool:
        """Check if event is in config.handle_events list"""
        return config.allows_event(event)
