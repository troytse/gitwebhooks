"""Handler base class

Defines the abstract interface for webhook handlers.
"""

from abc import ABC, abstractmethod
from typing import Optional

from gitwebhooks.models.provider import Provider
from gitwebhooks.models.request import WebhookRequest
from gitwebhooks.models.result import SignatureVerificationResult
from gitwebhooks.config.models import ProviderConfig
from gitwebhooks.utils.exceptions import SignatureValidationError, UnsupportedEventError


class WebhookHandler(ABC):
    """Webhook handler base class

    All platform-specific handlers must inherit from this class and implement all abstract methods.
    """

    @abstractmethod
    def get_provider(self) -> Provider:
        """Return the provider type supported by this handler

        Returns:
            Provider enum value
        """
        pass

    @abstractmethod
    def verify_signature(self, request: WebhookRequest,
                        config: ProviderConfig) -> SignatureVerificationResult:
        """Verify webhook signature

        Args:
            request: Webhook request data
            config: Provider configuration (includes secret)

        Returns:
            Signature verification result

        Raises:
            SignatureValidationError: When verification fails
        """
        pass

    @abstractmethod
    def extract_repository(self, request: WebhookRequest,
                          config: ProviderConfig) -> Optional[str]:
        """Extract repository identifier from request

        Args:
            request: Webhook request data
            config: Provider configuration (may include identifier_path)

        Returns:
            Repository identifier (e.g., 'owner/repo'), None if not found
        """
        pass

    @abstractmethod
    def is_event_allowed(self, event: Optional[str],
                        config: ProviderConfig) -> bool:
        """Check if event type is allowed to be handled

        Args:
            event: Event type (e.g., 'push', 'merge_request')
            config: Provider configuration (includes handle_events list)

        Returns:
            True if event is allowed, False otherwise
        """
        pass

    def handle_request(self, request: WebhookRequest,
                      config: ProviderConfig) -> Optional[str]:
        """Handle complete webhook request

        This is a template method that defines the fixed flow of request processing:
        1. Check if event is allowed
        2. Verify signature
        3. Extract repository identifier

        Args:
            request: Webhook request data
            config: Provider configuration

        Returns:
            Repository identifier, None if processing failed

        Raises:
            SignatureValidationError: Signature verification failed
            UnsupportedEventError: Event type not allowed
        """
        # Step 1: Check event
        if not self.is_event_allowed(request.event, config):
            raise UnsupportedEventError(f'Event not configured: {request.event}')

        # Step 2: Verify signature (if required)
        if config.verify:
            result = self.verify_signature(request, config)
            if not result.is_valid:
                raise SignatureValidationError(result.error_message or 'Verification failed')

        # Step 3: Extract repository identifier
        return self.extract_repository(request, config)
