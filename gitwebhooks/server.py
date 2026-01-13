"""HTTP server main logic

Creates and runs the HTTP server, handles webhook requests.
"""

import logging
import ssl
import sys
from http.server import HTTPServer
from typing import Optional

from gitwebhooks.config.loader import ConfigLoader
from gitwebhooks.config.registry import ConfigurationRegistry
from gitwebhooks.config.server import ServerConfig
from gitwebhooks.handlers.request import WebhookRequestHandler
from gitwebhooks.logging.setup import setup_logging
from gitwebhooks.utils.exceptions import ConfigurationError


class WebhookServer:
    """Git Webhooks server main class

    Responsible for creating and running the HTTP server, handling webhook requests.
    """

    def __init__(self, config_path: str,
                 registry: Optional[ConfigurationRegistry] = None):
        """Initialize Webhook server

        Args:
            config_path: INI configuration file path
            registry: Configuration registry (optional, for dependency injection)

        Raises:
            ConfigurationError: Invalid or missing configuration
        """
        self.config_path = config_path
        self.loader = ConfigLoader(config_path)
        self.registry = registry or ConfigurationRegistry(self.loader)
        self.server_config = self.registry.server_config

        # Configure logging
        self._setup_logging()

    def _setup_logging(self) -> None:
        """Configure logging system

        Sets up logging based on server configuration:
        - If log_file is empty, output to stdout only
        - If log_file is non-empty, output to both file and stdout

        Raises:
            ConfigurationError: Log file cannot be created
        """
        setup_logging(self.server_config.log_file)

    def create_http_server(self) -> HTTPServer:
        """Create HTTP server instance

        Returns:
            Configured HTTPServer instance

        Raises:
            ConfigurationError: Invalid server configuration
            OSError: Failed to bind address
        """
        # Configure handler class (inject dependencies)
        WebhookRequestHandler.configure(
            self.registry.provider_configs,
            self.registry.repository_configs
        )

        # Create server
        server = HTTPServer(
            (self.server_config.address, self.server_config.port),
            WebhookRequestHandler
        )

        # Configure SSL (if enabled)
        if self.server_config.ssl_enabled:
            server.socket = self._wrap_socket_ssl(server.socket)

        return server

    def _wrap_socket_ssl(self, socket):
        """Wrap socket with SSL

        Args:
            socket: Raw socket

        Returns:
            SSL-wrapped socket

        Raises:
            ConfigurationError: Invalid SSL configuration
            ssl.SSLError: SSL initialization failed
        """
        try:
            context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            context.load_cert_chain(
                certfile=self.server_config.ssl_cert_file,
                keyfile=self.server_config.ssl_key_file
            )
            return context.wrap_socket(socket, server_side=True)
        except (ssl.SSLError, OSError) as e:
            raise ConfigurationError(f'SSL configuration error: {e}')

    def run(self) -> None:
        """Start server main loop

        This method blocks until the server is stopped.
        """
        server = self.create_http_server()

        ssl_message = ' with SSL' if self.server_config.ssl_enabled else ''
        logging.info('Serving on %s port %d%s...',
                    self.server_config.address,
                    self.server_config.port,
                    ssl_message)

        try:
            server.serve_forever()
        except KeyboardInterrupt:
            logging.info('Server stopped by user')
            server.shutdown()
        except Exception as e:
            logging.error('Server error: %s', e)
            raise
