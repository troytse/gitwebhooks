"""Configuration loader

Load and parse configuration from INI files.
"""

import configparser
from pathlib import Path
from typing import Dict, Optional

from gitwebhooks.config.models import ProviderConfig, RepositoryConfig
from gitwebhooks.models.provider import Provider
from gitwebhooks.utils.exceptions import ConfigurationError


class ConfigLoader:
    """Configuration loader

    Responsible for loading and validating configuration from INI files
    """

    def __init__(self, config_path: str):
        """Initialize configuration loader

        Args:
            config_path: INI configuration file path

        Raises:
            ConfigurationError: File does not exist or cannot be parsed
        """
        self.config_path = Path(config_path)
        self.parser = configparser.ConfigParser()
        self._load_file()

    def _load_file(self) -> None:
        """Load configuration file

        Raises:
            ConfigurationError: File does not exist or parsing failed
        """
        if not self.config_path.exists():
            raise ConfigurationError(f'Config file not found: {self.config_path}')

        try:
            self.parser.read(str(self.config_path))
        except (configparser.Error, UnicodeDecodeError) as e:
            raise ConfigurationError(f'Failed to parse config: {e}')

    def load_provider_config(self, provider: Provider) -> ProviderConfig:
        """Load configuration for specified provider

        Args:
            provider: Provider type

        Returns:
            ProviderConfig instance

        Raises:
            ConfigurationError: Configuration section does not exist
        """
        try:
            return ProviderConfig.from_config_parser(self.parser, provider)
        except configparser.NoSectionError:
            # Return default configuration
            return ProviderConfig(
                provider=provider,
                verify=False,
                secret='',
                handle_events=[]
            )

    def load_all_provider_configs(self) -> Dict[Provider, ProviderConfig]:
        """Load all provider configurations

        Returns:
            Mapping of provider to configuration
        """
        configs = {}
        for provider in Provider:
            configs[provider] = self.load_provider_config(provider)
        return configs

    def load_repository_config(self, name: str) -> Optional[RepositoryConfig]:
        """Load configuration for specified repository

        Args:
            name: Repository name (configuration section name)

        Returns:
            RepositoryConfig instance, or None if section does not exist
        """
        return RepositoryConfig.from_config_parser(self.parser, name)

    def load_all_repository_configs(self) -> Dict[str, RepositoryConfig]:
        """Load all repository configurations

        Returns:
            Mapping of repository name to configuration

        Note:
            Skips reserved section names: server, ssl, github, gitee, gitlab, custom
            Skips repository sections with missing required options (logs warning)
        """
        configs = {}
        reserved_sections = self._get_reserved_sections()

        for section in self.parser.sections():
            if section not in reserved_sections:
                try:
                    repo_config = self.load_repository_config(section)
                    if repo_config is not None:
                        configs[section] = repo_config
                except (configparser.NoOptionError, ConfigurationError) as e:
                    # Skip incomplete repository configurations
                    import logging
                    logging.warning('跳过不完整的仓库配置 [%s]: %s', section, e)

        return configs

    def _get_reserved_sections(self) -> set:
        """Get reserved configuration section names

        Returns:
            Set of reserved section names
        """
        return {'server', 'ssl', 'github', 'gitee', 'gitlab', 'custom'}

    def get_server_config(self) -> Dict[str, any]:
        """Get server configuration

        Returns:
            Dictionary containing server configuration, keys include:
            - address: Listen address
            - port: Listen port
            - log_file: Log file path
        """
        return {
            'address': self.parser.get('server', 'address', fallback='0.0.0.0'),
            'port': self.parser.getint('server', 'port', fallback=6789),
            'log_file': self.parser.get('server', 'log_file', fallback='').strip(),
        }

    def get_ssl_config(self) -> Optional[Dict[str, str]]:
        """Get SSL configuration

        Returns:
            Dictionary containing SSL configuration, or None if not enabled
            Keys include:
            - enable: Whether SSL is enabled
            - key_file: SSL key file path
            - cert_file: SSL certificate file path
        """
        try:
            if not self.parser.getboolean('ssl', 'enable'):
                return None
        except (configparser.NoSectionError, ValueError):
            return None

        return {
            'enable': True,
            'key_file': self.parser.get('ssl', 'key_file'),
            'cert_file': self.parser.get('ssl', 'cert_file'),
        }

    def validate_repository_configs(self) -> None:
        """Validate all repository configurations

        Raises:
            ConfigurationError: Configuration is invalid
        """
        configs = self.load_all_repository_configs()

        for name, config in configs.items():
            try:
                config.validate()
            except ConfigurationError as e:
                raise ConfigurationError(f'Repository {name}: {e}')
