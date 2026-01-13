"""Configuration registry

Holds all configuration and provides access interface.
"""

from typing import Dict

from gitwebhooks.config.loader import ConfigLoader
from gitwebhooks.config.models import ProviderConfig, RepositoryConfig
from gitwebhooks.config.server import ServerConfig
from gitwebhooks.models.provider import Provider
from gitwebhooks.utils.exceptions import ConfigurationError


class ConfigurationRegistry:
    """Configuration registry

    Holds all configuration and provides access interface
    """

    def __init__(self, loader: ConfigLoader):
        """Initialize configuration registry

        Args:
            loader: Configuration loader instance
        """
        self.loader = loader
        self._server_config = None
        self._provider_configs = None
        self._repository_configs = None
        self._load_all_configs()

    def _load_all_configs(self) -> None:
        """Load all configurations

        Raises:
            ConfigurationError: Configuration loading or validation failed
        """
        self._server_config = ServerConfig.from_loader(self.loader)
        self._server_config.validate()

        self._provider_configs = self.loader.load_all_provider_configs()
        self._repository_configs = self.loader.load_all_repository_configs()

        self.loader.validate_repository_configs()

    @property
    def server_config(self) -> ServerConfig:
        """Get server configuration"""
        if self._server_config is None:
            raise ConfigurationError('Server config not loaded')
        return self._server_config

    @property
    def provider_configs(self) -> Dict[Provider, ProviderConfig]:
        """Get provider configuration dictionary"""
        if self._provider_configs is None:
            raise ConfigurationError('Provider configs not loaded')
        return self._provider_configs

    @property
    def repository_configs(self) -> Dict[str, RepositoryConfig]:
        """Get repository configuration dictionary"""
        if self._repository_configs is None:
            raise ConfigurationError('Repository configs not loaded')
        return self._repository_configs

    def get_provider_config(self, provider: Provider) -> ProviderConfig:
        """Get configuration for specified provider

        Args:
            provider: Provider type

        Returns:
            ProviderConfig instance
        """
        return self.provider_configs.get(provider, ProviderConfig(
            provider=provider,
            verify=False,
            secret='',
            handle_events=[]
        ))

    def get_repository_config(self, name: str) -> RepositoryConfig:
        """Get configuration for specified repository

        Args:
            name: Repository name

        Returns:
            RepositoryConfig instance, or None if not found
        """
        return self.repository_configs.get(name)

    def has_repository(self, name: str) -> bool:
        """Check if repository exists

        Args:
            name: Repository name

        Returns:
            True if exists, False otherwise
        """
        return name in self.repository_configs
