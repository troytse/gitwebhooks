"""
GitHub Webhook Payload Fixtures

This module provides test data fixtures for GitHub webhook requests.
Based on GitHub webhook documentation:
https://docs.github.com/en/webhooks/webhook-events-and-payloads
"""

from typing import Dict, Any, Optional


# Standard GitHub push event payload
GITHUB_PUSH_PAYLOAD = {
    "ref": "refs/heads/main",
    "before": "a108b6712c4255e38fb5c07fd3ff90c4b2af4cf3",
    "after": "b3c8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8",
    "repository": {
        "id": 1296269,
        "node_id": "MDEwOlJlcG9zaXRvcnkxMjk2MjY5",
        "name": "Hello-World",
        "full_name": "octocat/Hello-World",
        "owner": {
            "login": "octocat",
            "id": 1,
            "node_id": "MDQ6VXNlcjE=",
            "avatar_url": "https://github.com/images/error/octocat_happy.gif",
            "type": "User"
        },
        "private": False,
        "description": "This your first repo!",
        "fork": False
    },
    "pusher": {
        "name": "octocat",
        "email": "octocat@github.com"
    },
    "sender": {
        "login": "octocat",
        "id": 1,
        "node_id": "MDQ6VXNlcjE=",
        "type": "User"
    }
}

# GitHub release event payload
GITHUB_RELEASE_PAYLOAD = {
    "action": "published",
    "release": {
        "id": 1,
        "tag_name": "v1.0.0",
        "name": "v1.0.0",
        "draft": False,
        "prerelease": False
    },
    "repository": {
        "id": 1296269,
        "name": "Hello-World",
        "full_name": "octocat/Hello-World",
        "owner": {
            "login": "octocat",
            "id": 1
        }
    },
    "sender": {
        "login": "octocat",
        "id": 1
    }
}

# GitHub ping event payload
GITHUB_PING_PAYLOAD = {
    "zen": "Keep it logically awesome.",
    "hook_id": 12345678,
    "repository": {
        "id": 1296269,
        "name": "Hello-World",
        "full_name": "octocat/Hello-World",
        "owner": {
            "login": "octocat",
            "id": 1
        }
    }
}


class PayloadBuilder:
    """
    Builder for creating GitHub webhook payloads with custom values.

    Usage:
        payload = PayloadBuilder.github_push_event(
            repo="user/repo",
            ref="refs/heads/develop"
        )
    """

    @staticmethod
    def github_push_event(
        repo: str = "octocat/Hello-World",
        ref: str = "refs/heads/main",
        before: Optional[str] = None,
        after: Optional[str] = None,
        pusher: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Build a GitHub push event payload.

        Args:
            repo: Repository full name (owner/name format)
            ref: Git reference (e.g., "refs/heads/main")
            before: Commit SHA before push
            after: Commit SHA after push
            pusher: Pusher username

        Returns:
            dict: GitHub push event payload
        """
        owner, name = repo.split('/', 1) if '/' in repo else (repo, repo)

        payload = {
            "ref": ref,
            "before": before or "a108b6712c4255e38fb5c07fd3ff90c4b2af4cf3",
            "after": after or "b3c8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8",
            "repository": {
                "id": 1296269,
                "node_id": "MDEwOlJlcG9zaXRvcnkxMjk2MjY5",
                "name": name,
                "full_name": repo,
                "owner": {
                    "login": owner,
                    "id": 1,
                    "node_id": "MDQ6VXNlcjE=",
                    "avatar_url": "https://github.com/images/error/octocat_happy.gif",
                    "type": "User"
                },
                "private": False,
                "description": "Test repository",
                "fork": False
            },
            "pusher": {
                "name": pusher or owner,
                "email": f"{pusher or owner}@github.com"
            },
            "sender": {
                "login": pusher or owner,
                "id": 1,
                "node_id": "MDQ6VXNlcjE=",
                "type": "User"
            }
        }

        return payload

    @staticmethod
    def github_release_event(
        repo: str = "octocat/Hello-World",
        tag: str = "v1.0.0",
        action: str = "published"
    ) -> Dict[str, Any]:
        """
        Build a GitHub release event payload.

        Args:
            repo: Repository full name
            tag: Release tag name
            action: Release action (published, created, etc.)

        Returns:
            dict: GitHub release event payload
        """
        owner, name = repo.split('/', 1) if '/' in repo else (repo, repo)

        return {
            "action": action,
            "release": {
                "id": 1,
                "tag_name": tag,
                "name": tag,
                "draft": False,
                "prerelease": False
            },
            "repository": {
                "id": 1296269,
                "name": name,
                "full_name": repo,
                "owner": {
                    "login": owner,
                    "id": 1
                }
            },
            "sender": {
                "login": owner,
                "id": 1
            }
        }

    @staticmethod
    def github_ping_event(repo: str = "octocat/Hello-World") -> Dict[str, Any]:
        """
        Build a GitHub ping event payload.

        Args:
            repo: Repository full name

        Returns:
            dict: GitHub ping event payload
        """
        return {
            "zen": "Keep it logically awesome.",
            "hook_id": 12345678,
            "repository": {
                "id": 1296269,
                "name": repo.split('/')[-1],
                "full_name": repo,
                "owner": {
                    "login": repo.split('/')[0],
                    "id": 1
                }
            }
        }

    @staticmethod
    def github_create_event(
        repo: str = "octocat/Hello-World",
        ref_type: str = "branch",
        ref: str = "main"
    ) -> Dict[str, Any]:
        """
        Build a GitHub create event payload.

        Args:
            repo: Repository full name
            ref_type: Type of ref created (branch, tag)
            ref: Name of ref

        Returns:
            dict: GitHub create event payload
        """
        owner, name = repo.split('/', 1) if '/' in repo else (repo, repo)

        return {
            "ref": ref,
            "ref_type": ref_type,
            "repository": {
                "id": 1296269,
                "name": name,
                "full_name": repo,
                "owner": {
                    "login": owner,
                    "id": 1
                }
            },
            "sender": {
                "login": owner,
                "id": 1
            }
        }
