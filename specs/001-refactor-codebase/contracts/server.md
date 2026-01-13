# Server Module Contract

**Module**: `gitwebhooks.server`
**Version**: 1.0.0
**Status**: Design Phase

## Overview

服务器模块负责 HTTP 服务器的创建、配置和运行。基于 Python 标准库的 `http.server` 实现，支持可选的 SSL/TLS。

---

## WebhookServer Contract

**Class**: `WebhookServer`
**Module**: `gitwebhooks.server`
**Type**: Application class

```python
from http.server import HTTPServer
from typing import Dict, Optional

from gitwebhooks.config.loader import ConfigLoader
from gitwebhooks.config.registry import ConfigurationRegistry
from gitwebhooks.config.models import ServerConfig

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
        log_file = self.server_config.log_file

        if log_file:
            try:
                # 初始化日志文件
                with open(log_file, 'w', encoding='utf-8') as f:
                    pass
            except (IOError, OSError) as e:
                raise ConfigurationError(f'Cannot create log file {log_file}: {e}')

        logging.basicConfig(
            level=logging.DEBUG,
            filename=log_file if log_file else None,
            format='%(asctime)s %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        if log_file:
            logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))

    def create_http_server(self) -> HTTPServer:
        """创建 HTTP 服务器实例

        Returns:
            配置好的 HTTPServer 实例

        Raises:
            ConfigurationError: 服务器配置无效
            OSError: 绑定地址失败
        """
        # 导入请求处理器
        from gitwebhooks.handlers.request import WebhookRequestHandler

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
        import ssl

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
```

---

## Request Handler Contract

**Class**: `WebhookRequestHandler`
**Module**: `gitwebhooks.handlers.request`
**Extends**: `BaseHTTPRequestHandler`

```python
from http.server import BaseHTTPRequestHandler
from typing import Dict, Optional

from gitwebhooks.models.provider import Provider
from gitwebhooks.models.request import WebhookRequest
from gitwebhooks.config.models import ProviderConfig, RepositoryConfig
from gitwebhooks.utils.constants import *

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

                self._execute_deployment(repo_name, repo_config)
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
        # 实现 JSON 和 form-urlencoded 解析
        # 详见原始代码
        pass

    def _identify_provider(self, request: WebhookRequest) -> Optional[Provider]:
        """从请求中识别提供者

        Args:
            request: Webhook 请求

        Returns:
            Provider 枚举值，无法识别返回 None
        """
        # 检查 headers
        # 详见原始代码的 _parse_provider 方法
        pass

    def _execute_deployment(self, repo_name: str, repo_config: RepositoryConfig) -> None:
        """执行部署命令

        Args:
            repo_name: 仓库名称
            repo_config: 仓库配置

        Note:
            命令异步执行，不阻塞服务器
        """
        logging.info('[%s] Executing: %s', repo_name, repo_config.cmd)

        try:
            subprocess.Popen(
                repo_config.cmd,
                cwd=repo_config.cwd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
        except (OSError, subprocess.SubprocessError) as e:
            logging.warning('[%s] Execution failed: %s', repo_name, e)

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
```

---

## SSL/TLS Support

### Configuration

```ini
[ssl]
enable = true
key_file = /path/to/server.key
cert_file = /path/to/server.crt
```

### Implementation

使用 Python 标准库 `ssl` 模块：

```python
import ssl

context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
context.load_cert_chain(
    certfile=server_config.ssl_cert_file,
    keyfile=server_config.ssl_key_file
)
socket = context.wrap_socket(raw_socket, server_side=True)
```

---

## Server Lifecycle

```
1. WebhookServer.__init__(config_path)
   ↓
2. ConfigLoader.load_file()
   ↓
3. ConfigurationRegistry._load_all_configs()
   ↓
4. WebhookServer._setup_logging()
   ↓
5. WebhookServer.create_http_server()
   ↓
6. WebhookRequestHandler.configure(inject dependencies)
   ↓
7. HTTPServer.serve_forever()
   ↓
8. For each POST request:
   - WebhookRequestHandler.do_POST()
   - Parse request → WebhookRequest
   - Identify provider
   - Create handler
   - Verify signature
   - Extract repository
   - Execute command
   - Send response
   ↓
9. On KeyboardInterrupt:
   - HTTPServer.shutdown()
```

---

## Error Handling

| Exception | HTTP Status | Error Message |
|-----------|-------------|---------------|
| RequestParseError | 400 | Bad Request |
| SignatureValidationError | 401 | Unauthorized |
| UnsupportedProviderError | 412 | Precondition Failed |
| UnsupportedEventError | 406 | Not Acceptable |
| ConfigurationError | 500 | Internal Server Error |
| Generic Exception | 500 | Internal Server Error |

---

## Logging

### Format

```
%(asctime)s %(message)s
```

### Example Output

```
2025-01-13 10:30:45 Serving on 0.0.0.0 port 6789...
2025-01-13 10:31:12 [owner/repo] Executing: git pull && ./deploy.sh
2025-01-13 10:31:15 [owner/repo] Execution completed with exit code 0
```

---

## Performance Considerations

1. **异步命令执行**: 使用 `subprocess.Popen` 不阻塞服务器
2. **连接处理**: HTTPServer 默认使用 `ThreadingMixIn`
3. **内存使用**: 每个请求独立处理，不共享状态
4. **日志写入**: 异步或缓冲写入（考虑未来优化）

---

## Testing Strategy

1. **集成测试**: 启动真实服务器，发送 HTTP 请求
2. **SSL 测试**: 测试 HTTPS 连接
3. **并发测试**: 测试多个同时请求
4. **错误处理测试**: 测试各种错误场景
5. **命令执行测试**: 验证命令被正确执行

---

## Module Exports

**File**: `gitwebhooks/server.py`

```python
from .server import WebhookServer
from .handlers.request import WebhookRequestHandler

__all__ = ['WebhookServer', 'WebhookRequestHandler']
```
