"""
Shared fixtures and configuration for gitwebhooks test suite.

This module provides common test fixtures used across all test modules.
"""

import tempfile
import socket
import shutil
from pathlib import Path
from typing import Generator

import unittest


def get_free_port() -> int:
    """
    Get a free port from the OS.

    Returns:
        int: A free port number
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        s.listen(1)
        port = s.getsockname()[1]
    return port


def temp_dir() -> Generator[str, None, None]:
    """
    Provide a temporary directory for testing.

    The directory is automatically cleaned up after the test.

    Yields:
        str: Path to temporary directory
    """
    temp = tempfile.mkdtemp(prefix="git_webhook_test_")
    try:
        yield temp
    finally:
        shutil.rmtree(temp, ignore_errors=True)


def free_port() -> Generator[int, None, None]:
    """
    Provide a free port for testing.

    Yields:
        int: A free port number
    """
    port = get_free_port()
    yield port
    # Port is released automatically when socket closes


def temp_config(content: str) -> Generator[str, None, None]:
    """
    Create a temporary config file with the given content.

    Args:
        content: INI config file content

    Yields:
        str: Path to temporary config file
    """
    temp = tempfile.NamedTemporaryFile(
        mode='w',
        suffix='.ini',
        prefix='test_config_',
        delete=False
    )
    try:
        temp.write(content)
        temp.flush()
        temp.close()
        yield temp.name
    finally:
        Path(temp.name).unlink(missing_ok=True)


def temp_log_file() -> Generator[str, None, None]:
    """
    Create a temporary log file for testing.

    Yields:
        str: Path to temporary log file
    """
    temp = tempfile.NamedTemporaryFile(
        suffix='.log',
        prefix='test_log_',
        delete=False
    )
    temp.close()
    try:
        yield temp.name
    finally:
        Path(temp.name).unlink(missing_ok=True)


def read_log_file(log_path: str) -> str:
    """
    Read content from a log file.

    Args:
        log_path: Path to log file

    Returns:
        str: Log file content
    """
    try:
        with open(log_path, 'r') as f:
            return f.read()
    except FileNotFoundError:
        return ""


# Default test configuration template
DEFAULT_TEST_CONFIG = """[server]
address = 127.0.0.1
port = {port}
log_file = {log_file}

[ssl]
enable = false

[github]
handle_events = push
verify = false
secret = test_secret

[gitee]
handle_events = Push Hook
verify = false
secret = test_secret

[gitlab]
handle_events = push
verify = false
secret = test_secret

[custom]
header_name = X-Custom-Header
header_value = Custom-Git-Hookshot
identifier_path = project.path_with_namespace
handle_events = push
verify = false
secret = test_secret

