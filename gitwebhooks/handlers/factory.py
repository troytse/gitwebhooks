"""Handler factory class

Creates corresponding handler instances based on request headers.
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
    """Handler factory class

    Creates corresponding handler instances based on request headers
    """

    @staticmethod
    def from_headers(headers: Dict[str, str],
                    configs: Dict[Provider, ProviderConfig]) -> WebhookHandler:
        """Create handler based on request headers

        Args:
            headers: HTTP request header dictionary
            configs: Provider configuration dictionary

        Returns:
            Corresponding WebhookHandler instance

        Raises:
            UnsupportedProviderError: Unrecognized platform
        """
        # Check X-GitHub-Event
        if 'X-GitHub-Event' in headers:
            return GithubHandler()

        # Check X-Gitee-Event
        if 'X-Gitee-Event' in headers:
            return GiteeHandler()

        # Check X-Gitlab-Event
        if 'X-Gitlab-Event' in headers:
            return GitlabHandler()

        # Check custom header
        custom_config = configs.get(Provider.CUSTOM)
        if custom_config and custom_config.header_name:
            if headers.get(custom_config.header_name) == custom_config.header_value:
                return CustomHandler()

        raise UnsupportedProviderError('Unable to identify provider from headers')

    @staticmethod
    def from_handler_type(provider: Provider) -> WebhookHandler:
        """Create handler based on provider type

        Args:
            provider: Provider type

        Returns:
            Corresponding WebhookHandler instance

        Raises:
            UnsupportedProviderError: Unsupported provider
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
