"""Webhook request data wrapper

Represents a parsed HTTP webhook request.
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional

from gitwebhooks.models.provider import Provider


@dataclass
class WebhookRequest:
    """Webhook request data wrapper

    Attributes:
        provider: Git platform provider
        event: Event type (e.g., 'push', 'merge_request')
        payload: Raw request body bytes
        headers: HTTP request headers
        post_data: Parsed JSON/form data
        content_type: Content-Type header value
        content_length: Content-Length header value
    """
    provider: Provider
    event: Optional[str]
    payload: bytes
    headers: Dict[str, str]
    post_data: Optional[Dict[str, Any]]
    content_type: str
    content_length: int
