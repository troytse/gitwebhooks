"""配置加载器

从 INI 文件加载和解析配置。
"""

import configparser
from pathlib import Path
from typing import Dict, Optional

from gitwebhooks.config.models import ProviderConfig, RepositoryConfig
from gitwebhooks.models.provider import Provider
from gitwebhooks.utils.exceptions import ConfigurationError


class ConfigLoader:
    """配置加载器

    负责从 INI 文件加载和验证配置
    """

    def __init__(self, config_path: str):
        """初始化配置加载器

        Args:
            config_path: INI 配置文件路径

        Raises:
            ConfigurationError: 文件不存在或无法解析
        """
        self.config_path = Path(config_path)
        self.parser = configparser.ConfigParser()
        self._load_file()

    def _load_file(self) -> None:
        """加载配置文件

        Raises:
            ConfigurationError: 文件不存在或解析失败
        """
        if not self.config_path.exists():
            raise ConfigurationError(f'Config file not found: {self.config_path}')

        try:
            self.parser.read(str(self.config_path))
        except (configparser.Error, UnicodeDecodeError) as e:
            raise ConfigurationError(f'Failed to parse config: {e}')

    def load_provider_config(self, provider: Provider) -> ProviderConfig:
        """加载指定提供者的配置

        Args:
            provider: 提供者类型

        Returns:
            ProviderConfig 实例

        Raises:
            ConfigurationError: 配置节不存在
        """
        try:
            return ProviderConfig.from_config_parser(self.parser, provider)
        except configparser.NoSectionError:
            # 返回默认配置
            return ProviderConfig(
                provider=provider,
                verify=False,
                secret='',
                handle_events=[]
            )

    def load_all_provider_configs(self) -> Dict[Provider, ProviderConfig]:
        """加载所有提供者配置

        Returns:
            提供者到配置的映射
        """
        configs = {}
        for provider in Provider:
            configs[provider] = self.load_provider_config(provider)
        return configs

    def load_repository_config(self, name: str) -> Optional[RepositoryConfig]:
        """加载指定仓库的配置

        Args:
            name: 仓库名称（配置节名称）

        Returns:
            RepositoryConfig 实例，如果节不存在返回 None
        """
        return RepositoryConfig.from_config_parser(self.parser, name)

    def load_all_repository_configs(self) -> Dict[str, RepositoryConfig]:
        """加载所有仓库配置

        Returns:
            仓库名称到配置的映射

        Note:
            跳过保留节名: server, ssl, github, gitee, gitlab, custom
        """
        configs = {}
        reserved_sections = self._get_reserved_sections()

        for section in self.parser.sections():
            if section not in reserved_sections:
                repo_config = self.load_repository_config(section)
                if repo_config is not None:
                    configs[section] = repo_config

        return configs

    def _get_reserved_sections(self) -> set:
        """获取保留的配置节名称

        Returns:
            保留节名集合
        """
        return {'server', 'ssl', 'github', 'gitee', 'gitlab', 'custom'}

    def get_server_config(self) -> Dict[str, any]:
        """获取服务器配置

        Returns:
            包含 server 配置的字典，键包括:
            - address: 监听地址
            - port: 监听端口
            - log_file: 日志文件路径
        """
        return {
            'address': self.parser.get('server', 'address', fallback='0.0.0.0'),
            'port': self.parser.getint('server', 'port', fallback=6789),
            'log_file': self.parser.get('server', 'log_file', fallback='').strip(),
        }

    def get_ssl_config(self) -> Optional[Dict[str, str]]:
        """获取 SSL 配置

        Returns:
            包含 SSL 配置的字典，如果未启用则返回 None
            键包括:
            - enable: 是否启用 SSL
            - key_file: SSL 密钥文件路径
            - cert_file: SSL 证书文件路径
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
        """验证所有仓库配置

        Raises:
            ConfigurationError: 配置无效
        """
        configs = self.load_all_repository_configs()

        for name, config in configs.items():
            try:
                config.validate()
            except ConfigurationError as e:
                raise ConfigurationError(f'Repository {name}: {e}')
