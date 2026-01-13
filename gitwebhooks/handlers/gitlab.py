"""Gitlab webhook 处理器

处理来自 Gitlab 的 webhook 请求。
"""

from typing import Optional

from gitwebhooks.handlers.base import WebhookHandler
from gitwebhooks.models.provider import Provider
from gitwebhooks.models.request import WebhookRequest
from gitwebhooks.models.result import SignatureVerificationResult
from gitwebhooks.config.models import ProviderConfig
from gitwebhooks.auth.factory import VerifierFactory


class GitlabHandler(WebhookHandler):
    """Gitlab webhook 处理器"""

    def __init__(self):
        self._verifier = VerifierFactory.create_gitlab_verifier()

    def get_provider(self) -> Provider:
        """返回 Provider.GITLAB"""
        return Provider.GITLAB

    def verify_signature(self, request: WebhookRequest,
                        config: ProviderConfig) -> SignatureVerificationResult:
        """验证 Gitlab token"""
        signature = request.headers.get('X-Gitlab-Token')
        return self._verifier.verify(request.payload, signature, config.secret)

    def extract_repository(self, request: WebhookRequest,
                          config: ProviderConfig) -> Optional[str]:
        """从请求中提取 Gitlab 项目路径"""
        if request.post_data is None:
            return None
        project = request.post_data.get('project', {})
        return project.get('path_with_namespace') if isinstance(project, dict) else None

    def is_event_allowed(self, event: Optional[str],
                        config: ProviderConfig) -> bool:
        """检查事件是否在 config.handle_events 列表中"""
        return config.allows_event(event)
