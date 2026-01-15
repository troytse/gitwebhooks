"""
Integration Tests for Custom Webhook Handling (User Story 6)

Tests for verifying that the server correctly processes custom webhook requests.
"""

import unittest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tests.conftest import WebhookTestCase, TestConfigBuilder
from tests.utils.http_client import TestWebhookClient
from tests.utils.server_manager import TestServer
from tests.fixtures.custom_payloads import PayloadBuilder as CustomPayloadBuilder


class TestCustomWebhook(WebhookTestCase):
    """Test custom webhook processing."""

    def setUp(self):
        """Set up test environment."""
        super().setUp()
        self.temp_dir = self.create_temp_dir()

    def test_custom_header_recognized(self):
        """
        Test that configured header_name/header_value identifies custom platform.
        """
        config_builder = TestConfigBuilder(self.temp_dir)
        config_builder.set_platform_verify('custom', verify=False)
        config_builder.add_repository("team/custom-repo", self.temp_dir,
                                     "echo 'test' > /dev/null")
        config_path = config_builder.build()

        with TestServer(config_path) as server:
            server.wait_for_ready()

            client = TestWebhookClient("127.0.0.1", server.port)

            # Default config uses X-Custom-Header: Custom-Git-Hookshot
            response = client.send_webhook(
                headers={
                    "X-Custom-Header": "Custom-Git-Hookshot",
                    "X-Custom-Event": "push"
                },
                payload=CustomPayloadBuilder.custom_push_event(repo="team/custom-repo")
            )

            self.assertNotEqual(response.status_code, 412)

    def test_identifier_path_extracted(self):
        """
        Test that identifier_path extracts repository name correctly.
        """
        config_builder = TestConfigBuilder(self.temp_dir)
        config_builder.set_platform_verify('custom', verify=False)
        config_builder.add_repository("team/service", self.temp_dir,
                                     "echo 'test' > /dev/null")
        config_path = config_builder.build()

        with TestServer(config_path) as server:
            server.wait_for_ready()

            client = TestWebhookClient("127.0.0.1", server.port)

            # Default identifier_path is project.path_with_namespace
            response = client.send_webhook(
                headers={
                    "X-Custom-Header": "Custom-Git-Hookshot",
                    "X-Custom-Event": "push"
                },
                payload=CustomPayloadBuilder.custom_push_event(repo="team/service")
            )

            self.assertNotEqual(response.status_code, 404)

    def test_valid_token_accepted(self):
        """
        Test that matching header_token is accepted.
        """
        config_builder = TestConfigBuilder(self.temp_dir)
        config_builder.set_platform_verify('custom', verify=False, secret="custom_secret")
        config_builder.add_repository("team/repo", self.temp_dir,
                                     "echo 'test' > /dev/null")
        config_path = config_builder.build()

        with TestServer(config_path) as server:
            server.wait_for_ready()

            client = TestWebhookClient("127.0.0.1", server.port)

            # Default header_token is X-Custom-Token
            response = client.send_webhook(
                headers={
                    "X-Custom-Header": "Custom-Git-Hookshot",
                    "X-Custom-Token": "custom_secret",
                    "X-Custom-Event": "push"
                },
                payload=CustomPayloadBuilder.custom_push_event(repo="team/repo")
            )

            self.assertNotEqual(response.status_code, 401)

    def test_invalid_token_returns_401(self):
        """
        Test that wrong header_token returns 401.
        """
        config_builder = TestConfigBuilder(self.temp_dir)
        config_builder.set_platform_verify('custom', verify=True, secret="correct_secret")
        config_builder.add_repository("team/repo", self.temp_dir,
                                     "echo 'test' > /dev/null")
        config_path = config_builder.build()

        with TestServer(config_path) as server:
            server.wait_for_ready()

            client = TestWebhookClient("127.0.0.1", server.port)

            response = client.send_webhook(
                headers={
                    "X-Custom-Header": "Custom-Git-Hookshot",
                    "X-Custom-Token": "wrong_secret",
                    "X-Custom-Event": "push"
                },
                payload=CustomPayloadBuilder.custom_push_event(repo="team/repo")
            )

            self.assertStatusCode(response, 401)


if __name__ == '__main__':
    unittest.main()
