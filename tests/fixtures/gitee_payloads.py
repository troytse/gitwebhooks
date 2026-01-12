"""
Gitee Webhook Payload Fixtures

This module provides test data fixtures for Gitee webhook requests.
Based on Gitee webhook documentation:
https://gitee.com/help/categories/4040
"""

from typing import Dict, Any, Optional


# Standard Gitee push event payload
GITEE_PUSH_PAYLOAD = {
    "ref": "refs/heads/master",
    "before": "0000000000000000000000000000000000000000",
    "after": "b3c8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8",
    "repository": {
        "id": 12345,
        "name": "test-repo",
        "full_name": "user/test-repo",
        "namespace": "user",
        "path_with_namespace": "user/test-repo",
        "url": "git@gitee.com:user/test-repo.git",
        "description": "Test repository"
    },
    "pusher": {
        "name": "user",
        "email": "user@example.com"
    },
    "sender": {
        "id": 123,
        "username": "user",
        "email": "user@example.com"
    }
}

# Gitee tag push event payload
GITEE_TAG_PUSH_PAYLOAD = {
    "ref": "refs/tags/v1.0.0",
    "before": "0000000000000000000000000000000000000000",
    "after": "a1b2c3d4e5f6789012345678901234567890abcd",
    "repository": {
        "id": 12345,
        "name": "test-repo",
        "full_name": "user/test-repo",
        "namespace": "user"
    },
    "pusher": {
        "name": "user",
        "email": "user@example.com"
    },
    "sender": {
        "username": "user"
    }
}

# Gitee merge request event payload
GITEE_MR_PAYLOAD = {
    "object_kind": "merge_request",
    "event_type": "Merge Request Hook",
    "repository": {
        "name": "test-repo",
        "url": "git@gitee.com:user/test-repo.git",
        "description": "Test repository",
        "homepage": "https://gitee.com/user/test-repo"
    },
    "object_attributes": {
        "id": 1,
        "target_branch": "master",
        "source_branch": "feature",
        "title": "Test MR"
    }
}


class PayloadBuilder:
    """
    Builder for creating Gitee webhook payloads with custom values.

    Usage:
        payload = PayloadBuilder.gitee_push_event(
            repo="user/repo",
            ref="refs/heads/develop"
        )
    """

    @staticmethod
    def gitee_push_event(
        repo: str = "user/test-repo",
        ref: str = "refs/heads/master",
        before: Optional[str] = None,
        after: Optional[str] = None,
        pusher: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Build a Gitee push event payload.

        Args:
            repo: Repository full name (owner/name format)
            ref: Git reference (e.g., "refs/heads/master")
            before: Commit SHA before push
            after: Commit SHA after push
            pusher: Pusher username

        Returns:
            dict: Gitee push event payload
        """
        namespace, name = repo.split('/', 1) if '/' in repo else (repo, repo)
        username = pusher or namespace

        payload = {
            "ref": ref,
            "before": before or "0000000000000000000000000000000000000000",
            "after": after or "b3c8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8",
            "repository": {
                "id": 12345,
                "name": name,
                "full_name": repo,
                "namespace": namespace,
                "path_with_namespace": repo,
                "url": f"git@gitee.com:{repo}.git",
                "description": "Test repository"
            },
            "pusher": {
                "name": username,
                "email": f"{username}@example.com"
            },
            "sender": {
                "id": 123,
                "username": username,
                "email": f"{username}@example.com"
            }
        }

        return payload

    @staticmethod
    def gitee_tag_push_event(
        repo: str = "user/test-repo",
        tag: str = "v1.0.0"
    ) -> Dict[str, Any]:
        """
        Build a Gitee tag push event payload.

        Args:
            repo: Repository full name
            tag: Tag name

        Returns:
            dict: Gitee tag push event payload
        """
        namespace, name = repo.split('/', 1) if '/' in repo else (repo, repo)

        return {
            "ref": f"refs/tags/{tag}",
            "before": "0000000000000000000000000000000000000000",
            "after": "a1b2c3d4e5f6789012345678901234567890abcd",
            "repository": {
                "id": 12345,
                "name": name,
                "full_name": repo,
                "namespace": namespace
            },
            "pusher": {
                "name": namespace,
                "email": f"{namespace}@example.com"
            },
            "sender": {
                "username": namespace
            }
        }

    @staticmethod
    def gitee_merge_request_event(
        repo: str = "user/test-repo",
        source_branch: str = "feature",
        target_branch: str = "master"
    ) -> Dict[str, Any]:
        """
        Build a Gitee merge request event payload.

        Args:
            repo: Repository full name
            source_branch: Source branch
            target_branch: Target branch

        Returns:
            dict: Gitee merge request event payload
        """
        namespace, name = repo.split('/', 1) if '/' in repo else (repo, repo)

        return {
            "object_kind": "merge_request",
            "event_type": "Merge Request Hook",
            "repository": {
                "name": name,
                "url": f"git@gitee.com:{repo}.git",
                "description": "Test repository",
                "homepage": f"https://gitee.com/{repo}"
            },
            "object_attributes": {
                "id": 1,
                "target_branch": target_branch,
                "source_branch": source_branch,
                "title": f"Merge {source_branch} into {target_branch}"
            }
        }
