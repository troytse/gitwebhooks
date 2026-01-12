"""
SSL Certificate Generator for git-webhooks-server Testing

This module provides a TestCertificate class for generating self-signed
SSL certificates for testing HTTPS connections.
"""

import os
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Optional, Tuple


class TestCertificate:
    """
    Self-signed SSL certificate generator for testing.

    This class creates temporary SSL certificates for use in HTTPS
    connection testing. Certificates are automatically cleaned up
    when the object is destroyed or cleanup() is called.

    Usage:
        cert = TestCertificate()
        cert.generate()
        # Use cert.cert_path and cert.key_path for SSL config
        cert.cleanup()

    Context manager usage:
        with TestCertificate() as cert:
            cert.generate()
            # Use certificate paths...
    """

    def __init__(self, temp_dir: Optional[str] = None):
        """
        Initialize certificate generator.

        Args:
            temp_dir: Directory for certificate files (uses temp if None)
        """
        self.temp_dir = temp_dir
        self._cert_path = None
        self._key_path = None
        self._managed_temp = False

    @property
    def cert_path(self) -> str:
        """
        Get certificate file path.

        Returns:
            str: Path to certificate file

        Raises:
            RuntimeError: If certificate has not been generated
        """
        if self._cert_path is None:
            raise RuntimeError("Certificate has not been generated")
        return self._cert_path

    @property
    def key_path(self) -> str:
        """
        Get private key file path.

        Returns:
            str: Path to private key file

        Raises:
            RuntimeError: If certificate has not been generated
        """
        if self._key_path is None:
            raise RuntimeError("Certificate has not been generated")
        return self._key_path

    def _check_openssl(self) -> bool:
        """
        Check if openssl command is available.

        Returns:
            bool: True if openssl is available
        """
        try:
            result = subprocess.run(
                ['openssl', 'version'],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def generate(self) -> Tuple[str, str]:
        """
        Generate self-signed SSL certificate.

        Creates a self-signed certificate valid for 1 day using openssl.
        Files are created in the configured temp directory.

        Returns:
            tuple: (cert_path, key_path) - Paths to certificate and key files

        Raises:
            RuntimeError: If openssl is not available
            subprocess.CalledProcessError: If certificate generation fails
        """
        if not self._check_openssl():
            raise RuntimeError(
                "openssl command not available. "
                "Install openssl to generate test certificates."
            )

        # Create temp directory if needed
        if self.temp_dir is None:
            self.temp_dir = tempfile.mkdtemp(prefix="git_webhook_cert_")
            self._managed_temp = True

        # Generate file paths
        self._key_path = os.path.join(self.temp_dir, "test.key")
        self._cert_path = os.path.join(self.temp_dir, "test.crt")

        # Generate certificate using openssl
        subprocess.run([
            'openssl', 'req', '-x509', '-newkey', 'rsa:2048',
            '-keyout', self._key_path,
            '-out', self._cert_path,
            '-days', '1',
            '-nodes',
            '-subj', '/CN=localhost/O=Test/C=US'
        ], check=True, capture_output=True)

        return self._cert_path, self._key_path

    def generate_with_subject(self, subject: str) -> Tuple[str, str]:
        """
        Generate certificate with custom subject.

        Args:
            subject: Certificate subject string (e.g., "/CN=example.com")

        Returns:
            tuple: (cert_path, key_path)
        """
        if not self._check_openssl():
            raise RuntimeError("openssl command not available")

        if self.temp_dir is None:
            self.temp_dir = tempfile.mkdtemp(prefix="git_webhook_cert_")
            self._managed_temp = True

        self._key_path = os.path.join(self.temp_dir, "test.key")
        self._cert_path = os.path.join(self.temp_dir, "test.crt")

        subprocess.run([
            'openssl', 'req', '-x509', '-newkey', 'rsa:2048',
            '-keyout', self._key_path,
            '-out', self._cert_path,
            '-days', '1',
            '-nodes',
            '-subj', subject
        ], check=True, capture_output=True)

        return self._cert_path, self._key_path

    def cleanup(self):
        """
        Clean up certificate files and temporary directory.

        This method is safe to call multiple times.
        """
        if self._cert_path and os.path.exists(self._cert_path):
            try:
                os.remove(self._cert_path)
            except OSError:
                pass
            self._cert_path = None

        if self._key_path and os.path.exists(self._key_path):
            try:
                os.remove(self._key_path)
            except OSError:
                pass
            self._key_path = None

        if self._managed_temp and self.temp_dir and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
            except OSError:
                pass
            self.temp_dir = None

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleans up files."""
        self.cleanup()

    def __del__(self):
        """Destructor - ensures cleanup."""
        self.cleanup()


def generate_cert_pair(temp_dir: str) -> Tuple[str, str]:
    """
    Convenience function to generate a certificate pair.

    Args:
        temp_dir: Directory for certificate files

    Returns:
        tuple: (cert_path, key_path)
    """
    cert = TestCertificate(temp_dir)
    return cert.generate()


def check_ssl_available() -> bool:
    """
    Check if SSL testing is available (openssl installed).

    Returns:
        bool: True if SSL testing is available
    """
    try:
        result = subprocess.run(
            ['openssl', 'version'],
            capture_output=True,
            timeout=5
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False
