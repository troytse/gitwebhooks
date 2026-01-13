"""HTTP 服务器主逻辑

创建和运行 HTTP 服务器，处理 webhook 请求。
"""

import logging
import ssl
import sys
from http.server import HTTPServer
from typing import Optional

from gitwebhooks.config.loader import ConfigLoader
from gitwebhooks.config.registry import ConfigurationRegistry
from gitwebhooks.config.server import ServerConfig
from gitwebhooks.handlers.request import WebhookRequestHandler
from gitwebhooks.logging.setup import setup_logging
from gitwebhooks.utils.exceptions import ConfigurationError


class WebhookServer:
    """Git Webhooks 服务器主类

    负责创建和运行 HTTP 服务器，处理 webhook 请求。
    """

    def __init__(self, config_path: str,
                 registry: Optional[ConfigurationRegistry] = None):
        """初始化 Webhook 服务器

        Args:
            config_path: INI 配置文件路径
            registry: 配置注册表（可选，用于依赖注入）

        Raises:
            ConfigurationError: 配置无效或缺失
        """
        self.config_path = config_path
        self.loader = ConfigLoader(config_path)
        self.registry = registry or ConfigurationRegistry(self.loader)
        self.server_config = self.registry.server_config

        # 配置日志
        self._setup_logging()

    def _setup_logging(self) -> None:
        """配置日志系统

        根据 server 配置设置日志记录：
        - 如果 log_file 为空，只输出到 stdout
        - 如果 log_file 非空，同时输出到文件和 stdout

        Raises:
            ConfigurationError: 日志文件无法创建
        """
        setup_logging(self.server_config.log_file)

    def create_http_server(self) -> HTTPServer:
        """创建 HTTP 服务器实例

        Returns:
            配置好的 HTTPServer 实例

        Raises:
            ConfigurationError: 服务器配置无效
            OSError: 绑定地址失败
        """
        # 配置处理器类（注入依赖）
        WebhookRequestHandler.configure(
            self.registry.provider_configs,
            self.registry.repository_configs
        )

        # 创建服务器
        server = HTTPServer(
            (self.server_config.address, self.server_config.port),
            WebhookRequestHandler
        )

        # 配置 SSL（如果启用）
        if self.server_config.ssl_enabled:
            server.socket = self._wrap_socket_ssl(server.socket)

        return server

    def _wrap_socket_ssl(self, socket):
        """用 SSL 包装 socket

        Args:
            socket: 原始 socket

        Returns:
            SSL 包装的 socket

        Raises:
            ConfigurationError: SSL 配置无效
            ssl.SSLError: SSL 初始化失败
        """
        try:
            context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            context.load_cert_chain(
                certfile=self.server_config.ssl_cert_file,
                keyfile=self.server_config.ssl_key_file
            )
            return context.wrap_socket(socket, server_side=True)
        except (ssl.SSLError, OSError) as e:
            raise ConfigurationError(f'SSL configuration error: {e}')

    def run(self) -> None:
        """启动服务器主循环

        此方法会阻塞，直到服务器被停止。
        """
        server = self.create_http_server()

        ssl_message = ' with SSL' if self.server_config.ssl_enabled else ''
        logging.info('Serving on %s port %d%s...',
                    self.server_config.address,
                    self.server_config.port,
                    ssl_message)

        try:
            server.serve_forever()
        except KeyboardInterrupt:
            logging.info('Server stopped by user')
            server.shutdown()
        except Exception as e:
            logging.error('Server error: %s', e)
            raise
