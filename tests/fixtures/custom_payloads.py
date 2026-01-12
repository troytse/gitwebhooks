"""
Custom Webhook Payload Fixtures

This module provides test data fixtures for custom webhook requests.
Custom webhooks can have any JSON structure.
"""

from typing import Dict, Any, Optional


# Standard custom push event payload
CUSTOM_PUSH_PAYLOAD = {
    "event": "push",
    "project": {
        "path_with_namespace": "team/custom-repo",
        "name": "custom-repo"
    },
    "ref": "main",
    "before": "abc123",
    "after": "def456"
}

# Custom deployment event payload
CUSTOM_DEPLOYMENT_PAYLOAD = {
    "event": "deployment",
    "project": {
        "path_with_namespace": "team/app",
        "name": "app"
    },
    "environment": "production",
    "status": "success"
}

# Custom release event payload
CUSTOM_RELEASE_PAYLOAD = {
    "event": "release",
    "project": {
        "path_with_namespace": "team/project",
        "name": "project"
    },
    "version": "v2.0.0",
    "notes": "Release notes here"
}


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

    @staticmethod
    def custom_deployment_event(
        repo: str = "team/app",
        environment: str = "production",
        status: str = "success"
    ) -> Dict[str, Any]:
        """
        Build a custom deployment event payload.

        Args:
            repo: Repository identifier
            environment: Target environment
            status: Deployment status

        Returns:
            dict: Custom deployment event payload
        """
        name = repo.split('/')[-1] if '/' in repo else repo

        return {
            "event": "deployment",
            "project": {
                "path_with_namespace": repo,
                "name": name
            },
            "environment": environment,
            "status": status,
            "timestamp": "2025-01-12T00:00:00Z"
        }

    @staticmethod
    def custom_release_event(
        repo: str = "team/project",
        version: str = "v1.0.0",
        notes: str = "Release notes"
    ) -> Dict[str, Any]:
        """
        Build a custom release event payload.

        Args:
            repo: Repository identifier
            version: Release version
            notes: Release notes

        Returns:
            dict: Custom release event payload
        """
        name = repo.split('/')[-1] if '/' in repo else repo

        return {
            "event": "release",
            "project": {
                "path_with_namespace": repo,
                "name": name
            },
            "version": version,
            "notes": notes
        }

    @staticmethod
    def custom_build_event(
        repo: str = "team/service",
        build_id: str = "#123",
        status: str = "completed"
    ) -> Dict[str, Any]:
        """
        Build a custom build event payload.

        Args:
            repo: Repository identifier
            build_id: Build identifier
            status: Build status

        Returns:
            dict: Custom build event payload
        """
        name = repo.split('/')[-1] if '/' in repo else repo

        return {
            "event": "build",
            "project": {
                "path_with_namespace": repo,
                "name": name
            },
            "build_id": build_id,
            "status": status
        }

    @staticmethod
    def custom_with_nested_path(
        repo: str = "org/nested/project",
        event: str = "push"
    ) -> Dict[str, Any]:
        """
        Build a custom payload with nested path structure.

        Useful for testing complex identifier_path configurations.

        Args:
            repo: Repository path with multiple segments
            event: Event type

        Returns:
            dict: Custom payload with nested structure
        """
        segments = repo.split('/')
        name = segments[-1]

        return {
            "event": event,
            "data": {
                "project": {
                    "path_with_namespace": repo,
                    "name": name,
                    "organization": segments[0] if len(segments) > 0 else None
                }
            },
            "metadata": {
                "timestamp": "2025-01-12T00:00:00Z"
            }
        }

    @staticmethod
    def custom_with_array_index(
        repo: str = "team/repo",
        index: int = 0
    ) -> Dict[str, Any]:
        """
        Build a custom payload with array data.

        Useful for testing identifier_path with array access like
        "projects[0].name".

        Args:
            repo: Repository identifier
            index: Array index

        Returns:
            dict: Custom payload with array structure
        """
        return {
            "event": "batch",
            "projects": [
                {
                    "name": repo,
                    "status": "success"
                },
                {
                    "name": "another/repo",
                    "status": "pending"
                }
            ]
        }
