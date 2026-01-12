"""
Unit Tests for Request Body Parsing (User Story 7)

Tests for verifying that the server correctly parses different request body formats.
"""

import unittest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tests.conftest import WebhookTestCase, TestConfigBuilder
from tests.utils.http_client import TestWebhookClient
from tests.utils.server_manager import TestServer


class TestDataParsing(WebhookTestCase):
    """Test request body parsing for different content types."""

    def setUp(self):
        """Set up test environment."""
        super().setUp()
        self.temp_dir = self.create_temp_dir()

    def test_application_json_parsed_correctly(self):
        """
        Test that application/json content type is parsed correctly.
        """
        config_builder = TestConfigBuilder(self.temp_dir)
        config_builder.set_platform_verify('github', verify=False)
        config_builder.add_repository("test/repo", self.temp_dir,
                                     "echo 'test' > /dev/null")
        config_path = config_builder.build()

        with TestServer(config_path) as server:
            server.wait_for_ready()

            client = TestWebhookClient("127.0.0.1", server.port)

            # Send valid JSON
            response = client.send_webhook(
                headers={
                    "X-GitHub-Event": "push",
                    "Content-Type": "application/json"
                },
                payload={"repository": {"full_name": "test/repo"}}
            )

            # Should not get 400 (parsing error)
            self.assertNotEqual(response.status_code, 400)

    def test_form_urlencoded_with_json_payload(self):
        """
        Test form-urlencoded with JSON in 'payload' field.

        Some platforms send JSON as a form field called 'payload'.
        """
        config_builder = TestConfigBuilder(self.temp_dir)
        config_builder.set_platform_verify('github', verify=False)
        config_builder.add_repository("test/repo", self.temp_dir,
                                     "echo 'test' > /dev/null")
        config_path = config_builder.build()

        with TestServer(config_path) as server:
            server.wait_for_ready()

            client = TestWebhookClient("127.0.0.1", server.port)

            import json
            json_data = json.dumps({"repository": {"full_name": "test/repo"}})

            response = client.send_form_urlencoded(
                headers={"X-GitHub-Event": "push"},
                data={"payload": json_data}
            )

            # Should parse the JSON from payload field
            self.assertNotEqual(response.status_code, 400)

    def test_form_urlencoded_non_json_returns_form_data(self):
        """
        Test that non-JSON form data is handled.
        """
        config_builder = TestConfigBuilder(self.temp_dir)
        config_builder.set_platform_verify('github', verify=False)
        config_path = config_builder.build()

        with TestServer(config_path) as server:
            server.wait_for_ready()

            client = TestWebhookClient("127.0.0.1", server.port)

            response = client.send_form_urlencoded(
                headers={"X-GitHub-Event": "push"},
                data={"key": "value", "another": "data"}
            )

            # Form data should be accepted (may get 404 for missing repo)
            self.assertNotEqual(response.status_code, 400)

    def test_unsupported_content_type_returns_400(self):
        """
        Test that unsupported content types return 400.
        """
        config_builder = TestConfigBuilder(self.temp_dir)
        config_path = config_builder.build()

        with TestServer(config_path) as server:
            server.wait_for_ready()

            client = TestWebhookClient("127.0.0.1", server.port)

            response = client.send_raw(
                "POST",
                "/",
                headers={"Content-Type": "text/xml"},
                body=b'<xml>data</xml>'
            )

            self.assertStatusCode(response, 400)

    def test_invalid_json_returns_400(self):
        """
        Test that malformed JSON returns 400.
        """
        config_builder = TestConfigBuilder(self.temp_dir)
        config_path = config_builder.build()

        with TestServer(config_path) as server:
            server.wait_for_ready()

            client = TestWebhookClient("127.0.0.1", server.port)

            response = client.send_raw(
                "POST",
                "/",
                headers={"Content-Type": "application/json"},
                body=b'{"invalid": json}'  # Missing quotes around json
            )

            self.assertStatusCode(response, 400)


if __name__ == '__main__':
    unittest.main()
