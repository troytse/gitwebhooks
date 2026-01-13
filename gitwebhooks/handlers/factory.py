"""处理器工厂类

根据请求 headers 创建对应的处理器实例。
"""

from typing import Dict

from gitwebhooks.handlers.base import WebhookHandler
from gitwebhooks.handlers.github import GithubHandler
from gitwebhooks.handlers.gitee import GiteeHandler
from gitwebhooks.handlers.gitlab import GitlabHandler
from gitwebhooks.handlers.custom import CustomHandler
from gitwebhooks.models.provider import Provider
from gitwebhooks.config.models import ProviderConfig
from gitwebhooks.utils.exceptions import UnsupportedProviderError


class HandlerFactory:
    """处理器工厂类

    根据请求 headers 创建对应的处理器实例
    """

    @staticmethod
    def from_headers(headers: Dict[str, str],
                    configs: Dict[Provider, ProviderConfig]) -> WebhookHandler:
        """根据请求 headers 创建处理器

        Args:
            headers: HTTP 请求头字典
            configs: 提供者配置字典

        Returns:
            对应的 WebhookHandler 实例

        Raises:
            UnsupportedProviderError: 无法识别的平台
        """
        # 检查 X-GitHub-Event
        if 'X-GitHub-Event' in headers:
            return GithubHandler()

        # 检查 X-Gitee-Event
        if 'X-Gitee-Event' in headers:
            return GiteeHandler()

        # 检查 X-Gitlab-Event
        if 'X-Gitlab-Event' in headers:
            return GitlabHandler()

        # 检查自定义 header
        custom_config = configs.get(Provider.CUSTOM)
        if custom_config and custom_config.header_name:
            if headers.get(custom_config.header_name) == custom_config.header_value:
                return CustomHandler()

        raise UnsupportedProviderError('Unable to identify provider from headers')

    @staticmethod
    def from_handler_type(provider: Provider) -> WebhookHandler:
        """根据提供者类型创建处理器

        Args:
            provider: 提供者类型

        Returns:
            对应的 WebhookHandler 实例

        Raises:
            UnsupportedProviderError: 不支持的提供者
        """
        handlers = {
            Provider.GITHUB: GithubHandler,
            Provider.GITEE: GiteeHandler,
            Provider.GITLAB: GitlabHandler,
            Provider.CUSTOM: CustomHandler,
        }

        handler_class = handlers.get(provider)
        if handler_class is None:
            raise UnsupportedProviderError(f'No handler for provider: {provider}')

        return handler_class()
