"""
GitLab Webhook Payload Fixtures

This module provides test data fixtures for GitLab webhook requests.
Based on GitLab webhook documentation:
https://docs.gitlab.com/ee/user/project/integrations/webhook_events.html
"""

from typing import Dict, Any, Optional


# Standard GitLab push event payload

# GitLab tag push event payload

# GitLab merge request event payload

# GitLab pipeline event payload


class PayloadBuilder:
    """
    Builder for creating GitLab webhook payloads with custom values.

    Usage:
        payload = PayloadBuilder.gitlab_push_event(
            repo="user/repo",
            ref="refs/heads/develop"
        )
    """

    @staticmethod
    def gitlab_push_event(
        repo: str = "user/test-repo",
        ref: str = "refs/heads/main",
        before: Optional[str] = None,
        after: Optional[str] = None,
        username: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Build a GitLab push event payload.

        Args:
            repo: Repository full name (namespace/project format)
            ref: Git reference (e.g., "refs/heads/main")
            before: Commit SHA before push
            after: Commit SHA after push
            username: Username who triggered the push

        Returns:
            dict: GitLab push event payload
        """
        namespace, name = repo.split('/', 1) if '/' in repo else (repo, repo)
        user = username or namespace

        payload = {
            "object_kind": "push",
            "event_name": "push",
            "before": before or "a108b6712c4255e38fb5c07fd3ff90c4b2af4cf3",
            "after": after or "b3c8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8",
            "ref": ref,
            "project": {
                "id": 1,
                "name": name,
                "path_with_namespace": repo,
                "path": name,
                "namespace": namespace,
                "description": "Test repository",
                "web_url": f"https://gitlab.com/{repo}"
            },
            "user_username": user,
            "user_email": f"{user}@example.com",
            "user_name": user.title(),
            "user_id": 1,
            "total_commits_count": 1
        }

        return payload

    @staticmethod
    def gitlab_pipeline_event(
        repo: str = "user/test-repo",
        ref: str = "main",
        status: str = "success"
    ) -> Dict[str, Any]:
        """
        Build a GitLab pipeline event payload.

        Args:
            repo: Repository full name
            ref: Git reference
            status: Pipeline status (success, failed, pending)

        Returns:
            dict: GitLab pipeline event payload
        """
        namespace, name = repo.split('/', 1) if '/' in repo else (repo, repo)

        return {
            "object_kind": "pipeline",
            "event_name": "pipeline",
            "project": {
                "id": 1,
                "name": name,
                "path_with_namespace": repo
            },
            "object_attributes": {
                "id": 1,
                "ref": ref,
                "status": status
            }
        }
