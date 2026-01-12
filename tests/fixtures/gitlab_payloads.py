"""
GitLab Webhook Payload Fixtures

This module provides test data fixtures for GitLab webhook requests.
Based on GitLab webhook documentation:
https://docs.gitlab.com/ee/user/project/integrations/webhook_events.html
"""

from typing import Dict, Any, Optional


# Standard GitLab push event payload
GITLAB_PUSH_PAYLOAD = {
    "object_kind": "push",
    "event_name": "push",
    "before": "a108b6712c4255e38fb5c07fd3ff90c4b2af4cf3",
    "after": "b3c8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8",
    "ref": "refs/heads/main",
    "project": {
        "id": 1,
        "name": "test-repo",
        "path_with_namespace": "user/test-repo",
        "path": "test-repo",
        "namespace": "user",
        "description": "Test repository",
        "web_url": "https://gitlab.com/user/test-repo"
    },
    "user_username": "user",
    "user_email": "user@example.com",
    "user_name": "Test User",
    "user_id": 1,
    "total_commits_count": 1
}

# GitLab tag push event payload
GITLAB_TAG_PUSH_PAYLOAD = {
    "object_kind": "push",
    "event_name": "tag_push",
    "before": "0000000000000000000000000000000000000000",
    "after": "a1b2c3d4e5f6789012345678901234567890abcd",
    "ref": "refs/tags/v1.0.0",
    "project": {
        "id": 1,
        "name": "test-repo",
        "path_with_namespace": "user/test-repo"
    },
    "user_username": "user"
}

# GitLab merge request event payload
GITLAB_MR_PAYLOAD = {
    "object_kind": "merge_request",
    "event_type": "merge_request",
    "project": {
        "id": 1,
        "name": "test-repo",
        "path_with_namespace": "user/test-repo"
    },
    "object_attributes": {
        "id": 1,
        "target_branch": "main",
        "source_branch": "feature",
        "title": "Test MR",
        "state": "opened"
    }
}

# GitLab pipeline event payload
GITLAB_PIPELINE_PAYLOAD = {
    "object_kind": "pipeline",
    "event_name": "pipeline",
    "project": {
        "id": 1,
        "name": "test-repo",
        "path_with_namespace": "user/test-repo"
    },
    "object_attributes": {
        "id": 1,
        "ref": "main",
        "status": "success"
    }
}


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
    def gitlab_tag_push_event(
        repo: str = "user/test-repo",
        tag: str = "v1.0.0"
    ) -> Dict[str, Any]:
        """
        Build a GitLab tag push event payload.

        Args:
            repo: Repository full name
            tag: Tag name

        Returns:
            dict: GitLab tag push event payload
        """
        namespace, name = repo.split('/', 1) if '/' in repo else (repo, repo)

        return {
            "object_kind": "push",
            "event_name": "tag_push",
            "before": "0000000000000000000000000000000000000000",
            "after": "a1b2c3d4e5f6789012345678901234567890abcd",
            "ref": f"refs/tags/{tag}",
            "project": {
                "id": 1,
                "name": name,
                "path_with_namespace": repo
            },
            "user_username": namespace
        }

    @staticmethod
    def gitlab_merge_request_event(
        repo: str = "user/test-repo",
        source_branch: str = "feature",
        target_branch: str = "main"
    ) -> Dict[str, Any]:
        """
        Build a GitLab merge request event payload.

        Args:
            repo: Repository full name
            source_branch: Source branch
            target_branch: Target branch

        Returns:
            dict: GitLab merge request event payload
        """
        namespace, name = repo.split('/', 1) if '/' in repo else (repo, repo)

        return {
            "object_kind": "merge_request",
            "event_type": "merge_request",
            "project": {
                "id": 1,
                "name": name,
                "path_with_namespace": repo
            },
            "object_attributes": {
                "id": 1,
                "target_branch": target_branch,
                "source_branch": source_branch,
                "title": f"Merge {source_branch} into {target_branch}",
                "state": "opened"
            }
        }

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
