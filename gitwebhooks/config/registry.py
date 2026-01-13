"""配置注册表

持有所有配置并提供访问接口。
"""

from typing import Dict

from gitwebhooks.config.loader import ConfigLoader
from gitwebhooks.config.models import ProviderConfig, RepositoryConfig
from gitwebhooks.config.server import ServerConfig
from gitwebhooks.models.provider import Provider
from gitwebhooks.utils.exceptions import ConfigurationError


class ConfigurationRegistry:
    """配置注册表

    持有所有配置并提供访问接口
    """

    def __init__(self, loader: ConfigLoader):
        """初始化配置注册表

        Args:
            loader: 配置加载器实例
        """
        self.loader = loader
        self._server_config = None
        self._provider_configs = None
        self._repository_configs = None
        self._load_all_configs()

    def _load_all_configs(self) -> None:
        """加载所有配置

        Raises:
            ConfigurationError: 配置加载或验证失败
        """
        self._server_config = ServerConfig.from_loader(self.loader)
        self._server_config.validate()

        self._provider_configs = self.loader.load_all_provider_configs()
        self._repository_configs = self.loader.load_all_repository_configs()

        self.loader.validate_repository_configs()

    @property
    def server_config(self) -> ServerConfig:
        """获取服务器配置"""
        if self._server_config is None:
            raise ConfigurationError('Server config not loaded')
        return self._server_config

    @property
    def provider_configs(self) -> Dict[Provider, ProviderConfig]:
        """获取提供者配置字典"""
        if self._provider_configs is None:
            raise ConfigurationError('Provider configs not loaded')
        return self._provider_configs

    @property
    def repository_configs(self) -> Dict[str, RepositoryConfig]:
        """获取仓库配置字典"""
        if self._repository_configs is None:
            raise ConfigurationError('Repository configs not loaded')
        return self._repository_configs

    def get_provider_config(self, provider: Provider) -> ProviderConfig:
        """获取指定提供者的配置

        Args:
            provider: 提供者类型

        Returns:
            ProviderConfig 实例
        """
        return self.provider_configs.get(provider, ProviderConfig(
            provider=provider,
            verify=False,
            secret='',
            handle_events=[]
        ))

    def get_repository_config(self, name: str) -> RepositoryConfig:
        """获取指定仓库的配置

        Args:
            name: 仓库名称

        Returns:
            RepositoryConfig 实例，未找到返回 None
        """
        return self.repository_configs.get(name)

    def has_repository(self, name: str) -> bool:
        """检查仓库是否存在

        Args:
            name: 仓库名称

        Returns:
            True 如果存在，False 否则
        """
        return name in self.repository_configs
