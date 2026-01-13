"""配置数据模型

定义配置相关的数据类。
"""

import configparser
from dataclasses import dataclass
from pathlib import Path
from typing import List

from gitwebhooks.models.provider import Provider
from gitwebhooks.utils.exceptions import ConfigurationError


@dataclass
class ProviderConfig:
    """Git 平台提供者配置

    Attributes:
        provider: 提供者类型
        verify: 是否验证签名/token
        secret: 验证用的密钥
        handle_events: 要处理的事件列表（空列表=处理所有事件）
        header_name: 自定义识别 header（仅 CUSTOM）
        header_value: 自定义识别值（仅 CUSTOM）
        header_event: 自定义事件 header（仅 CUSTOM）
        header_token: 自定义 token header（仅 CUSTOM）
        identifier_path: 仓库标识符 JSON 路径（仅 CUSTOM）
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
        """从 ConfigParser 加载提供者配置

        Args:
            parser: ConfigParser 实例
            provider: 提供者类型

        Returns:
            ProviderConfig 实例

        Raises:
            configparser.NoSectionError: 配置节不存在
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

        # Custom provider 额外字段
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
        """检查事件是否被允许处理

        Args:
            event: 事件类型（None 表示所有事件）

        Returns:
            True 如果事件被允许，False 否则
        """
        if not self.handle_events:
            return True  # 空列表 = 处理所有事件
        return event in self.handle_events


@dataclass
class RepositoryConfig:
    """仓库部署配置

    Attributes:
        name: 仓库名称（格式：'owner/repo' 或 'group/project/repo'）
        cwd: 部署命令执行的工作目录
        cmd: 部署命令（shell 字符串）
    """
    name: str
    cwd: str
    cmd: str

    @classmethod
    def from_config_parser(cls, parser: configparser.ConfigParser,
                          name: str):
        """从 ConfigParser 加载仓库配置

        Args:
            parser: ConfigParser 实例
            name: 配置节名称（仓库名称）

        Returns:
            RepositoryConfig 实例，如果节不存在则返回 None

        Raises:
            configparser.NoOptionError: 节存在但缺少必需选项
        """
        if not parser.has_section(name):
            return None

        return cls(
            name=name,
            cwd=parser.get(name, 'cwd'),
            cmd=parser.get(name, 'cmd')
        )

    def validate(self) -> None:
        """验证配置有效性

        Raises:
            ConfigurationError: 配置无效
        """
        if not self.cwd:
            raise ConfigurationError(f'Repository {self.name}: cwd is required')
        if not self.cmd:
            raise ConfigurationError(f'Repository {self.name}: cmd is required')