[test/repo1]
cwd = {temp_dir}/repo1
cmd = touch {temp_dir}/repo1/.test_marker && echo "success"
"""


class TestConfigBuilder:
    """
    Builder for creating test configuration files.

    Usage:
        builder = TestConfigBuilder(temp_dir)
        builder.add_repository("owner/repo", cwd, cmd)
        config_path = builder.build()
    """

    def __init__(self, temp_dir: str):
        """
        Initialize config builder.

        Args:
            temp_dir: Temporary directory for test files
        """
        self.temp_dir = temp_dir
        self.repositories = {}
        self.server_config = {}
        self.platform_config = {}
        self.ssl_config = {"enable": False}

    def add_repository(self, name: str, cwd: str, cmd: str) -> None:
        """
        Add a repository configuration.

        Args:
            name: Repository name (e.g., "owner/repo")
            cwd: Working directory
            cmd: Command to execute
        """
        self.repositories[name] = {"cwd": cwd, "cmd": cmd}

    def set_server_config(self, address: str = None, port: int = None,
                          log_file: str = None) -> None:
        """
        Set server configuration.

        Args:
            address: Server address
            port: Server port
            log_file: Log file path
        """
        if address:
            self.server_config["address"] = address
        if port:
            self.server_config["port"] = port
        if log_file:
            self.server_config["log_file"] = log_file

    def set_platform_verify(self, platform: str, verify: bool,
                            secret: str = "test_secret") -> None:
        """
        Set platform verification configuration.

        Args:
            platform: Platform name (github, gitee, gitlab, custom)
            verify: Whether to enable verification
            secret: Secret for verification
        """
        self.platform_config[platform] = {
            "verify": verify,
            "secret": secret
        }

    def enable_ssl(self, cert_path: str, key_path: str) -> None:
        """
        Enable SSL configuration.

        Args:
            cert_path: Certificate file path
            key_path: Private key file path
        """
        self.ssl_config = {
            "enable": True,
            "key_file": key_path,
            "cert_file": cert_path
        }

    def build(self, port: int = None) -> str:
        """
        Build the configuration file.

        Args:
            port: Override port (uses free port if not specified)

        Returns:
            str: Path to created config file
        """
        if port is None:
            port = get_free_port()

        # Build config content
        lines = []

        # Server section
        lines.append("[server]")
        lines.append(f"address = {self.server_config.get('address', '127.0.0.1')}")
        lines.append(f"port = {port}")
        log_file = self.server_config.get('log_file',
                                          f"{self.temp_dir}/test.log")
        lines.append(f"log_file = {log_file}")
        lines.append("")

        # SSL section
        lines.append("[ssl]")
        lines.append(f"enable = {str(self.ssl_config['enable']).lower()}")
        if self.ssl_config['enable']:
            lines.append(f"key_file = {self.ssl_config['key_file']}")
            lines.append(f"cert_file = {self.ssl_config['cert_file']}")
        lines.append("")

        # GitHub section
        github_config = self.platform_config.get('github', {})
        lines.append("[github]")
        lines.append("handle_events = push")
        lines.append(f"verify = {str(github_config.get('verify', False)).lower()}")
        lines.append(f"secret = {github_config.get('secret', 'test_secret')}")
        lines.append("")

        # Gitee section
        gitee_config = self.platform_config.get('gitee', {})
        lines.append("[gitee]")
        lines.append("handle_events = Push Hook")
        lines.append(f"verify = {str(gitee_config.get('verify', False)).lower()}")
        lines.append(f"secret = {gitee_config.get('secret', 'test_secret')}")
        lines.append("")

        # GitLab section
        gitlab_config = self.platform_config.get('gitlab', {})
        lines.append("[gitlab]")
        lines.append("handle_events = push")
        lines.append(f"verify = {str(gitlab_config.get('verify', False)).lower()}")
        lines.append(f"secret = {gitlab_config.get('secret', 'test_secret')}")
        lines.append("")

        # Custom section
        custom_config = self.platform_config.get('custom', {})
        lines.append("[custom]")
        lines.append("header_name = X-Custom-Header")
        lines.append("header_value = Custom-Git-Hookshot")
        lines.append("header_token = X-Custom-Token")
        lines.append("header_event = X-Custom-Event")
        lines.append("identifier_path = project.path_with_namespace")
        lines.append("handle_events = push")
        lines.append(f"verify = {str(custom_config.get('verify', False)).lower()}")
        lines.append(f"secret = {custom_config.get('secret', 'test_secret')}")
        lines.append("")

        # Repository sections
        for name, config in self.repositories.items():
            lines.append(f"[{name}]")
            lines.append(f"cwd = {config['cwd']}")
            lines.append(f"cmd = {config['cmd']}")
            lines.append("")

        content = "\n".join(lines)

        # Write to temp file
        import tempfile
        from pathlib import Path

        temp = tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.ini',
            prefix='test_config_',
            delete=False
        )
        temp.write(content)
        temp.flush()
        temp.close()

        return temp.name


# unittest.TestCase mixin for common test utilities
class WebhookTestCase(unittest.TestCase):
    """
    Base test class with common webhook test utilities.
    """

    def setUp(self):
        """Set up test fixtures."""
        self._temp_dirs = []
        self._temp_files = []

    def tearDown(self):
        """Clean up test fixtures."""
        for temp_dir in self._temp_dirs:
            shutil.rmtree(temp_dir, ignore_errors=True)
        for temp_file in self._temp_files:
            Path(temp_file).unlink(missing_ok=True)

    def create_temp_dir(self) -> str:
        """
        Create a temporary directory for testing.

        Returns:
            str: Path to temporary directory
        """
        temp_dir = tempfile.mkdtemp(prefix="git_webhook_test_")
        self._temp_dirs.append(temp_dir)
        return temp_dir

    def create_temp_file(self, suffix: str = "") -> str:
        """
        Create a temporary file for testing.

        Args:
            suffix: File suffix/extension

        Returns:
            str: Path to temporary file
        """
        temp_file = tempfile.NamedTemporaryFile(
            suffix=suffix,
            prefix="test_file_",
            delete=False
        )
        temp_file.close()
        self._temp_files.append(temp_file.name)
        return temp_file.name

    def assertStatusCode(self, response, expected: int):
        """
        Assert HTTP status code.

        Args:
            response: HTTP response object with status_code attribute
            expected: Expected status code
        """
        self.assertEqual(response.status_code, expected,
                        f"Expected status {expected}, got {response.status_code}")

    def assertRepositoryExecuted(self, repo_name: str, temp_dir: str):
        """
        Assert that repository command was executed.

        Args:
            repo_name: Repository name
            temp_dir: Temporary directory containing marker files
        """
        marker_path = Path(temp_dir) / f"{repo_name.replace('/', '_')}" / ".test_marker"
        self.assertTrue(marker_path.exists(),
                       f"Repository {repo_name} command did not execute (marker not found)")

    def assertLogFileContains(self, log_path: str, text: str):
        """
        Assert that log file contains specific text.

        Args:
            log_path: Path to log file
            text: Text to search for
        """
        content = read_log_file(log_path)
        self.assertIn(text, content,
                     f"Log file does not contain expected text: {text}")
