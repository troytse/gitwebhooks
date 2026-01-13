"""HTTP 请求处理器

处理 HTTP POST 请求的 webhook 端点。
"""

import json
import logging
from http.server import BaseHTTPRequestHandler
from typing import Dict, Optional
from urllib.parse import parse_qs

from gitwebhooks.models.provider import Provider
from gitwebhooks.models.request import WebhookRequest
from gitwebhooks.config.models import ProviderConfig, RepositoryConfig
from gitwebhooks.handlers.factory import HandlerFactory
from gitwebhooks.utils.constants import *
from gitwebhooks.utils.exceptions import *
from gitwebhooks.utils.executor import execute_deployment


class WebhookRequestHandler(BaseHTTPRequestHandler):
    """Webhook 请求处理器

    处理 HTTP POST 请求，验证签名，触发部署命令。
    """

    # 类变量：配置注入
    _provider_configs: Dict[Provider, ProviderConfig] = {}
    _repository_configs: Dict[str, RepositoryConfig] = {}

    @classmethod
    def configure(cls, provider_configs: Dict[Provider, ProviderConfig],
                 repository_configs: Dict[str, RepositoryConfig]) -> None:
        """配置处理器类（依赖注入）

        Args:
            provider_configs: 提供者配置字典
            repository_configs: 仓库配置字典
        """
        cls._provider_configs = provider_configs
        cls._repository_configs = repository_configs

    def __init__(self, request, client_address, server):
        """初始化请求处理器

        Args:
            request: HTTP 请求
            client_address: 客户端地址
            server: 服务器实例
        """
        # 复制类级配置到实例（避免共享状态）
        self._provider_configs = self.__class__._provider_configs.copy()
        self._repository_configs = self.__class__._repository_configs.copy()
        super().__init__(request, client_address, server)

    def do_GET(self) -> None:
        """处理 GET 请求

        所有 GET 请求返回 403 Forbidden
        """
        self.send_error(HTTP_FORBIDDEN, MESSAGE_FORBIDDEN)

    def do_POST(self) -> None:
        """处理 POST 请求（webhook 端点）

        实现流程：
        1. 解析请求体
        2. 识别提供者和事件
        3. 创建对应的处理器
        4. 验证签名
        5. 提取仓库标识符
        6. 执行部署命令
        7. 发送响应

        所有错误都被捕获并返回适当的 HTTP 状态码
        """
        try:
            # 步骤 1: 解析请求体
            try:
                request = self._parse_request()
            except RequestParseError as e:
                logging.warning('Request parse failed: %s', e)
                self._send_error(HTTP_BAD_REQUEST, MESSAGE_BAD_REQUEST)
                return

            if request.post_data is None:
                logging.warning('Unsupported request format')
                self._send_error(HTTP_BAD_REQUEST, MESSAGE_BAD_REQUEST)
                return

            # 步骤 2: 识别提供者
            provider = self._identify_provider(request)
            if provider is None:
                logging.warning('Unknown provider')
                self._send_error(HTTP_PRECONDITION_FAILED, MESSAGE_PRECONDITION_FAILED)
                return

            # 步骤 3: 创建处理器
            handler = HandlerFactory.from_handler_type(provider)

            # 步骤 4-6: 处理请求
            try:
                provider_config = self._provider_configs.get(provider)
                if not provider_config:
                    raise UnsupportedProviderError(f'{provider} configuration not found')

                repo_name = handler.handle_request(request, provider_config)

            except (SignatureValidationError, UnsupportedEventError,
                   UnsupportedProviderError) as e:
                logging.warning('Webhook processing error: %s', e)
                if isinstance(e, SignatureValidationError):
                    self._send_error(HTTP_UNAUTHORIZED, MESSAGE_UNAUTHORIZED)
                elif isinstance(e, UnsupportedEventError):
                    self._send_error(HTTP_NOT_ACCEPTABLE, MESSAGE_NOT_ACCEPTABLE)
                else:
                    self._send_error(HTTP_PRECONDITION_FAILED, MESSAGE_PRECONDITION_FAILED)
                return

            # 步骤 7: 执行部署命令
            if repo_name:
                repo_config = self._repository_configs.get(repo_name)
                if not repo_config:
                    logging.warning('No repository configuration: %s', repo_name)
                    self._send_error(HTTP_NOT_FOUND, MESSAGE_NOT_FOUND)
                    return

                execute_deployment(repo_name, repo_config.cwd, repo_config.cmd)
                self._send_response(HTTP_OK)
            else:
                logging.warning('Repository information missing from payload')
                self._send_error(HTTP_NOT_FOUND, MESSAGE_NOT_FOUND)

        except Exception as e:
            logging.error('Unexpected error processing webhook: %s', e)
            self._send_error(HTTP_INTERNAL_SERVER_ERROR, MESSAGE_INTERNAL_SERVER_ERROR)

    def _parse_request(self) -> WebhookRequest:
        """解析 HTTP 请求

        Returns:
            WebhookRequest 实例

        Raises:
            RequestParseError: 解析失败
        """
        # 获取 Content-Type 和 Content-Length
        content_type = self.headers.get(HEADER_CONTENT_TYPE, '')
        content_length = int(self.headers.get(HEADER_CONTENT_LENGTH, 0))

        # 读取请求体
        if content_length == 0:
            raise RequestParseError('Empty request body')

        payload = self.rfile.read(content_length)

        # 解析 POST 数据
        post_data = None
        if CONTENT_TYPE_JSON in content_type:
            try:
                post_data = json.loads(payload.decode('utf-8'))
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                raise RequestParseError(f'Invalid JSON: {e}')
        elif CONTENT_TYPE_FORM_URLENCODED in content_type:
            try:
                post_data = {k: v[0] if v else None for k, v in parse_qs(payload.decode('utf-8')).items()}
            except UnicodeDecodeError as e:
                raise RequestParseError(f'Invalid form data: {e}')

        # 识别提供者和事件
        provider, event = self._parse_provider_and_event()

        return WebhookRequest(
            provider=provider,
            event=event,
            payload=payload,
            headers=dict(self.headers),
            post_data=post_data,
            content_type=content_type,
            content_length=content_length
        )

    def _parse_provider_and_event(self) -> tuple:
        """从请求头解析提供者和事件

        Returns:
            Tuple of (provider, event)
        """
        headers_dict = dict(self.headers)

        # Github
        if HEADER_GITHUB_EVENT in headers_dict:
            return Provider.GITHUB, headers_dict.get(HEADER_GITHUB_EVENT)

        # Gitee
        if HEADER_GITEE_EVENT in headers_dict:
            return Provider.GITEE, headers_dict.get(HEADER_GITEE_EVENT)

        # Gitlab
        if HEADER_GITLAB_EVENT in headers_dict:
            return Provider.GITLAB, headers_dict.get(HEADER_GITLAB_EVENT)

        # Custom
        custom_config = self._provider_configs.get(Provider.CUSTOM)
        if custom_config and custom_config.header_name:
            header_value = headers_dict.get(custom_config.header_name, '')
            if header_value.startswith(custom_config.header_value):
                event = headers_dict.get(custom_config.header_event) if custom_config.header_event else None
                return Provider.CUSTOM, event

        # 无法识别
        return None, None

    def _identify_provider(self, request: WebhookRequest) -> Optional[Provider]:
        """从请求中识别提供者

        Args:
            request: Webhook 请求

        Returns:
            Provider 枚举值，无法识别返回 None
        """
        return request.provider

    def _send_response(self, status_code: int, message: bytes = MESSAGE_OK) -> None:
        """发送 HTTP 响应

        Args:
            status_code: HTTP 状态码
            message: 响应体
        """
        self.send_response(status_code)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write(message)

    def _send_error(self, status_code: int, message: str = '') -> None:
        """发送 HTTP 错误响应

        Args:
            status_code: HTTP 状态码
            message: 错误消息
        """
        self.send_error(status_code, message)

    def log_message(self, format: str, *args) -> None:
        """覆盖以防止重复日志"""
        pass
