"""处理器基类

定义 webhook 处理器的抽象接口。
"""

from abc import ABC, abstractmethod
from typing import Optional

from gitwebhooks.models.provider import Provider
from gitwebhooks.models.request import WebhookRequest
from gitwebhooks.models.result import SignatureVerificationResult
from gitwebhooks.config.models import ProviderConfig
from gitwebhooks.utils.exceptions import SignatureValidationError, UnsupportedEventError


class WebhookHandler(ABC):
    """Webhook 处理器基类

    所有平台特定的处理器必须继承此类并实现所有抽象方法。
    """

    @abstractmethod
    def get_provider(self) -> Provider:
        """返回此处理器支持的提供者类型

        Returns:
            Provider 枚举值
        """
        pass

    @abstractmethod
    def verify_signature(self, request: WebhookRequest,
                        config: ProviderConfig) -> SignatureVerificationResult:
        """验证 webhook 签名

        Args:
            request: Webhook 请求数据
            config: 提供者配置（包含 secret）

        Returns:
            签名验证结果

        Raises:
            SignatureValidationError: 验证失败时
        """
        pass

    @abstractmethod
    def extract_repository(self, request: WebhookRequest,
                          config: ProviderConfig) -> Optional[str]:
        """从请求中提取仓库标识符

        Args:
            request: Webhook 请求数据
            config: 提供者配置（可能包含 identifier_path）

        Returns:
            仓库标识符（如 'owner/repo'），未找到返回 None
        """
        pass

    @abstractmethod
    def is_event_allowed(self, event: Optional[str],
                        config: ProviderConfig) -> bool:
        """检查事件类型是否被允许处理

        Args:
            event: 事件类型（如 'push', 'merge_request'）
            config: 提供者配置（包含 handle_events 列表）

        Returns:
            True 如果事件被允许，False 否则
        """
        pass

    def handle_request(self, request: WebhookRequest,
                      config: ProviderConfig) -> Optional[str]:
        """处理完整的 webhook 请求

        这是模板方法，定义了请求处理的固定流程：
        1. 检查事件是否被允许
        2. 验证签名
        3. 提取仓库标识符

        Args:
            request: Webhook 请求数据
            config: 提供者配置

        Returns:
            仓库标识符，如果处理失败返回 None

        Raises:
            SignatureValidationError: 签名验证失败
            UnsupportedEventError: 事件类型不被允许
        """
        # 步骤 1: 检查事件
        if not self.is_event_allowed(request.event, config):
            raise UnsupportedEventError(f'Event not configured: {request.event}')

        # 步骤 2: 验证签名（如果需要）
        if config.verify:
            result = self.verify_signature(request, config)
            if not result.is_valid:
                raise SignatureValidationError(result.error_message or 'Verification failed')

        # 步骤 3: 提取仓库标识符
        return self.extract_repository(request, config)
