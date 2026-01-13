"""
Integration Tests for Gitee Webhook Handling (User Story 4)

Tests for verifying that the server correctly processes Gitee webhook requests,
including signature verification and password authentication.
"""

import unittest
import sys
import json
import time
from pathlib import Path
import tempfile

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tests.conftest import WebhookTestCase, TestConfigBuilder
from tests.utils.http_client import TestWebhookClient
from tests.utils.server_manager import TestServer
from tests.fixtures.gitee_payloads import PayloadBuilder as GiteePayloadBuilder
from tests.fixtures.signature_builder import SignatureBuilder


class TestGiteeWebhook(WebhookTestCase):
    """Test Gitee webhook processing."""

    def setUp(self):
        """Set up test environment."""
        super().setUp()
        self.temp_dir = self.create_temp_dir()

    def test_no_signature_accepted_when_verify_false(self):
        """
        Test that requests without signature are accepted when verify=False.
        """
        config_builder = TestConfigBuilder(self.temp_dir)
        config_builder.set_platform_verify('gitee', verify=False)
        config_builder.add_repository("user/test-repo", self.temp_dir,
                                     "echo 'test' > /dev/null")
        config_path = config_builder.build()

        with TestServer(config_path) as server:
            server.wait_for_ready()

            client = TestWebhookClient("127.0.0.1", server.port)

            response = client.send_webhook(
                headers={"X-Gitee-Event": "Push Hook"},
                payload=GiteePayloadBuilder.gitee_push_event(repo="user/test-repo")
            )

            self.assertNotEqual(response.status_code, 401)

    def test_valid_signature_accepted(self):
        """
        Test that valid HMAC-SHA256 signature is accepted.
        """
        config_builder = TestConfigBuilder(self.temp_dir)
        config_builder.set_platform_verify('gitee', verify=True, secret="test_secret")
        config_builder.add_repository("user/test-repo", self.temp_dir,
                                     "echo 'test' > /dev/null")
        config_path = config_builder.build()

        with TestServer(config_path) as server:
            server.wait_for_ready()

            client = TestWebhookClient("127.0.0.1", server.port)

            payload = GiteePayloadBuilder.gitee_push_event(repo="user/test-repo")
            timestamp = 1705000000
            # Gitee signature does NOT use payload
            signature = SignatureBuilder.gitee_signature("test_secret", timestamp)

            response = client.send_webhook(
                headers={
                    "X-Gitee-Event": "Push Hook",
                    "X-Gitee-Timestamp": str(timestamp),
                    "X-Gitee-Token": signature
                },
                payload=payload
            )

            self.assertNotEqual(response.status_code, 401)

    def test_invalid_signature_returns_401(self):
        """
        Test that invalid signature returns 401.
        """
        config_builder = TestConfigBuilder(self.temp_dir)
        config_builder.set_platform_verify('gitee', verify=True, secret="test_secret")
        config_builder.add_repository("user/test-repo", self.temp_dir,
                                     "echo 'test' > /dev/null")
        config_path = config_builder.build()

        with TestServer(config_path) as server:
            server.wait_for_ready()

            client = TestWebhookClient("127.0.0.1", server.port)

            response = client.send_webhook(
                headers={
                    "X-Gitee-Event": "Push Hook",
                    "X-Gitee-Timestamp": "1705000000",
                    "X-Gitee-Token": "invalid_base64_signature"
                },
                payload=GiteePayloadBuilder.gitee_push_event(repo="user/test-repo")
            )

            self.assertStatusCode(response, 401)

    def test_password_accepted_when_matches(self):
        """
        Test that password authentication via X-Gitee-Token works.
        """
        config_builder = TestConfigBuilder(self.temp_dir)
        config_builder.set_platform_verify('gitee', verify=False, secret="test_password")
        config_builder.add_repository("user/test-repo", self.temp_dir,
                                     "echo 'test' > /dev/null")
        config_path = config_builder.build()

        with TestServer(config_path) as server:
            server.wait_for_ready()

            client = TestWebhookClient("127.0.0.1", server.port)

            response = client.send_webhook(
                headers={
                    "X-Gitee-Event": "Push Hook",
                    "X-Gitee-Token": "test_password"
                },
                payload=GiteePayloadBuilder.gitee_push_event(repo="user/test-repo")
            )

            self.assertNotEqual(response.status_code, 401)

    def test_wrong_password_returns_401(self):
        """
        Test that wrong password returns 401.
        """
        config_builder = TestConfigBuilder(self.temp_dir)
        config_builder.set_platform_verify('gitee', verify=False, secret="correct_password")
        config_builder.add_repository("user/test-repo", self.temp_dir,
                                     "echo 'test' > /dev/null")
        config_path = config_builder.build()

        with TestServer(config_path) as server:
            server.wait_for_ready()

            client = TestWebhookClient("127.0.0.1", server.port)

            response = client.send_webhook(
                headers={
                    "X-Gitee-Event": "Push Hook",
                    "X-Gitee-Token": "wrong_password"
                },
                payload=GiteePayloadBuilder.gitee_push_event(repo="user/test-repo")
            )

            self.assertStatusCode(response, 401)

    def test_unhandled_event_returns_406(self):
        """
        Test that events not in handle_events return 406.
        """
        config_builder = TestConfigBuilder(self.temp_dir)
        config_builder.set_platform_verify('gitee', verify=False)
        config_builder.add_repository("user/test-repo", self.temp_dir,
                                     "echo 'test' > /dev/null")
        config_path = config_builder.build()

        with TestServer(config_path) as server:
            server.wait_for_ready()

            client = TestWebhookClient("127.0.0.1", server.port)

            # Send Merge Request event (not "Push Hook")
            response = client.send_webhook(
                headers={"X-Gitee-Event": "Merge Request Hook"},
                payload=GiteePayloadBuilder.gitee_merge_request_event(repo="user/test-repo")
            )

            self.assertStatusCode(response, 406)


if __name__ == '__main__':
    unittest.main()
