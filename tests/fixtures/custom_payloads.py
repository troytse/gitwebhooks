"""
Custom Webhook Payload Fixtures

This module provides test data fixtures for custom webhook requests.
Custom webhooks can have any JSON structure.
"""

from typing import Dict, Any, Optional


# Standard custom push event payload

# Custom deployment event payload

# Custom release event payload


class PayloadBuilder:
    """
    Builder for creating custom webhook payloads with custom values.

    Custom webhooks have flexible structure. The identifier_path
    configuration determines how the repository name is extracted.

    Usage:
        payload = PayloadBuilder.custom_push_event(
            repo="team/repo",
            event="deploy",
            ref="main"
        )
    """

    @staticmethod
    def custom_push_event(
        repo: str = "team/custom-repo",
        event: str = "push",
        ref: str = "main",
        before: Optional[str] = None,
        after: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Build a custom push event payload.

        Args:
            repo: Repository identifier (any format)
            event: Event type string
            ref: Git reference or branch name
            before: Previous commit SHA
            after: New commit SHA

        Returns:
            dict: Custom push event payload
        """
        name = repo.split('/')[-1] if '/' in repo else repo

        payload = {
            "event": event,
            "project": {
                "path_with_namespace": repo,
                "name": name
            },
            "ref": ref,
            "before": before or "abc123",
            "after": after or "def456"
        }

        return payload
