"""Gitee webhook handler

Handles webhook requests from Gitee.

Gitee supports two authentication modes:
1. Signature mode: X-Gitee-Timestamp + X-Gitee-Token (HMAC-SHA256)
2. Password mode: X-Gitee-Token only (plaintext)

According to Gitee documentation:
https://help.gitee.com/webhook/how-to-verify-webhook-keys

Even when verify=False, if a password is provided (no timestamp),
it should still be validated for security.
"""

from typing import Optional

from gitwebhooks.handlers.base import WebhookHandler
from gitwebhooks.models.provider import Provider
from gitwebhooks.models.request import WebhookRequest
from gitwebhooks.models.result import SignatureVerificationResult
from gitwebhooks.config.models import ProviderConfig
from gitwebhooks.auth.factory import VerifierFactory
from gitwebhooks.utils.exceptions import SignatureValidationError, UnsupportedEventError


class GiteeHandler(WebhookHandler):
    """Gitee webhook handler"""

    def __init__(self):
        self._verifier = VerifierFactory.create_gitee_verifier()

    def get_provider(self) -> Provider:
        """Return Provider.GITEE"""
        return Provider.GITEE

    def verify_signature(self, request: WebhookRequest,
                        config: ProviderConfig) -> SignatureVerificationResult:
        """Verify Gitee signature or password

        Gitee has two modes:
        1. Signature mode: Has X-Gitee-Timestamp header
        2. Password mode: Only X-Gitee-Token header

        Args:
            request: Webhook request
            config: Provider configuration

        Returns:
            SignatureVerificationResult instance
        """
        signature = request.headers.get('X-Gitee-Token')
        timestamp = request.headers.get('X-Gitee-Timestamp')

        # Always validate if signature/token is provided
        if signature is None:
            return SignatureVerificationResult.failure('Missing signature or password')

        return self._verifier.verify(
            request.payload,
            signature,
            config.secret,
            timestamp=timestamp
        )

    def handle_request(self, request: WebhookRequest,
                      config: ProviderConfig) -> Optional[str]:
        """Handle complete webhook request

        Override base implementation to handle Gitee's special case:
        Even when verify=False, password validation is performed if provided.

        Args:
            request: Webhook request data
            config: Provider configuration

        Returns:
            Repository identifier, None if processing failed

        Raises:
            SignatureValidationError: Signature/password verification failed
            UnsupportedEventError: Event type not allowed
        """
        # Step 1: Check event
        if not self.is_event_allowed(request.event, config):
            raise UnsupportedEventError(f'Event not configured: {request.event}')

        # Step 2: Verify signature or password
        # For Gitee, we always validate if token is provided
        signature = request.headers.get('X-Gitee-Token')
        if signature is not None:
            result = self.verify_signature(request, config)
            if not result.is_valid:
                raise SignatureValidationError(result.error_message or 'Verification failed')
        elif config.verify:
            # verify=True but no signature provided
            raise SignatureValidationError('Missing signature')

        # Step 3: Extract repository identifier
        return self.extract_repository(request, config)

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
