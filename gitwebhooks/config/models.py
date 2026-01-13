"""Configuration data models

Defines configuration-related dataclasses.
"""

import configparser
from dataclasses import dataclass
from pathlib import Path
from typing import List

from gitwebhooks.models.provider import Provider
from gitwebhooks.utils.exceptions import ConfigurationError


@dataclass
class ProviderConfig:
    """Git platform provider configuration

    Attributes:
        provider: Provider type
        verify: Whether to verify signature/token
        secret: Secret key for verification
        handle_events: List of events to handle (empty list = handle all events)
        header_name: Custom identification header (CUSTOM only)
        header_value: Custom identification value (CUSTOM only)
        header_event: Custom event header (CUSTOM only)
        header_token: Custom token header (CUSTOM only)
        identifier_path: Repository identifier JSON path (CUSTOM only)
    """
    provider: Provider
    verify: bool
    secret: str
    handle_events: List[str]

    # Custom provider only
    header_name: str = ''
    header_value: str = ''
    header_event: str = ''
    header_token: str = ''
    identifier_path: str = ''

    @classmethod
    def from_config_parser(cls, parser: configparser.ConfigParser,
                          provider: Provider) -> 'ProviderConfig':
        """Load provider configuration from ConfigParser

        Args:
            parser: ConfigParser instance
            provider: Provider type

        Returns:
            ProviderConfig instance

        Raises:
            configparser.NoSectionError: Configuration section does not exist
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

        # Custom provider additional fields
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

    def allows_event(self, event: str) -> bool:
        """Check if an event is allowed to be handled

        Args:
            event: Event type (None means all events)

        Returns:
            True if event is allowed, False otherwise
        """
        if not self.handle_events:
            return True  # Empty list = handle all events
        return event in self.handle_events


@dataclass
class RepositoryConfig:
    """Repository deployment configuration

    Attributes:
        name: Repository name (format: 'owner/repo' or 'group/project/repo')
        cwd: Working directory for deployment command execution
        cmd: Deployment command (shell string)
    """
    name: str
    cwd: str
    cmd: str

    @classmethod
    def from_config_parser(cls, parser: configparser.ConfigParser,
                          name: str):
        """Load repository configuration from ConfigParser

        Args:
            parser: ConfigParser instance
            name: Configuration section name (repository name)

        Returns:
            RepositoryConfig instance, or None if section does not exist

        Raises:
            configparser.NoOptionError: Section exists but missing required options
        """
        if not parser.has_section(name):
            return None

        return cls(
            name=name,
            cwd=parser.get(name, 'cwd'),
            cmd=parser.get(name, 'cmd')
        )

    def validate(self) -> None:
        """Validate configuration

        Raises:
            ConfigurationError: Configuration is invalid
        """
        if not self.cwd:
            raise ConfigurationError(f'Repository {self.name}: cwd is required')
        if not self.cmd:
            raise ConfigurationError(f'Repository {self.name}: cmd is required')
