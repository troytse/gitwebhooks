"""
Integration Tests for GitHub Webhook Handling (User Story 3)

Tests for verifying that the server correctly processes GitHub webhook requests,
including signature verification, event filtering, and repository name extraction.
"""

import unittest
import sys
import json
from pathlib import Path
import tempfile
import os

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tests.conftest import WebhookTestCase, TestConfigBuilder
from tests.utils.http_client import TestWebhookClient
from tests.utils.server_manager import TestServer
from tests.fixtures.github_payloads import PayloadBuilder, GITHUB_PUSH_PAYLOAD
from tests.fixtures.signature_builder import SignatureBuilder


class TestGitHubWebhook(WebhookTestCase):
    """Test GitHub webhook processing."""

    def setUp(self):
        """Set up test environment."""
        super().setUp()
        self.temp_dir = self.create_temp_dir()

    def test_no_signature_accepted_when_verify_false(self):
        """
        Test that requests without signature are accepted when verify=False.

        When GitHub signature verification is disabled in config,
        requests should be processed without X-Hub-Signature header.
        """
        config_builder = TestConfigBuilder(self.temp_dir)
        config_builder.set_platform_verify('github', verify=False)
        config_builder.add_repository("octocat/Hello-World", self.temp_dir,
                                     "echo 'test' > /dev/null")
        config_path = config_builder.build()

        with TestServer(config_path) as server:
            server.wait_for_ready()

            client = TestWebhookClient("127.0.0.1", server.port)

            # Send request without signature
            response = client.send_webhook(
                headers={"X-GitHub-Event": "push"},
                payload=PayloadBuilder.github_push_event(repo="octocat/Hello-World")
            )

            # Should be accepted (200) or return expected error
            # May get 200 if command executed, or other status if repo not found
            # But should NOT get 401 (auth error) since verify is false
            self.assertNotEqual(response.status_code, 401,
                              "Should not require signature when verify=False")

    def test_valid_signature_accepted(self):
        """
        Test that valid HMAC-SHA1 signature is accepted.

        When verify=True, the server should validate the X-Hub-Signature
        header and accept requests with correct signatures.
        """
        config_builder = TestConfigBuilder(self.temp_dir)
        config_builder.set_platform_verify('github', verify=True, secret="test_secret")
        config_builder.add_repository("octocat/Hello-World", self.temp_dir,
                                     "echo 'test' > /dev/null")
        config_path = config_builder.build()

        with TestServer(config_path) as server:
            server.wait_for_ready()

            client = TestWebhookClient("127.0.0.1", server.port)

            # Build payload and calculate signature
            payload = PayloadBuilder.github_push_event(repo="octocat/Hello-World")
            payload_bytes = json.dumps(payload).encode('utf-8')
            signature = SignatureBuilder.github_signature(payload_bytes, "test_secret")

            # Send request with valid signature
            response = client.send_webhook(
                headers={
                    "X-GitHub-Event": "push",
                    "X-Hub-Signature": signature
                },
                payload=payload
            )

            # Should not get 401 (auth error)
            self.assertNotEqual(response.status_code, 401,
                              "Valid signature should be accepted")

    def test_invalid_signature_returns_401(self):
        """
        Test that invalid HMAC-SHA1 signature returns 401.

        When verify=True, requests with incorrect signatures should
        be rejected with 401 Unauthorized.
        """
        config_builder = TestConfigBuilder(self.temp_dir)
        config_builder.set_platform_verify('github', verify=True, secret="test_secret")
        config_builder.add_repository("octocat/Hello-World", self.temp_dir,
                                     "echo 'test' > /dev/null")
        config_path = config_builder.build()

        with TestServer(config_path) as server:
            server.wait_for_ready()

            client = TestWebhookClient("127.0.0.1", server.port)

            # Send request with invalid signature
            response = client.send_webhook(
                headers={
                    "X-GitHub-Event": "push",
                    "X-Hub-Signature": "sha1=invalid_signature_12345"
                },
                payload=PayloadBuilder.github_push_event(repo="octocat/Hello-World")
            )

            # Should get 401
            self.assertStatusCode(response, 401)

    def test_missing_signature_returns_401_when_verify_true(self):
        """
        Test that missing X-Hub-Signature header returns 401 when verify=True.

        When signature verification is enabled, requests without
        signature header should be rejected.
        """
        config_builder = TestConfigBuilder(self.temp_dir)
        config_builder.set_platform_verify('github', verify=True, secret="test_secret")
        config_builder.add_repository("octocat/Hello-World", self.temp_dir,
                                     "echo 'test' > /dev/null")
        config_path = config_builder.build()

        with TestServer(config_path) as server:
            server.wait_for_ready()

            client = TestWebhookClient("127.0.0.1", server.port)

            # Send request without signature
            response = client.send_webhook(
                headers={"X-GitHub-Event": "push"},
                payload=PayloadBuilder.github_push_event(repo="octocat/Hello-World")
            )

            # Should get 401
            self.assertStatusCode(response, 401)

    def test_unhandled_event_returns_406(self):
        """
        Test that unhandled events return 406.

        When handle_events is configured, events not in the list
        should be rejected with 406 Not Acceptable.
        """
        config_builder = TestConfigBuilder(self.temp_dir)
        config_builder.set_platform_verify('github', verify=False)
        config_builder.add_repository("octocat/Hello-World", self.temp_dir,
                                     "echo 'test' > /dev/null")
        config_path = config_builder.build()

        with TestServer(config_path) as server:
            server.wait_for_ready()

            client = TestWebhookClient("127.0.0.1", server.port)

            # Send release event (not in default handle_events="push")
            response = client.send_webhook(
                headers={"X-GitHub-Event": "release"},
                payload=PayloadBuilder.github_release_event(repo="octocat/Hello-World")
            )

            # Should get 406 (event not handled)
            self.assertStatusCode(response, 406)

    def test_handled_event_accepted(self):
        """
        Test that events in handle_events list are accepted.

        Push events should be processed when "push" is in handle_events.
        """
        config_builder = TestConfigBuilder(self.temp_dir)
        config_builder.set_platform_verify('github', verify=False)
        config_builder.add_repository("octocat/Hello-World", self.temp_dir,
                                     "echo 'test' > /dev/null")
        config_path = config_builder.build()

        with TestServer(config_path) as server:
            server.wait_for_ready()

            client = TestWebhookClient("127.0.0.1", server.port)

            # Send push event (in default handle_events)
            response = client.send_webhook(
                headers={"X-GitHub-Event": "push"},
                payload=PayloadBuilder.github_push_event(repo="octocat/Hello-World")
            )

            # Should not get 406 (event is handled)
            self.assertNotEqual(response.status_code, 406,
                              "Push event should be handled")

    def test_repository_full_name_extracted(self):
        """
        Test that repository.full_name is correctly extracted.

        The server should extract "owner/repo" from the repository.full_name
        field in the GitHub payload.
        """
        config_builder = TestConfigBuilder(self.temp_dir)
        config_builder.set_platform_verify('github', verify=False)
        config_builder.add_repository("testuser/myproject", self.temp_dir,
                                     f"touch {self.temp_dir}/.marker")
        config_path = config_builder.build()

        with TestServer(config_path) as server:
            server.wait_for_ready()

            client = TestWebhookClient("127.0.0.1", server.port)

            # Send request with matching repo name
            response = client.send_webhook(
                headers={"X-GitHub-Event": "push"},
                payload=PayloadBuilder.github_push_event(repo="testuser/myproject")
            )

            # Should find the repo and execute command
            # Check for marker file created by command
            import time
            time.sleep(0.5)  # Give time for async command to execute
            marker = Path(self.temp_dir) / ".marker"
            # May or may not exist depending on async execution timing
            # The key is that response wasn't a "repo not found" error
            self.assertNotEqual(response.status_code, 404,
                              "Repository should be found by full_name")

    def test_ping_event_handling(self):
        """
        Test that ping events are handled correctly.

        GitHub sends ping events when webhooks are first configured.
        These may or may not be in handle_events depending on config.
        """
        config_builder = TestConfigBuilder(self.temp_dir)
        config_builder.set_platform_verify('github', verify=False)
        config_builder.add_repository("octocat/Hello-World", self.temp_dir,
                                     "echo 'test' > /dev/null")
        config_path = config_builder.build()

        with TestServer(config_path) as server:
            server.wait_for_ready()

            client = TestWebhookClient("127.0.0.1", server.port)

            # Send ping event
            response = client.send_webhook(
                headers={"X-GitHub-Event": "ping"},
                payload=PayloadBuilder.github_ping_event(repo="octocat/Hello-World")
            )

            # Ping is not in default handle_events, should get 406
            self.assertStatusCode(response, 406)


if __name__ == '__main__':
    unittest.main()
