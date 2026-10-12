"""Handler factory class

Creates corresponding handler instances based on request headers.
"""


from gitwebhooks.handlers.base import WebhookHandler
from gitwebhooks.handlers.github import GithubHandler
from gitwebhooks.handlers.gitee import GiteeHandler
from gitwebhooks.handlers.gitlab import GitlabHandler
from gitwebhooks.handlers.custom import CustomHandler
from gitwebhooks.models.provider import Provider
from gitwebhooks.utils.exceptions import UnsupportedProviderError


class HandlerFactory:
    """Handler factory class

    Creates corresponding handler instances based on request headers
    """

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
