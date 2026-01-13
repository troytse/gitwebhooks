#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Git Webhooks Server - Automated deployment webhook handler.

This server receives webhook events from Git platforms (Github, Gitee, Gitlab)
and triggers deployment commands configured in INI files.

Example:
    python3 git-webhooks-server.py -c /path/to/config.ini
"""

import base64
import configparser
import getopt
import hashlib
import hmac
import json
import logging
import ssl
import subprocess
import sys
from dataclasses import dataclass
from enum import Enum, unique
from http.server import BaseHTTPRequestHandler, HTTPServer
from os import path
from typing import Any, Dict, Optional, Tuple


# =============================================================================
# Constants
# =============================================================================

# HTTP Status Codes
HTTP_OK = 200
HTTP_BAD_REQUEST = 400
HTTP_UNAUTHORIZED = 401
HTTP_FORBIDDEN = 403
HTTP_NOT_FOUND = 404
HTTP_NOT_ACCEPTABLE = 406
HTTP_PRECONDITION_FAILED = 412
HTTP_INTERNAL_SERVER_ERROR = 500

# HTTP Content Types
CONTENT_TYPE_JSON = 'application/json'
CONTENT_TYPE_FORM_URLENCODED = 'application/x-www-form-urlencoded'

# HTTP Headers
HEADER_CONTENT_TYPE = 'Content-Type'
HEADER_CONTENT_LENGTH = 'Content-Length'
HEADER_GITHUB_EVENT = 'X-GitHub-Event'
HEADER_GITHUB_SIGNATURE = 'X-Hub-Signature'
HEADER_GITEE_EVENT = 'X-Gitee-Event'
HEADER_GITEE_TOKEN = 'X-Gitee-Token'
HEADER_GITEE_TIMESTAMP = 'X-Gitee-Timestamp'
HEADER_GITLAB_EVENT = 'X-Gitlab-Event'
HEADER_GITLAB_TOKEN = 'X-Gitlab-Token'

# Response Messages
MESSAGE_OK = b'OK'
MESSAGE_FORBIDDEN = 'Forbidden'
MESSAGE_BAD_REQUEST = 'Bad Request'
MESSAGE_UNAUTHORIZED = 'Unauthorized'
MESSAGE_NOT_FOUND = 'Not Found'
MESSAGE_NOT_ACCEPTABLE = 'Not Acceptable'
MESSAGE_PRECONDITION_FAILED = 'Precondition Failed'
MESSAGE_INTERNAL_SERVER_ERROR = 'Internal Server Error'


# =============================================================================
# Custom Exceptions
# =============================================================================

class WebhookError(Exception):
    """Base exception for webhook processing errors."""

    pass


class SignatureValidationError(WebhookError):
    """Raised when signature verification fails."""

    pass


class UnsupportedEventError(WebhookError):
    """Raised when event type is not configured for handling."""

    pass


class UnsupportedProviderError(WebhookError):
    """Raised when provider cannot be identified."""

    pass


class ConfigurationError(WebhookError):
    """Raised when configuration is invalid or missing."""

    pass


class RequestParseError(WebhookError):
    """Raised when request parsing fails."""

    pass


# =============================================================================
# Provider Enum
# =============================================================================

@unique
class Provider(Enum):
    """Git platform provider types.

    Attributes:
        GITHUB: Github platform
        GITEE: Gitee platform
        GITLAB: Gitlab platform
        CUSTOM: Custom webhook platform
    """

    GITHUB = 'github'
    GITEE = 'gitee'
    GITLAB = 'gitlab'
    CUSTOM = 'custom'


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class SignatureVerificationResult:
    """Result of signature verification.

    Attributes:
        is_valid: True if verification passed, False otherwise
        error_message: Error description if verification failed, None otherwise
    """

    is_valid: bool
    error_message: Optional[str] = None

    @classmethod
    def success(cls) -> 'SignatureVerificationResult':
        """Create a successful verification result.

        Returns:
            SignatureVerificationResult with is_valid=True
        """
        return cls(is_valid=True)

    @classmethod
    def failure(cls, message: str) -> 'SignatureVerificationResult':
        """Create a failed verification result.

        Args:
            message: Error description

        Returns:
            SignatureVerificationResult with is_valid=False and error message
        """
        return cls(is_valid=False, error_message=message)


@dataclass
class ProviderConfig:
    """Configuration for a Git platform provider.

    Attributes:
        provider: The provider type
        verify: Whether to verify signatures/tokens
        secret: Secret key for verification
        handle_events: List of events to handle (empty = all events)
        header_name: Custom header name for identification (custom provider only)
        header_value: Custom header value for identification (custom provider only)
        header_event: Custom event header name (custom provider only)
        header_token: Custom token header name (custom provider only)
        identifier_path: JSON path to repository identifier (custom provider only)
    """

    provider: Provider
    verify: bool
    secret: str
    handle_events: list
    header_name: str = ''
    header_value: str = ''
    header_event: str = ''
    header_token: str = ''
    identifier_path: str = ''

    @classmethod
    def from_config_parser(cls, parser: configparser.ConfigParser,
                          provider: Provider) -> 'ProviderConfig':
        """Load provider configuration from ConfigParser.

        Args:
            parser: ConfigParser instance
            provider: Provider type to load

        Returns:
            ProviderConfig instance
        """
        section = provider.value
        handle_events_str = parser.get(section, 'handle_events',
                                       fallback='').strip()
        handle_events = [e.strip() for e in handle_events_str.split(',')
                        if e.strip()] if handle_events_str else []

        config = cls(
            provider=provider,
            verify=parser.getboolean(section, 'verify', fallback=False),
            secret=parser.get(section, 'secret', fallback=''),
            handle_events=handle_events
        )

        # Additional fields for custom provider
        if provider == Provider.CUSTOM:
            config.header_name = parser.get(section, 'header_name',
                                           fallback='X-Custom-Webhook')
            config.header_value = parser.get(section, 'header_value',
                                            fallback='custom')
            config.header_event = parser.get(section, 'header_event',
                                            fallback='X-Custom-Event')
            config.header_token = parser.get(section, 'header_token',
                                            fallback='X-Custom-Token')
            config.identifier_path = parser.get(section, 'identifier_path',
                                               fallback='')

        return config


@dataclass
class RepositoryConfig:
    """Configuration for a repository deployment.

    Attributes:
        name: Repository name (e.g., 'owner/repo')
        cwd: Working directory for command execution
        cmd: Shell command to execute on webhook
    """

    name: str
    cwd: str
    cmd: str

    @classmethod
    def from_config_parser(cls, parser: configparser.ConfigParser,
                          name: str) -> Optional['RepositoryConfig']:
        """Load repository configuration from ConfigParser.

        Args:
            parser: ConfigParser instance
            name: Repository name (section name in config)

        Returns:
            RepositoryConfig instance, or None if section doesn't exist

        Raises:
            configparser.NoOptionError: If section exists but required options are missing
        """
        if not parser.has_section(name):
            return None

        # This will raise NoOptionError if required options are missing
        # We let it propagate to be handled as a 500 error
        return cls(
            name=name,
            cwd=parser.get(name, 'cwd'),
            cmd=parser.get(name, 'cmd')
        )


@dataclass
class WebhookRequest:
    """Parsed webhook request data.

    Attributes:
        provider: Git platform provider
        event: Event type (e.g., 'push', 'merge_request')
        payload: Raw request body bytes
        headers: HTTP request headers
        post_data: Parsed JSON/form data
        content_type: Content-Type header value
        content_length: Content-Length header value
    """

    provider: Provider
    event: Optional[str]
    payload: bytes
    headers: Dict[str, str]
    post_data: Optional[Dict[str, Any]]
    content_type: str
    content_length: int

    @property
    def repo_identifier(self) -> Optional[str]:
        """Extract repository identifier from post_data.

        Returns:
            Repository identifier (e.g., 'owner/repo'), or None if not found
        """
        if self.post_data is None:
            return None

        extractors = {
            Provider.GITHUB: lambda d: d.get('repository', {}).get('full_name'),
            Provider.GITEE: lambda d: d.get('repository', {}).get('full_name'),
            Provider.GITLAB: lambda d: d.get('project', {}).get('path_with_namespace'),
        }

        extractor = extractors.get(self.provider)
        if extractor:
            result = extractor(self.post_data)
            return result if isinstance(result, str) else None

        # For custom provider, use identifier_path (handled elsewhere)
        return None


# =============================================================================
# WebhookServer - Main Application Class
# =============================================================================

class WebhookServer:
    """Git Webhooks Server main application.

    This class manages configuration, provider settings, and repository
    configurations. It creates HTTP server instances with proper handlers.
    """

    def __init__(self, config_path: str, address: str = '0.0.0.0',
                 port: int = 6789):
        """Initialize the webhook server.

        Args:
            config_path: Path to INI configuration file
            address: Server listening address (default: 0.0.0.0)
            port: Server listening port (default: 6789)

        Raises:
            ConfigurationError: If configuration file is invalid or missing
        """
        self.config_path = config_path
        self.config = self._load_config(config_path)
        self.address = address
        self.port = port
        self.provider_configs = self._load_provider_configs()
        self.repository_configs = self._load_repository_configs()
        self._setup_logging()

    def _load_config(self, config_path: str) -> configparser.ConfigParser:
        """Load configuration from INI file.

        Args:
            config_path: Path to configuration file

        Returns:
            ConfigParser instance

        Raises:
            ConfigurationError: If file cannot be read or parsed
        """
        parser = configparser.ConfigParser()
        try:
            parser.read(config_path)
            return parser
        except (configparser.Error, UnicodeDecodeError) as e:
            raise ConfigurationError(f'Failed to load config: {e}')

    def _load_provider_configs(self) -> Dict[Provider, ProviderConfig]:
        """Load all provider configurations.

        Returns:
            Dictionary mapping Provider to ProviderConfig
        """
        configs = {}
        for provider in Provider:
            try:
                configs[provider] = ProviderConfig.from_config_parser(
                    self.config, provider
                )
            except configparser.NoSectionError:
                # Provider section not in config, use defaults
                configs[provider] = ProviderConfig(
                    provider=provider,
                    verify=False,
                    secret='',
                    handle_events=[]
                )
        return configs

    def _load_repository_configs(self) -> Dict[str, RepositoryConfig]:
        """Load all repository configurations.

        Returns:
            Dictionary mapping repository name to RepositoryConfig
        """
        configs = {}
        reserved_sections = {'server', 'ssl', 'github', 'gitee', 'gitlab', 'custom'}

        for section in self.config.sections():
            if section not in reserved_sections:
                repo_config = RepositoryConfig.from_config_parser(
                    self.config, section
                )
                if repo_config is not None:
                    configs[section] = repo_config

        return configs

    def _setup_logging(self) -> None:
        """Configure logging based on configuration file.

        Raises:
            ConfigurationError: If log file configuration is invalid
        """
        log_file = self.config.get('server', 'log_file', fallback='').strip()

        if log_file:
            try:
                # Initialize log file
                with open(log_file, 'w', encoding='utf-8') as f:
                    pass
            except (IOError, OSError) as e:
                logging.warning('Cannot create log file %s: %s', log_file, e)
                log_file = ''

        logging.basicConfig(
            level=logging.DEBUG,
            filename=log_file if log_file else None,
            format='%(asctime)s %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        if log_file:
            logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))

    def create_handler_factory(self):
        """Create a factory function for request handlers.

        The factory configures the handler class with injected dependencies.

        Returns:
            The ConfiguredRequestHandler class (configured)
        """
        # Configure the handler class with our configs
        ConfiguredRequestHandler.configure(
            self.provider_configs,
            self.repository_configs
        )
        return ConfiguredRequestHandler

    def create_http_server(self) -> HTTPServer:
        """Create and configure HTTP server.

        Returns:
            Configured HTTPServer instance

        Raises:
            ConfigurationError: If server configuration is invalid
        """
        handler_factory = self.create_handler_factory()
        server = HTTPServer((self.address, self.port), handler_factory)

        # Configure SSL if enabled
        if self._is_ssl_enabled():
            server.socket = self._wrap_socket_ssl(server.socket)

        return server

    def _is_ssl_enabled(self) -> bool:
        """Check if SSL is enabled in configuration.

        Returns:
            True if SSL is enabled, False otherwise
        """
        try:
            return self.config.getboolean('ssl', 'enable')
        except (configparser.NoSectionError, ValueError):
            return False

    def _wrap_socket_ssl(self, socket):
        """Wrap socket with SSL.

        Args:
            socket: Socket to wrap

        Returns:
            SSL-wrapped socket

        Raises:
            ConfigurationError: If SSL configuration is invalid
        """
        try:
            key_file = self.config.get('ssl', 'key_file')
            cert_file = self.config.get('ssl', 'cert_file')
            return ssl.wrap_socket(
                socket,
                keyfile=key_file,
                certfile=cert_file,
                server_side=True
            )
        except (configparser.NoOptionError, ssl.SSLError, OSError) as e:
            raise ConfigurationError(f'SSL configuration error: {e}')

    def run(self) -> None:
        """Start the server main loop.

        This method blocks and runs the server indefinitely.
        """
        server = self.create_http_server()
        ssl_message = ' with SSL' if self._is_ssl_enabled() else ''
        logging.info('Serving on %s port %d%s...', self.address, self.port,
                    ssl_message)
        server.serve_forever()


# =============================================================================
# ConfiguredRequestHandler - HTTP Request Handler
# =============================================================================

class ConfiguredRequestHandler(BaseHTTPRequestHandler):
    """HTTP request handler with injected configuration.

    This handler processes webhook POST requests from Git platforms.

    For backward compatibility, this class can use:
    1. Injected configuration via class-level configure() method (new way)
    2. Global config variable (legacy way for tests)
    """

    # Class variables to hold injected configuration
    _provider_configs: Dict[Provider, ProviderConfig] = {}
    _repository_configs: Dict[str, RepositoryConfig] = {}

    @classmethod
    def configure(cls, provider_configs: Dict[Provider, ProviderConfig],
                 repository_configs: Dict[str, RepositoryConfig]) -> None:
        """Configure the handler with dependencies.

        Args:
            provider_configs: Provider configuration dictionary
            repository_configs: Repository configuration dictionary
        """
        cls._provider_configs = provider_configs
        cls._repository_configs = repository_configs

    def __init__(self, request, client_address, server):
        """Initialize the request handler.

        Configuration is loaded from class-level configs or global config.

        Args:
            request: HTTP request
            client_address: Client address tuple
            server: Server instance
        """
        # Initialize instance configs from class-level configs
        self._provider_configs = self.__class__._provider_configs.copy()
        self._repository_configs = self.__class__._repository_configs.copy()

        # If class-level configs are empty, load from global config (backward compatibility)
        if not self._provider_configs:
            self._provider_configs = self._load_provider_configs_from_global()

        if not self._repository_configs:
            self._repository_configs = self._load_repository_configs_from_global()

        super().__init__(request, client_address, server)

    def _load_provider_configs_from_global(self) -> Dict[Provider, ProviderConfig]:
        """Load provider configs from global config variable.

        Returns:
            Dictionary mapping Provider to ProviderConfig
        """
        configs = {}
        global config
        if config is None:
            return configs

        for provider in Provider:
            try:
                configs[provider] = ProviderConfig.from_config_parser(config, provider)
            except configparser.NoSectionError:
                configs[provider] = ProviderConfig(
                    provider=provider,
                    verify=False,
                    secret='',
                    handle_events=[]
                )
        return configs

    def _load_repository_configs_from_global(self) -> Dict[str, RepositoryConfig]:
        """Load repository configs from global config variable.

        Returns:
            Dictionary mapping repository name to RepositoryConfig
        """
        configs = {}
        global config
        if config is None:
            return configs

        reserved_sections = {'server', 'ssl', 'github', 'gitee', 'gitlab', 'custom'}

        for section in config.sections():
            if section not in reserved_sections:
                try:
                    repo_config = RepositoryConfig.from_config_parser(config, section)
                    if repo_config is not None:
                        configs[section] = repo_config
                except configparser.NoOptionError:
                    # Section exists but missing required options - skip for now
                    # Will be handled at runtime as 500 error
                    pass

        return configs

    def _parse_provider(self) -> Tuple[Optional[Provider], Optional[str]]:
        """Parse provider type and event from request headers.

        Returns:
            Tuple of (provider, event). Returns (None, None) if provider
            cannot be identified.

        Raises:
            UnsupportedProviderError: If provider configuration is invalid
        """
        # Github
        if HEADER_GITHUB_EVENT in self.headers:
            return Provider.GITHUB, self.headers.get(HEADER_GITHUB_EVENT)

        # Gitee
        if HEADER_GITEE_EVENT in self.headers:
            return Provider.GITEE, self.headers.get(HEADER_GITEE_EVENT)

        # Gitlab
        if HEADER_GITLAB_EVENT in self.headers:
            return Provider.GITLAB, self.headers.get(HEADER_GITLAB_EVENT)

        # Custom
        custom_config = self._provider_configs.get(Provider.CUSTOM)
        if custom_config and custom_config.header_name:
            header_value = self.headers.get(custom_config.header_name, '')
            if header_value.startswith(custom_config.header_value):
                event = None
                if custom_config.header_event:
                    event = self.headers.get(custom_config.header_event)
                return Provider.CUSTOM, event

        # Unknown provider
        return None, None

    def _parse_data(self) -> Tuple[bytes, Optional[Dict[str, Any]]]:
        """Parse request body content.

        Returns:
            Tuple of (payload, post_data). post_data is None if parsing fails.

        Raises:
            RequestParseError: If content type is not supported
        """
        content_type_header = self.headers.get(HEADER_CONTENT_TYPE, '')
        content_type = content_type_header.lower() if content_type_header else ''
        content_len = int(self.headers.get(HEADER_CONTENT_LENGTH, 0))
        payload = self.rfile.read(content_len)

        try:
            # JSON content
            if content_type.startswith(CONTENT_TYPE_JSON):
                decoded = payload.decode('utf-8')
                post_data = json.loads(decoded)
                return payload, post_data

            # Form encoded
            if content_type.startswith(CONTENT_TYPE_FORM_URLENCODED):
                from urllib.parse import parse_qs
                decoded = payload.decode('utf-8')
                data = parse_qs(decoded, keep_blank_values=True)
                if 'payload' in data:
                    try:
                        post_data = json.loads(data['payload'][0])
                        return payload, post_data
                    except (json.JSONDecodeError, IndexError, KeyError):
                        pass
                return payload, data

        except (UnicodeDecodeError, json.JSONDecodeError) as e:
            logging.warning('Request parse error: %s', e)
            raise RequestParseError(f'Failed to parse request: {e}')

        # Unsupported content type
        raise RequestParseError(f'Unsupported Content-Type: {content_type_header}')

    def _verify_github_signature(self, payload: bytes,
                                 provider_config: ProviderConfig) -> SignatureVerificationResult:
        """Verify Github webhook signature.

        Args:
            payload: Raw request body bytes
            provider_config: Provider configuration

        Returns:
            SignatureVerificationResult indicating success or failure
        """
        request_signature = self.headers.get(HEADER_GITHUB_SIGNATURE)

        if request_signature is None:
            return SignatureVerificationResult.failure('Missing signature')

        if not provider_config.secret:
            return SignatureVerificationResult.failure('Secret not configured')

        secret_bytes = provider_config.secret.encode('utf-8')
        expected_signature = 'sha1=' + hmac.new(
            secret_bytes, payload, hashlib.sha1
        ).hexdigest()

        if request_signature != expected_signature:
            return SignatureVerificationResult.failure('Invalid signature')

        return SignatureVerificationResult.success()

    def _verify_gitee_signature(self, payload: bytes,
                                provider_config: ProviderConfig) -> SignatureVerificationResult:
        """Verify Gitee webhook signature or password.

        Args:
            payload: Raw request body bytes
            provider_config: Provider configuration

        Returns:
            SignatureVerificationResult indicating success or failure
        """
        request_signature = self.headers.get(HEADER_GITEE_TOKEN)
        request_timestamp_str = self.headers.get(HEADER_GITEE_TIMESTAMP)

        if request_signature is None:
            return SignatureVerificationResult.failure('Missing signature or password')

        # Signature mode (with timestamp)
        if request_timestamp_str is not None:
            try:
                request_timestamp = int(request_timestamp_str)
            except ValueError:
                return SignatureVerificationResult.failure('Invalid timestamp format')

            payload_str = payload.decode('utf-8') if isinstance(payload, bytes) else payload
            sign_string = f'{request_timestamp}{payload_str}'
            secret_bytes = provider_config.secret.encode('utf-8')

            signature_bytes = hmac.new(
                secret_bytes, sign_string.encode('utf-8'), hashlib.sha256
            ).digest()
            expected_signature = base64.b64encode(signature_bytes).decode('utf-8')

            if request_signature != expected_signature:
                return SignatureVerificationResult.failure('Invalid signature')

            return SignatureVerificationResult.success()

        # Password mode (without timestamp)
        if request_signature != provider_config.secret:
            return SignatureVerificationResult.failure('Invalid password')

        return SignatureVerificationResult.success()

    def _verify_gitlab_token(self, provider_config: ProviderConfig) -> SignatureVerificationResult:
        """Verify Gitlab webhook token.

        Args:
            provider_config: Provider configuration

        Returns:
            SignatureVerificationResult indicating success or failure
        """
        request_token = self.headers.get(HEADER_GITLAB_TOKEN)

        if request_token != provider_config.secret:
            return SignatureVerificationResult.failure('Invalid token')

        return SignatureVerificationResult.success()

    def _verify_custom_token(self, provider_config: ProviderConfig) -> SignatureVerificationResult:
        """Verify custom webhook token.

        Args:
            provider_config: Provider configuration

        Returns:
            SignatureVerificationResult indicating success or failure
        """
        if not provider_config.header_token:
            return SignatureVerificationResult.success()

        request_token = self.headers.get(provider_config.header_token)

        if request_token != provider_config.secret:
            return SignatureVerificationResult.failure('Invalid token')

        return SignatureVerificationResult.success()

    def _extract_repository_name(self, provider: Provider,
                                 post_data: Dict[str, Any]) -> Optional[str]:
        """Extract repository identifier from webhook payload.

        Args:
            provider: Git platform provider
            post_data: Parsed webhook payload

        Returns:
            Repository identifier (e.g., 'owner/repo'), or None if not found
        """
        if provider == Provider.GITHUB:
            repo = post_data.get('repository', {})
            return repo.get('full_name') if isinstance(repo, dict) else None

        if provider == Provider.GITEE:
            repo = post_data.get('repository', {})
            return repo.get('full_name') if isinstance(repo, dict) else None

        if provider == Provider.GITLAB:
            project = post_data.get('project', {})
            return project.get('path_with_namespace') if isinstance(project, dict) else None

        if provider == Provider.CUSTOM:
            custom_config = self._provider_configs.get(Provider.CUSTOM)
            if custom_config and custom_config.identifier_path:
                path = custom_config.identifier_path.split('.')
                value = post_data
                for step in path:
                    if isinstance(value, dict) and step in value:
                        value = value[step]
                    else:
                        return None
                return value if isinstance(value, str) else None

        return None

    def _execute_deployment_command(self, repo_name: str,
                                   repo_config: RepositoryConfig) -> None:
        """Execute deployment command for repository.

        The command is executed asynchronously via subprocess.Popen.
        Errors are logged but do not raise exceptions, as the command
        runs in the background.

        Args:
            repo_name: Repository name
            repo_config: Repository configuration
        """
        logging.info('[%s] Executing: %s', repo_name, repo_config.cmd)

        try:
            subprocess.Popen(
                repo_config.cmd,
                cwd=repo_config.cwd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
        except (OSError, subprocess.SubprocessError) as e:
            # Log error but don't raise - command execution is async
            logging.warning('[%s] Execution failed: %s', repo_name, e)

    def _send_response(self, status_code: int, message: bytes = MESSAGE_OK) -> None:
        """Send HTTP response.

        Args:
            status_code: HTTP status code
            message: Response body bytes
        """
        self.send_response(status_code)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write(message)

    def _send_error(self, status_code: int, message: str = '') -> None:
        """Send HTTP error response.

        Args:
            status_code: HTTP status code
            message: Error message (optional, uses status code default if empty)
        """
        self.send_error(status_code, message)

    def _handle_github(self, provider: Provider, event: Optional[str],
                      payload: bytes, post_data: Dict[str, Any]) -> Optional[str]:
        """Handle Github webhook request.

        Args:
            provider: Provider type
            event: Event type
            payload: Raw request body
            post_data: Parsed webhook data

        Returns:
            Repository name if successful, None otherwise

        Raises:
            SignatureValidationError: If signature verification fails
            UnsupportedEventError: If event is not configured for handling
        """
        provider_config = self._provider_configs.get(provider)
        if not provider_config:
            raise UnsupportedProviderError('Github configuration not found')

        # Check if event is allowed
        if provider_config.handle_events and event not in provider_config.handle_events:
            raise UnsupportedEventError(f'Event not configured: {event}')

        # Verify signature if required
        if provider_config.verify:
            result = self._verify_github_signature(payload, provider_config)
            if not result.is_valid:
                raise SignatureValidationError(result.error_message or 'Signature verification failed')

        # Extract repository name
        return self._extract_repository_name(provider, post_data)

    def _handle_gitee(self, provider: Provider, event: Optional[str],
                      payload: bytes, post_data: Dict[str, Any]) -> Optional[str]:
        """Handle Gitee webhook request.

        Args:
            provider: Provider type
            event: Event type
            payload: Raw request body
            post_data: Parsed webhook data

        Returns:
            Repository name if successful, None otherwise

        Raises:
            SignatureValidationError: If signature/password verification fails
            UnsupportedEventError: If event is not configured for handling
        """
        provider_config = self._provider_configs.get(provider)
        if not provider_config:
            raise UnsupportedProviderError('Gitee configuration not found')

        # Check if event is allowed
        if provider_config.handle_events and event not in provider_config.handle_events:
            raise UnsupportedEventError(f'Event not configured: {event}')

        # Verify signature/password if required
        if provider_config.verify:
            result = self._verify_gitee_signature(payload, provider_config)
            if not result.is_valid:
                raise SignatureValidationError(result.error_message or 'Verification failed')
        else:
            # If verify=False but token is provided (no timestamp), still verify
            request_timestamp = self.headers.get(HEADER_GITEE_TIMESTAMP)
            request_signature = self.headers.get(HEADER_GITEE_TOKEN)
            if request_timestamp is None and request_signature:
                if request_signature != provider_config.secret:
                    raise SignatureValidationError('Invalid password')

        # Extract repository name
        return self._extract_repository_name(provider, post_data)

    def _handle_gitlab(self, provider: Provider, event: Optional[str],
                       payload: bytes, post_data: Dict[str, Any]) -> Optional[str]:
        """Handle Gitlab webhook request.

        Args:
            provider: Provider type
            event: Event type
            payload: Raw request body
            post_data: Parsed webhook data

        Returns:
            Repository name if successful, None otherwise

        Raises:
            SignatureValidationError: If token verification fails
            UnsupportedEventError: If event is not configured for handling
        """
        provider_config = self._provider_configs.get(provider)
        if not provider_config:
            raise UnsupportedProviderError('Gitlab configuration not found')

        # Check if event is allowed
        if provider_config.handle_events and event not in provider_config.handle_events:
            raise UnsupportedEventError(f'Event not configured: {event}')

        # Verify token if required
        if provider_config.verify:
            result = self._verify_gitlab_token(provider_config)
            if not result.is_valid:
                raise SignatureValidationError(result.error_message or 'Token verification failed')

        # Extract repository name
        return self._extract_repository_name(provider, post_data)

    def _handle_custom(self, provider: Provider, event: Optional[str],
                       payload: bytes, post_data: Dict[str, Any]) -> Optional[str]:
        """Handle custom webhook request.

        Args:
            provider: Provider type
            event: Event type
            payload: Raw request body
            post_data: Parsed webhook data

        Returns:
            Repository name if successful, None otherwise

        Raises:
            SignatureValidationError: If token verification fails
            UnsupportedEventError: If event is not configured for handling
        """
        provider_config = self._provider_configs.get(provider)
        if not provider_config:
            raise UnsupportedProviderError('Custom configuration not found')

        # Check if event is allowed
        if provider_config.handle_events and event not in provider_config.handle_events:
            raise UnsupportedEventError(f'Event not configured: {event}')

        # Verify token if header_token is configured
        if provider_config.header_token:
            result = self._verify_custom_token(provider_config)
            if not result.is_valid:
                raise SignatureValidationError(result.error_message or 'Token verification failed')

        # Extract repository name
        return self._extract_repository_name(provider, post_data)

    def _dispatch_to_provider(self, provider: Provider, event: Optional[str],
                              payload: bytes, post_data: Dict[str, Any]) -> Optional[str]:
        """Dispatch webhook request to appropriate provider handler.

        Args:
            provider: Git platform provider
            event: Event type
            payload: Raw request body
            post_data: Parsed webhook data

        Returns:
            Repository name if successful, None otherwise

        Raises:
            UnsupportedProviderError: If provider is not recognized
        """
        handlers = {
            Provider.GITHUB: self._handle_github,
            Provider.GITEE: self._handle_gitee,
            Provider.GITLAB: self._handle_gitlab,
            Provider.CUSTOM: self._handle_custom,
        }

        handler = handlers.get(provider)
        if not handler:
            raise UnsupportedProviderError(f'Unknown provider: {provider}')

        return handler(provider, event, payload, post_data)

    def do_GET(self) -> None:
        """Handle GET requests.

        All GET requests are rejected with 403 Forbidden.
        """
        self._send_error(HTTP_FORBIDDEN, MESSAGE_FORBIDDEN)

    def do_POST(self) -> None:
        """Handle POST requests (webhook endpoints).

        Processes webhook requests from Git platforms and triggers
        configured deployment commands.
        """
        try:
            # Parse request body first (to catch unsupported content types)
            try:
                payload, post_data = self._parse_data()
            except RequestParseError as e:
                logging.warning('Request parse failed: %s', e)
                self._send_error(HTTP_BAD_REQUEST, MESSAGE_BAD_REQUEST)
                return

            if post_data is None:
                logging.warning('Unsupported request format')
                self._send_error(HTTP_BAD_REQUEST, MESSAGE_BAD_REQUEST)
                return

            # Parse provider and event
            provider, event = self._parse_provider()
            if provider is None:
                logging.warning('Unknown provider')
                self._send_error(HTTP_PRECONDITION_FAILED, MESSAGE_PRECONDITION_FAILED)
                return

            # Dispatch to provider handler
            try:
                repo_name = self._dispatch_to_provider(provider, event, payload, post_data)
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

            # Execute deployment command
            if repo_name:
                repo_config = self._repository_configs.get(repo_name)
                if not repo_config:
                    # Check if repo section exists in global config
                    global config
                    if config and config.has_section(repo_name):
                        # Section exists but config wasn't loaded (missing options)
                        logging.error('Missing required config for %s', repo_name)
                        self._send_error(HTTP_INTERNAL_SERVER_ERROR, MESSAGE_INTERNAL_SERVER_ERROR)
                    else:
                        # Section doesn't exist
                        logging.warning('No repository configuration: %s', repo_name)
                        self._send_error(HTTP_NOT_FOUND, MESSAGE_NOT_FOUND)
                    return

                self._execute_deployment_command(repo_name, repo_config)
                self._send_response(HTTP_OK)
            else:
                logging.warning('Repository information missing from payload')
                self._send_error(HTTP_NOT_FOUND, MESSAGE_NOT_FOUND)

        except Exception as e:
            logging.error('Unexpected error processing webhook: %s', e)
            self._send_error(HTTP_INTERNAL_SERVER_ERROR, MESSAGE_INTERNAL_SERVER_ERROR)

    def log_message(self, format: str, *args) -> None:
        """Override to prevent duplicate logging."""
        pass


# =============================================================================
# Helper Functions
# =============================================================================

def print_help() -> None:
    """Print usage help information."""
    print('usage: git-webhooks-server.py -c <configuration_file>')
    sys.exit(0)


# =============================================================================
# Main Entry Point
# =============================================================================

def main(argv: list) -> None:
    """Main entry point for the webhook server.

    Args:
        argv: Command line arguments (excluding program name)

    Raises:
        SystemExit: On configuration error or user request
    """
    # Default configuration file
    conf_file = '/usr/local/etc/git-webhooks-server.ini'

    # Parse command line arguments
    try:
        opts, _ = getopt.getopt(argv, 'hc:', ['config='])
    except getopt.GetoptError:
        print_help()

    for opt, value in opts:
        if opt == '-h':
            print_help()
        elif opt in ('-c', '--config'):
            conf_file = value

    # Check configuration file exists
    if not path.exists(conf_file):
        print(f'Missing configuration file: {conf_file}')
        sys.exit(1)

    # Create and run server
    try:
        server = WebhookServer(config_path=conf_file)
        server.run()
    except ConfigurationError as e:
        print(f'Configuration error: {e}')
        sys.exit(1)
    except Exception as e:
        logging.error('Failed to start server: %s', e)
        sys.exit(1)


# =============================================================================
# Backward Compatibility
# =============================================================================

# Alias for backward compatibility with tests
RequestHandler = ConfiguredRequestHandler

# Global config for backward compatibility (set by test code)
config: Optional[configparser.ConfigParser] = None


if __name__ == '__main__':
    main(sys.argv[1:])
