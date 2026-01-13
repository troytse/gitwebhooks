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

    @property
    def repo_identifier(self) -> Optional[str]:
        """Extract repository identifier from post_data

        Returns:
            Repository identifier (e.g., 'owner/repo'), None if not found

        Extraction rules:
        - GitHub: repository.full_name
        - Gitee: repository.full_name
        - GitLab: project.path_with_namespace
        - Custom: Uses ProviderConfig.identifier_path
        """
        if self.post_data is None:
            return None

        extractors = {
            Provider.GITHUB: lambda d: d.get('repository', {}).get('full_name'),
            Provider.GITEE: lambda d: d.get('repository', {}).get('full_name'),
            Provider.GITLAB: lambda d: d.get('project', {}).get('path_with_namespace'),
        }

        extractor = extractors.get(self.provider)
        if extractor:
            result = extractor(self.post_data)
            return result if isinstance(result, str) else None

        # Custom provider uses identifier_path (handled in handler)
        return None
