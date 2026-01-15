"""Git Webhooks Server - Modular package structure.

Automated deployment server supporting GitHub, Gitee, GitLab, and custom webhooks.
"""

__version__ = '2.2.0'

# Export main classes for convenient import paths
from .server import WebhookServer
from .models.provider import Provider
from .models.request import WebhookRequest

__all__ = [
    '__version__',
    'WebhookServer',
    'Provider',
    'WebhookRequest',
]
