"""Custom exception classes

Defines all exception types used in the project.
"""


class WebhookError(Exception):
    """Webhook processing error base class"""
    pass


class SignatureValidationError(WebhookError):
    """Signature verification failed"""
    pass


class UnsupportedEventError(WebhookError):
    """Unsupported event type"""
    pass


class UnsupportedProviderError(WebhookError):
    """Unrecognized platform provider"""
    pass


class ConfigurationError(WebhookError):
    """Configuration error or missing"""
    pass


class RequestParseError(WebhookError):
    """Request parsing failed"""
    pass
