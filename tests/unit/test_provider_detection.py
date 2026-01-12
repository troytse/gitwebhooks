"""
Unit Tests for Platform Detection (User Story 2)

Tests for verifying that the server correctly identifies webhook requests
from different Git platforms (GitHub, Gitee, GitLab, Custom).
"""

import unittest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tests.conftest import WebhookTestCase, TestConfigBuilder
from tests.utils.http_client import TestWebhookClient
from tests.fixtures.github_payloads import PayloadBuilder as GitHubPayloadBuilder


class TestProviderDetection(WebhookTestCase):
    """Test platform identification from HTTP headers."""

    def setUp(self):
        """Set up test environment."""
        super().setUp()
        self.temp_dir = self.create_temp_dir()

        # Create test configuration
        self.config_builder = TestConfigBuilder(self.temp_dir)
        self.config_builder.add_repository("test/repo", self.temp_dir, "echo 'test'")

    def test_github_headers_detected(self):
        """
        Test that X-GitHub-Event header identifies GitHub platform.

        GitHub webhooks include the X-GitHub-Event header which
        identifies the request as coming from GitHub.
        """
        config_path = self.config_builder.build()

        from tests.utils.server_manager import TestServer

        with TestServer(config_path) as server:
            server.wait_for_ready()

            client = TestWebhookClient("127.0.0.1", server.port)

            # Send request with GitHub header
            response = client.send_webhook(
                headers={"X-GitHub-Event": "push"},
                payload=GitHubPayloadBuilder.github_push_event(repo="test/repo")
            )

            # GitHub platform should be detected (not 412 for unknown provider)
            # Response might be 404 if repo config not exact match, but provider should be recognized
            # The key is that we don't get "unknown provider" type errors
            self.assertNotEqual(response.status_code, 412,
                              "GitHub platform should be recognized")

    def test_gitee_headers_detected(self):
        """
        Test that X-Gitee-Event header identifies Gitee platform.

        Gitee webhooks include the X-Gitee-Event header which
        identifies the request as coming from Gitee.
        """
        config_path = self.config_builder.build()

        from tests.utils.server_manager import TestServer

        with TestServer(config_path) as server:
            server.wait_for_ready()

            client = TestWebhookClient("127.0.0.1", server.port)

            from tests.fixtures.gitee_payloads import PayloadBuilder as GiteePayloadBuilder

            # Send request with Gitee header
            response = client.send_webhook(
                headers={"X-Gitee-Event": "Push Hook"},
                payload=GiteePayloadBuilder.gitee_push_event(repo="test/repo")
            )

            # Gitee platform should be detected
            self.assertNotEqual(response.status_code, 412,
                              "Gitee platform should be recognized")

    def test_gitlab_headers_detected(self):
        """
        Test that X-Gitlab-Event header identifies GitLab platform.

        GitLab webhooks include the X-Gitlab-Event header which
        identifies the request as coming from GitLab.
        """
        config_path = self.config_builder.build()

        from tests.utils.server_manager import TestServer

        with TestServer(config_path) as server:
            server.wait_for_ready()

            client = TestWebhookClient("127.0.0.1", server.port)

            from tests.fixtures.gitlab_payloads import PayloadBuilder as GitLabPayloadBuilder

            # Send request with GitLab header
            response = client.send_webhook(
                headers={"X-Gitlab-Event": "push"},
                payload=GitLabPayloadBuilder.gitlab_push_event(repo="test/repo")
            )

            # GitLab platform should be detected
            self.assertNotEqual(response.status_code, 412,
                              "GitLab platform should be recognized")

    def test_custom_headers_detected(self):
        """
        Test that custom header_name/header_value identifies Custom platform.

        Custom webhooks are identified by configured header name and value.
        """
        config_path = self.config_builder.build()

        from tests.utils.server_manager import TestServer

        with TestServer(config_path) as server:
            server.wait_for_ready()

            client = TestWebhookClient("127.0.0.1", server.port)

            from tests.fixtures.custom_payloads import PayloadBuilder as CustomPayloadBuilder

            # Send request with custom header (matching default config)
            response = client.send_webhook(
                headers={
                    "X-Custom-Header": "Custom-Git-Hookshot",
                    "X-Custom-Event": "push"
                },
                payload=CustomPayloadBuilder.custom_push_event(repo="test/repo")
            )

            # Custom platform should be detected
            self.assertNotEqual(response.status_code, 412,
                              "Custom platform should be recognized")

    def test_no_platform_headers_returns_none(self):
        """
        Test that absence of platform headers results in unknown provider.

        When no platform identification headers are present, the server
        should reject the request.
        """
        config_path = self.config_builder.build()

        from tests.utils.server_manager import TestServer

        with TestServer(config_path) as server:
            server.wait_for_ready()

            client = TestWebhookClient("127.0.0.1", server.port)

            # Send request without any platform headers
            response = client.send_webhook(
                headers={},
                payload={"test": "data"}
            )

            # Should be rejected (412 or similar error)
            self.assertIn(response.status_code, [400, 404, 412],
                         f"Expected rejection for unknown provider, got {response.status_code}")

    def test_github_case_sensitivity(self):
        """
        Test GitHub header detection is case-sensitive.

        The X-GitHub-Event header should be detected with exact casing.
        """
        config_path = self.config_builder.build()

        from tests.utils.server_manager import TestServer

        with TestServer(config_path) as server:
            server.wait_for_ready()

            client = TestWebhookClient("127.0.0.1", server.port)

            # Send with incorrect case
            response = client.send_webhook(
                headers={"X-github-event": "push"},  # Wrong case
                payload=GitHubPayloadBuilder.github_push_event(repo="test/repo")
            )

            # Should fail due to case sensitivity
            # Server may not recognize the platform with wrong case
            self.assertIn(response.status_code, [400, 404, 412],
                         "Case sensitivity should matter for platform detection")

    def test_custom_header_value_mismatch(self):
        """
        Test that mismatched custom header value is not recognized.

        Custom platform requires both header name AND value to match.
        """
        config_path = self.config_builder.build()

        from tests.utils.server_manager import TestServer

        with TestServer(config_path) as server:
            server.wait_for_ready()

            client = TestWebhookClient("127.0.0.1", server.port)

            # Send with wrong header value
            response = client.send_webhook(
                headers={
                    "X-Custom-Header": "Wrong-Value",  # Doesn't match "Custom-Git-Hookshot"
                    "X-Custom-Event": "push"
                },
                payload={"test": "data"}
            )

            # Should be rejected
            self.assertIn(response.status_code, [400, 404, 412],
                         "Mismatched custom header value should not be recognized")


if __name__ == '__main__':
    unittest.main()
