"""
Unit Tests for Signature Verification (Phase 16)

Tests for verifying signature calculation and verification logic.
"""

import unittest
import sys
import json
import base64
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tests.fixtures.signature_builder import SignatureBuilder, sign_payload


class TestSignatureVerification(unittest.TestCase):
    """Test signature verification for all platforms."""

    def test_github_hmac_sha1_signature(self):
        """
        Test GitHub HMAC-SHA1 signature calculation.
        """
        payload = b'{"test": "data"}'
        secret = "test_secret"

        signature = SignatureBuilder.github_signature(payload, secret)

        # Should have sha1= prefix
        self.assertTrue(signature.startswith("sha1="))

        # Should be deterministic
        signature2 = SignatureBuilder.github_signature(payload, secret)
        self.assertEqual(signature, signature2)

    def test_github_signature_verification(self):
        """
        Test GitHub signature verification.
        """
        payload = b'{"test": "data"}'
        secret = "test_secret"

        correct_sig = SignatureBuilder.github_signature(payload, secret)

        # Correct signature should verify
        self.assertTrue(
            SignatureBuilder.verify_github_signature(payload, secret, correct_sig)
        )

        # Wrong signature should fail
        wrong_sig = "sha1=wrong1234567890abcdef"
        self.assertFalse(
            SignatureBuilder.verify_github_signature(payload, secret, wrong_sig)
        )

    def test_gitee_hmac_sha256_signature(self):
        """
        Test Gitee HMAC-SHA256 signature calculation.
        """
        payload = b'{"test": "data"}'
        secret = "test_secret"
        timestamp = 1705000000

        signature = SignatureBuilder.gitee_signature(payload, secret, timestamp)

        # Should be Base64 encoded
        import base64
        try:
            base64.b64decode(signature)
            is_valid_base64 = True
        except Exception:
            is_valid_base64 = False

        self.assertTrue(is_valid_base64)

    def test_gitee_signature_verification(self):
        """
        Test Gitee signature verification.
        """
        payload = b'{"test": "data"}'
        secret = "test_secret"
        timestamp = 1705000000

        correct_sig = SignatureBuilder.gitee_signature(payload, secret, timestamp)

        # Correct signature should verify
        self.assertTrue(
            SignatureBuilder.verify_gitee_signature(payload, secret, timestamp, correct_sig)
        )

        # Wrong signature should fail
        wrong_sig = base64.b64encode(b"wrong_signature").decode()
        self.assertFalse(
            SignatureBuilder.verify_gitee_signature(payload, secret, timestamp, wrong_sig)
        )

    def test_gitlab_token_comparison(self):
        """
        Test GitLab simple token comparison.
        """
        token = "test_token"

        # Token should be returned as-is
        result = SignatureBuilder.gitlab_token(token)
        self.assertEqual(result, token)

    def test_gitlab_token_verification(self):
        """
        Test GitLab token verification.
        """
        token = "test_token"

        # Correct token should verify
        self.assertTrue(
            SignatureBuilder.verify_gitlab_token(token, token)
        )

        # Wrong token should fail
        self.assertFalse(
            SignatureBuilder.verify_gitlab_token(token, "wrong_token")
        )

    def test_custom_token_comparison(self):
        """
        Test custom platform token comparison.
        """
        token = "custom_secret"

        result = SignatureBuilder.custom_token(token)
        self.assertEqual(result, token)

    def test_signature_mismatch_detection(self):
        """
        Test that signature mismatches are detected.
        """
        payload = b'{"test": "data"}'
        secret = "test_secret"

        # Generate signature with one secret
        sig1 = SignatureBuilder.github_signature(payload, secret)

        # Verify with different secret
        different_secret = "different_secret"
        sig2 = SignatureBuilder.github_signature(payload, different_secret)

        # Signatures should be different
        self.assertNotEqual(sig1, sig2)

        # sig1 should not verify with different secret's payload
        payload2 = b'{"different": "payload"}'
        self.assertFalse(
            SignatureBuilder.verify_github_signature(payload2, secret, sig1)
        )

    def test_sign_payload_convenience_function(self):
        """
        Test the sign_payload convenience function.
        """
        payload = b'{"test": "data"}'
        secret = "test_secret"

        # GitHub
        gh_sig = sign_payload('github', payload, secret)
        self.assertTrue(gh_sig.startswith("sha1="))

        # Gitee (needs timestamp)
        gt_sig = sign_payload('gitee', payload, secret, timestamp=1705000000)
        self.assertIsInstance(gt_sig, str)

        # GitLab
        gl_sig = sign_payload('gitlab', payload, secret)
        self.assertEqual(gl_sig, secret)

        # Custom
        cu_sig = sign_payload('custom', payload, secret)
        self.assertEqual(cu_sig, secret)

    def test_sign_payload_invalid_platform(self):
        """
        Test that invalid platform raises error.
        """
        payload = b'{"test": "data"}'
        secret = "test_secret"

        from tests.fixtures.signature_builder import SignatureError

        with self.assertRaises(SignatureError):
            sign_payload('invalid_platform', payload, secret)

    def test_github_signature_with_different_payloads(self):
        """
        Test that different payloads produce different signatures.
        """
        secret = "test_secret"

        payload1 = b'{"test": "data1"}'
        payload2 = b'{"test": "data2"}'

        sig1 = SignatureBuilder.github_signature(payload1, secret)
        sig2 = SignatureBuilder.github_signature(payload2, secret)

        self.assertNotEqual(sig1, sig2)

    def test_gitee_timestamp_affects_signature(self):
        """
        Test that different timestamps produce different Gitee signatures.
        """
        payload = b'{"test": "data"}'
        secret = "test_secret"

        sig1 = SignatureBuilder.gitee_signature(payload, secret, 1705000000)
        sig2 = SignatureBuilder.gitee_signature(payload, secret, 1705000001)

        self.assertNotEqual(sig1, sig2)


if __name__ == '__main__':
    unittest.main()
