"""Gitee webhook 处理器

处理来自 Gitee 的 webhook 请求。
"""

from typing import Optional

from gitwebhooks.handlers.base import WebhookHandler
from gitwebhooks.models.provider import Provider
from gitwebhooks.models.request import WebhookRequest
from gitwebhooks.models.result import SignatureVerificationResult
from gitwebhooks.config.models import ProviderConfig
from gitwebhooks.auth.factory import VerifierFactory


class GiteeHandler(WebhookHandler):
    """Gitee webhook 处理器"""

    def __init__(self):
        self._verifier = VerifierFactory.create_gitee_verifier()

    def get_provider(self) -> Provider:
        """返回 Provider.GITEE"""
        return Provider.GITEE

    def verify_signature(self, request: WebhookRequest,
                        config: ProviderConfig) -> SignatureVerificationResult:
        """验证 Gitee 签名或密码"""
        signature = request.headers.get('X-Gitee-Token')
        timestamp = request.headers.get('X-Gitee-Timestamp')
        return self._verifier.verify(
            request.payload,
            signature,
            config.secret,
            timestamp=timestamp
        )

    def extract_repository(self, request: WebhookRequest,
                          config: ProviderConfig) -> Optional[str]:
        """从请求中提取 Gitee 仓库全名"""
        if request.post_data is None:
            return None
        repo = request.post_data.get('repository', {})
        return repo.get('full_name') if isinstance(repo, dict) else None

    def is_event_allowed(self, event: Optional[str],
                        config: ProviderConfig) -> bool:
        """检查事件是否在 config.handle_events 列表中"""
        return config.allows_event(event)
