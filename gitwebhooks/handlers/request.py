"""HTTP request handler

Handles webhook endpoint for HTTP POST requests.
"""

import json
import logging
from http.server import BaseHTTPRequestHandler
from typing import Dict, Optional
from urllib.parse import parse_qs

from gitwebhooks.models.provider import Provider
from gitwebhooks.models.request import WebhookRequest
from gitwebhooks.config.models import ProviderConfig, RepositoryConfig
from gitwebhooks.handlers.factory import HandlerFactory
from gitwebhooks.utils.constants import *
from gitwebhooks.utils.exceptions import *
from gitwebhooks.utils.executor import execute_deployment


class WebhookRequestHandler(BaseHTTPRequestHandler):
    """Webhook request handler

    Handles HTTP POST requests, verifies signatures, triggers deployment commands.
    """

    # Class variables: configuration injection
    _provider_configs: Dict[Provider, ProviderConfig] = {}
    _repository_configs: Dict[str, RepositoryConfig] = {}

    @classmethod
    def configure(cls, provider_configs: Dict[Provider, ProviderConfig],
                 repository_configs: Dict[str, RepositoryConfig]) -> None:
        """Configure handler class (dependency injection)

        Args:
            provider_configs: Provider configuration dictionary
            repository_configs: Repository configuration dictionary
        """
        cls._provider_configs = provider_configs
        cls._repository_configs = repository_configs

    def __init__(self, request, client_address, server):
        """Initialize request handler

        Args:
            request: HTTP request
            client_address: Client address
            server: Server instance
        """
        # Copy class-level config to instance (avoid shared state)
        self._provider_configs = self.__class__._provider_configs.copy()
        self._repository_configs = self.__class__._repository_configs.copy()
        super().__init__(request, client_address, server)

    def do_GET(self) -> None:
        """Handle GET request

        All GET requests return 403 Forbidden
        """
        self.send_error(HTTP_FORBIDDEN, MESSAGE_FORBIDDEN)

    def do_POST(self) -> None:
        """Handle POST request (webhook endpoint)

        Implementation flow:
        1. Parse request body
        2. Identify provider and event
        3. Create corresponding handler
        4. Verify signature
        5. Extract repository identifier
        6. Execute deployment command
        7. Send response

        All errors are caught and appropriate HTTP status codes are returned
        """
        try:
            # Step 1: Parse request body
            try:
                request = self._parse_request()
            except RequestParseError as e:
                logging.warning('Request parse failed: %s', e)
                self._send_error(HTTP_BAD_REQUEST, MESSAGE_BAD_REQUEST)
                return

            if request.post_data is None:
                logging.warning('Unsupported request format')
                self._send_error(HTTP_BAD_REQUEST, MESSAGE_BAD_REQUEST)
                return

            # Step 2: Identify provider
            provider = self._identify_provider(request)
            if provider is None:
                logging.warning('Unknown provider')
                self._send_error(HTTP_PRECONDITION_FAILED, MESSAGE_PRECONDITION_FAILED)
                return

            # Step 3: Create handler
            handler = HandlerFactory.from_handler_type(provider)

            # Steps 4-6: Process request
            try:
                provider_config = self._provider_configs.get(provider)
                if not provider_config:
                    raise UnsupportedProviderError(f'{provider} configuration not found')

                repo_name = handler.handle_request(request, provider_config)

            except (SignatureValidationError, UnsupportedEventError,
                   UnsupportedProviderError) as e:
                logging.warning('Webhook processing error: %s', e)
                if isinstance(e, SignatureValidationError):
                    self._send_error(HTTP_UNAUTHORIZED, MESSAGE_UNAUTHORIZED)
                elif isinstance(e, UnsupportedEventError):
                    self._send_error(HTTP_NOT_ACCEPTABLE, MESSAGE_NOT_ACCEPTABLE)
                else:
                    self._send_error(HTTP_PRECONDITION_FAILED, MESSAGE_PRECONDITION_FAILED)
                return

            # Step 7: Execute deployment command
            if repo_name:
                repo_config = self._repository_configs.get(repo_name)
                if not repo_config:
                    logging.warning('No repository configuration: %s', repo_name)
                    self._send_error(HTTP_NOT_FOUND, MESSAGE_NOT_FOUND)
                    return

                execute_deployment(repo_name, repo_config.cwd, repo_config.cmd)
                self._send_response(HTTP_OK)
            else:
                logging.warning('Repository information missing from payload')
                self._send_error(HTTP_NOT_FOUND, MESSAGE_NOT_FOUND)

        except Exception as e:
            logging.error('Unexpected error processing webhook: %s', e)
            self._send_error(HTTP_INTERNAL_SERVER_ERROR, MESSAGE_INTERNAL_SERVER_ERROR)

    def _parse_request(self) -> WebhookRequest:
        """Parse HTTP request

        Returns:
            WebhookRequest instance

        Raises:
            RequestParseError: Parsing failed
        """
        # Get Content-Type and Content-Length
        content_type = self.headers.get(HEADER_CONTENT_TYPE, '')
        content_length = int(self.headers.get(HEADER_CONTENT_LENGTH, 0))

        # Read request body
        if content_length == 0:
            raise RequestParseError('Empty request body')

        payload = self.rfile.read(content_length)

        # Parse POST data
        post_data = None
        if CONTENT_TYPE_JSON in content_type:
            try:
                post_data = json.loads(payload.decode('utf-8'))
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                raise RequestParseError(f'Invalid JSON: {e}')
        elif CONTENT_TYPE_FORM_URLENCODED in content_type:
            try:
                post_data = {k: v[0] if v else None for k, v in parse_qs(payload.decode('utf-8')).items()}
            except UnicodeDecodeError as e:
                raise RequestParseError(f'Invalid form data: {e}')

        # Identify provider and event
        provider, event = self._parse_provider_and_event()

        return WebhookRequest(
            provider=provider,
            event=event,
            payload=payload,
            headers=dict(self.headers),
            post_data=post_data,
            content_type=content_type,
            content_length=content_length
        )

    def _parse_provider_and_event(self) -> tuple:
        """Parse provider and event from request headers

        Returns:
            Tuple of (provider, event)

        Note:
            HTTP headers are case-insensitive per RFC 2616.
            Uses get() method which is case-insensitive for HTTPMessage.
        """
        # GitHub
        github_event = self.headers.get(HEADER_GITHUB_EVENT)
        if github_event is not None:
            return Provider.GITHUB, github_event

        # Gitee
        gitee_event = self.headers.get(HEADER_GITEE_EVENT)
        if gitee_event is not None:
            return Provider.GITEE, gitee_event

        # GitLab
        gitlab_event = self.headers.get(HEADER_GITLAB_EVENT)
        if gitlab_event is not None:
            return Provider.GITLAB, gitlab_event

        # Custom
        custom_config = self._provider_configs.get(Provider.CUSTOM)
        if custom_config and custom_config.header_name:
            header_value = self.headers.get(custom_config.header_name, '')
            if header_value and header_value.startswith(custom_config.header_value):
                event = self.headers.get(custom_config.header_event) if custom_config.header_event else None
                return Provider.CUSTOM, event

        # Unable to identify
        return None, None

    def _identify_provider(self, request: WebhookRequest) -> Optional[Provider]:
        """Identify provider from request

        Args:
            request: Webhook request

        Returns:
            Provider enum value, None if unable to identify
        """
        return request.provider

    def _send_response(self, status_code: int, message: bytes = MESSAGE_OK) -> None:
        """Send HTTP response

        Args:
            status_code: HTTP status code
            message: Response body
        """
        self.send_response(status_code)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write(message)

    def _send_error(self, status_code: int, message: str = '') -> None:
        """Send HTTP error response

        Args:
            status_code: HTTP status code
            message: Error message
        """
        self.send_error(status_code, message)

    def log_message(self, format: str, *args) -> None:
        """Override to prevent duplicate logging"""
        pass
