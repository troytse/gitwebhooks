"""
Server Manager for git-webhooks-server Testing

This module provides a TestServer class for managing the git-webhooks-server
in test environments. It handles starting, stopping, and monitoring the server.
"""

import sys
import time
import threading
import configparser
import logging
from pathlib import Path
from typing import Optional

# Add project root to path for importing gitwebhooks module
_project_root = Path(__file__).parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

# Import from gitwebhooks package
from gitwebhooks.server import WebhookServer
from gitwebhooks.handlers.request import WebhookRequestHandler


class TestServer:
    """
    Test server manager for git-webhooks-server.

    This class manages the HTTP server in a background thread for testing.
    It provides methods to start, stop, and monitor the server state.

    Usage:
        server = TestServer(config_path="/path/to/test.ini")
        server.start()
        server.wait_for_ready()
        # Run tests...
        server.stop()

    Context manager usage:
        with TestServer(config_path="/path/to/test.ini") as server:
            server.wait_for_ready()
            # Run tests...
    """

    def __init__(self, config_path: str, port: Optional[int] = None):
        """
        Initialize test server.

        Args:
            config_path: Path to configuration file
            port: Override port (None to use config file port)
        """
        self.config_path = config_path
        self._port_override = port
        self._server = None
        self._thread = None
        self._running = False
        self._ready_event = threading.Event()
        self._config = None

        # Load config immediately to know the port before starting
        if port is not None:
            self._port = port
        else:
            # Read config to get the port
            config = configparser.ConfigParser()
            config.read(config_path)
            self._port = config.getint('server', 'port', fallback=6789)

    @property
    def port(self) -> int:
        """
        Get the server port.

        Returns:
            int: Server port number
        """
        return self._port

    @property
    def is_running(self) -> bool:
        """
        Check if server is currently running.

        Returns:
            bool: True if server is running
        """
        return self._running and self._thread is not None and self._thread.is_alive()

    def _load_config(self) -> configparser.ConfigParser:
        """
        Load configuration file.

        Returns:
            ConfigParser: Loaded configuration
        """
        config = configparser.ConfigParser()
        config.read(self.config_path)
        return config

    def _create_server(self):
        """
        Create and configure the HTTP server.

        The server is created but not started. The actual serve_forever()
        call happens in the background thread.
        """
        from http.server import HTTPServer

        # Load config
        self._config = self._load_config()

        # Apply port override if specified
        if self._port_override:
            if not self._config.has_section('server'):
                self._config.add_section('server')
            self._config.set('server', 'port', str(self._port_override))

        # Write temporary config file for WebhookServer
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as f:
            self._config.write(f)
            self._temp_config_path = f.name

        # Create WebhookServer instance
        webhook_server = WebhookServer(self._temp_config_path)

        # Get server address and port
        address = self._config.get('server', 'address', fallback='127.0.0.1')
        port = self._config.getint('server', 'port', fallback=6789)

        # Initialize logging (to suppress output during tests)
        log_file = self._config.get('server', 'log_file', fallback='')
        if log_file:
            logging.basicConfig(
                level=logging.WARNING,  # Reduce noise during tests
                filename=log_file if Path(log_file).parent.exists() else None,
                format='%(asctime)s %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        else:
            logging.basicConfig(level=logging.WARNING)

        # Create HTTP server using WebhookServer's create_http_server method
        self._server = webhook_server.create_http_server()

    def _server_thread(self):
        """
        Background thread function that runs the server.

        Sets the ready event when server is accepting connections.
        """
        self._running = True
        try:
            # Set ready event AFTER server starts listening
            self._ready_event.set()
            self._server.serve_forever()
        except Exception:
            self._running = False
            self._ready_event.clear()
            raise

    def start(self):
        """
        Start the server in a background thread.

        Raises:
            RuntimeError: If server is already running
            OSError: If port is already in use
        """
        if self.is_running:
            raise RuntimeError("Server is already running")

        # Reset ready event
        self._ready_event.clear()

        # Create server
        self._create_server()

        # Start server in background thread
        self._thread = threading.Thread(target=self._server_thread, daemon=True)
        self._thread.start()

    def stop(self):
        """
        Stop the server.

        Waits for the server thread to finish.
        """
        if self._server:
            self._server.shutdown()
            self._server.server_close()

        if self._thread:
            self._thread.join(timeout=5)
            if self._thread.is_alive():
                # Thread didn't shut down gracefully
                pass

        # Clean up temporary config file
        if hasattr(self, '_temp_config_path'):
            try:
                import os
                os.unlink(self._temp_config_path)
            except Exception:
                pass

        self._running = False
        self._ready_event.clear()

    def wait_for_ready(self, timeout: float = 10.0) -> bool:
        """
        Wait for server to be ready to accept connections.

        Args:
            timeout: Maximum time to wait in seconds

        Returns:
            bool: True if server is ready, False if timeout
        """
        import socket
        import time

        start_time = time.time()

        # First wait for the ready event (server thread started)
        if not self._ready_event.wait(timeout=timeout):
            return False

        # Give server a bit more time to actually start listening
        time.sleep(0.2)

        # Then verify port is actually accepting connections
        port = self.port
        end_time = start_time + timeout

        while time.time() < end_time:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(0.1)
                    result = s.connect_ex(('127.0.0.1', port))
                    if result == 0:
                        # Give a small extra delay for server to be fully ready
                        time.sleep(0.05)
                        return True
            except Exception:
                pass
            time.sleep(0.1)

        return False

    def __enter__(self):
        """Context manager entry - starts the server."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - stops the server."""
        self.stop()


class TestServerProcess:
    """
    Alternative test server manager that runs the server in a subprocess.

    This approach provides better isolation but is slower than the
    thread-based approach. Use this when you need complete isolation
    between tests.

    Usage:
        server = TestServerProcess(config_path="/path/to/test.ini")
        server.start()
        server.wait_for_ready()
        # Run tests...
        server.stop()
    """

    def __init__(self, config_path: str, port: Optional[int] = None):
        """
        Initialize test server process.

        Args:
            config_path: Path to configuration file
            port: Override port (None to use config file port)
        """
        self.config_path = config_path
        self._port_override = port
        self._process = None
        self._config = None

    @property
    def port(self) -> int:
        """
        Get the server port.

        Returns:
            int: Server port number
        """
        if self._port_override:
            return self._port_override
        if self._config:
            return self._config.getint('server', 'port')
        # Load config to get port
        config = configparser.ConfigParser()
        config.read(self.config_path)
        self._config = config
        return config.getint('server', 'port')

    @property
    def is_running(self) -> bool:
        """
        Check if server process is running.

        Returns:
            bool: True if process is running
        """
        return self._process is not None and self._process.poll() is None

    def start(self):
        """
        Start the server in a subprocess.

        Raises:
            RuntimeError: If server is already running
        """
        if self.is_running:
            raise RuntimeError("Server is already running")

        import subprocess

        # Build command using gitwebhooks-cli
        # The CLI wrapper expects to be run from project root
        project_root = Path(__file__).parent.parent.parent
        cli_script = project_root / "gitwebhooks-cli"
        cmd = [sys.executable, "-m", "gitwebhooks.cli", "-c", self.config_path]

        # Start process from project root directory
        self._process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE,
            cwd=str(project_root)
        )

    def stop(self):
        """
        Stop the server process.

        Sends SIGTERM and waits for process to finish.
        """
        if self._process:
            self._process.terminate()
            try:
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._process.kill()
                self._process.wait()

    def wait_for_ready(self, timeout: float = 5.0) -> bool:
        """
        Wait for server to be ready by checking if port is listening.

        Args:
            timeout: Maximum time to wait in seconds

        Returns:
            bool: True if server is ready, False if timeout
        """
        import socket

        start_time = time.time()
        port = self.port

        while time.time() - start_time < timeout:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(0.1)
                    result = s.connect_ex(('127.0.0.1', port))
                    if result == 0:
                        return True
            except Exception:
                pass
            time.sleep(0.1)

        return False

    def __enter__(self):
        """Context manager entry - starts the server."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - stops the server."""
        self.stop()
