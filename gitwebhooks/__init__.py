"""Git Webhooks Server - Modular package structure.

支持 Github、Gitee、Gitlab 和自定义 webhook 的自动化部署服务器。
"""

__version__ = '2.0.0'

# 导出主要类，提供便利的导入路径
from .server import WebhookServer
from .models.provider import Provider
from .models.request import WebhookRequest

__all__ = [
    '__version__',
    'WebhookServer',
    'Provider',
    'WebhookRequest',
]
