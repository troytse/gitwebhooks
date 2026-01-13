"""Webhook 请求数据封装

表示解析后的 HTTP webhook 请求。
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional

from gitwebhooks.models.provider import Provider


@dataclass
class WebhookRequest:
    """Webhook 请求数据封装

    Attributes:
        provider: Git 平台提供者
        event: 事件类型（如 'push', 'merge_request'）
        payload: 原始请求体字节
        headers: HTTP 请求头
        post_data: 解析后的 JSON/表单数据
        content_type: Content-Type header 值
        content_length: Content-Length header 值
    """
    provider: Provider
    event: Optional[str]
    payload: bytes
    headers: Dict[str, str]
    post_data: Optional[Dict[str, Any]]
    content_type: str
    content_length: int

    @property
    def repo_identifier(self) -> Optional[str]:
        """从 post_data 提取仓库标识符

        Returns:
            仓库标识符（如 'owner/repo'），未找到则返回 None

        提取规则:
        - Github: repository.full_name
        - Gitee: repository.full_name
        - Gitlab: project.path_with_namespace
        - Custom: 使用 ProviderConfig.identifier_path
        """
        if self.post_data is None:
            return None

        extractors = {
            Provider.GITHUB: lambda d: d.get('repository', {}).get('full_name'),
            Provider.GITEE: lambda d: d.get('repository', {}).get('full_name'),
            Provider.GITLAB: lambda d: d.get('project', {}).get('path_with_namespace'),
        }

        extractor = extractors.get(self.provider)
        if extractor:
            result = extractor(self.post_data)
            return result if isinstance(result, str) else None

        # Custom provider 使用 identifier_path（在处理器中处理）
        return None
