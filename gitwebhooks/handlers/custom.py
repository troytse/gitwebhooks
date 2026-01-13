"""自定义 webhook 处理器

处理来自自定义 webhook 源的请求。
"""

from typing import Optional

from gitwebhooks.handlers.base import WebhookHandler
from gitwebhooks.models.provider import Provider
from gitwebhooks.models.request import WebhookRequest
from gitwebhooks.models.result import SignatureVerificationResult
from gitwebhooks.config.models import ProviderConfig
from gitwebhooks.auth.factory import VerifierFactory


class CustomHandler(WebhookHandler):
    """自定义 webhook 处理器"""

    def __init__(self):
        self._verifier = None  # 根据配置动态创建

    def get_provider(self) -> Provider:
        """返回 Provider.CUSTOM"""
        return Provider.CUSTOM

    def verify_signature(self, request: WebhookRequest,
                        config: ProviderConfig) -> SignatureVerificationResult:
        """验证自定义 token"""
        # 创建验证器（验证是否启用取决于 header_token 是否配置）
        verify_enabled = bool(config.header_token)
        if not self._verifier:
            self._verifier = VerifierFactory.create_custom_verifier(verify_enabled)

        signature = request.headers.get(config.header_token) if config.header_token else ''
        return self._verifier.verify(request.payload, signature, config.secret)

    def extract_repository(self, request: WebhookRequest,
                          config: ProviderConfig) -> Optional[str]:
        """使用 JSON 路径提取仓库标识符"""
        if request.post_data is None or not config.identifier_path:
            return None

        # 按 '.' 分割路径
        path_parts = config.identifier_path.split('.')
        current = request.post_data

        # 逐层遍历
        for part in path_parts:
            if isinstance(current, dict):
                current = current.get(part)
            else:
                return None

        # 返回最终值（必须是字符串）
        return current if isinstance(current, str) else None

    def is_event_allowed(self, event: Optional[str],
                        config: ProviderConfig) -> bool:
        """检查事件是否被允许

        Args:
            event: 事件类型（已在调用方从 headers 解析）
            config: 提供者配置

        Returns:
            True 如果事件被允许，False 否则
        """
        # 如果没有配置事件 header，允许所有事件
        if not config.header_event:
            return config.allows_event(event)

        # 使用传入的 event 参数（已由调用方从 headers 解析）
        return config.allows_event(event)
