"""
GitHub Webhook Payload Fixtures

This module provides test data fixtures for GitHub webhook requests.
Based on GitHub webhook documentation:
https://docs.github.com/en/webhooks/webhook-events-and-payloads
"""

from typing import Dict, Any, Optional


# Standard GitHub push event payload

# GitHub release event payload

# GitHub ping event payload


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
