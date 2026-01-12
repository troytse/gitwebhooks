"""
Integration Tests for GitLab Webhook Handling (User Story 5)

Tests for verifying that the server correctly processes GitLab webhook requests,
including token verification and event filtering.
"""

import unittest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tests.conftest import WebhookTestCase, TestConfigBuilder
from tests.utils.http_client import TestWebhookClient
from tests.utils.server_manager import TestServer
from tests.fixtures.gitlab_payloads import PayloadBuilder as GitLabPayloadBuilder


class TestGitLabWebhook(WebhookTestCase):
    """Test GitLab webhook processing."""

    def setUp(self):
        """Set up test environment."""
        super().setUp()
        self.temp_dir = self.create_temp_dir()

    def test_no_token_accepted_when_verify_false(self):
        """
        Test that requests without token are accepted when verify=False.
        """
        config_builder = TestConfigBuilder(self.temp_dir)
        config_builder.set_platform_verify('gitlab', verify=False)
        config_builder.add_repository("user/test-repo", self.temp_dir,
                                     "echo 'test' > /dev/null")
        config_path = config_builder.build()

        with TestServer(config_path) as server:
            server.wait_for_ready()

            client = TestWebhookClient("127.0.0.1", server.port)

            response = client.send_webhook(
                headers={"X-Gitlab-Event": "push"},
                payload=GitLabPayloadBuilder.gitlab_push_event(repo="user/test-repo")
            )

            self.assertNotEqual(response.status_code, 401)

    def test_valid_token_accepted(self):
        """
        Test that valid X-Gitlab-Token is accepted.
        """
        config_builder = TestConfigBuilder(self.temp_dir)
        config_builder.set_platform_verify('gitlab', verify=True, secret="test_token")
        config_builder.add_repository("user/test-repo", self.temp_dir,
                                     "echo 'test' > /dev/null")
        config_path = config_builder.build()

        with TestServer(config_path) as server:
            server.wait_for_ready()

            client = TestWebhookClient("127.0.0.1", server.port)

            response = client.send_webhook(
                headers={
                    "X-Gitlab-Event": "push",
                    "X-Gitlab-Token": "test_token"
                },
                payload=GitLabPayloadBuilder.gitlab_push_event(repo="user/test-repo")
            )

            self.assertNotEqual(response.status_code, 401)

    def test_invalid_token_returns_401(self):
        """
        Test that invalid token returns 401.
        """
        config_builder = TestConfigBuilder(self.temp_dir)
        config_builder.set_platform_verify('gitlab', verify=True, secret="correct_token")
        config_builder.add_repository("user/test-repo", self.temp_dir,
                                     "echo 'test' > /dev/null")
        config_path = config_builder.build()

        with TestServer(config_path) as server:
            server.wait_for_ready()

            client = TestWebhookClient("127.0.0.1", server.port)

            response = client.send_webhook(
                headers={
                    "X-Gitlab-Event": "push",
                    "X-Gitlab-Token": "wrong_token"
                },
                payload=GitLabPayloadBuilder.gitlab_push_event(repo="user/test-repo")
            )

            self.assertStatusCode(response, 401)

    def test_unhandled_event_returns_406(self):
        """
        Test that events not in handle_events return 406.
        """
        config_builder = TestConfigBuilder(self.temp_dir)
        config_builder.set_platform_verify('gitlab', verify=False)
        config_builder.add_repository("user/test-repo", self.temp_dir,
                                     "echo 'test' > /dev/null")
        config_path = config_builder.build()

        with TestServer(config_path) as server:
            server.wait_for_ready()

            client = TestWebhookClient("127.0.0.1", server.port)

            # Send pipeline event (not "push")
            response = client.send_webhook(
                headers={"X-Gitlab-Event": "pipeline"},
                payload=GitLabPayloadBuilder.gitlab_pipeline_event(repo="user/test-repo")
            )

            self.assertStatusCode(response, 406)

    def test_project_path_with_namespace_extracted(self):
        """
        Test that project.path_with_namespace is correctly extracted.
        """
        config_builder = TestConfigBuilder(self.temp_dir)
        config_builder.set_platform_verify('gitlab', verify=False)
        config_builder.add_repository("mygroup/myproject", self.temp_dir,
                                     "echo 'test' > /dev/null")
        config_path = config_builder.build()

        with TestServer(config_path) as server:
            server.wait_for_ready()

            client = TestWebhookClient("127.0.0.1", server.port)

            response = client.send_webhook(
                headers={"X-Gitlab-Event": "push"},
                payload=GitLabPayloadBuilder.gitlab_push_event(repo="mygroup/myproject")
            )

            # Should find the repo
            self.assertNotEqual(response.status_code, 404)


if __name__ == '__main__':
    unittest.main()
