# Data Model: 优化 git-webhooks-server.py 代码质量

**Feature**: 优化 git-webhooks-server.py 代码质量和规范性
**Date**: 2025-01-13
**Phase**: Phase 1 - Design & Artifacts

## Overview

本文档定义代码重构后的内部数据结构和实体。注意，这是内部实现的数据模型，不涉及外部 API 或持久化存储。

## Core Entities

### 1. Provider (枚举)

表示支持的 Git 平台类型。

```python
from enum import Enum, unique

@unique
class Provider(Enum):
    """Git 平台类型枚举。"""
    GITHUB = "github"
    GITEE = "gitee"
    GITLAB = "gitlab"
    CUSTOM = "custom"
```

**Attributes**:
- 枚举值用于配置节名称（如 `[github]`）
- 保证唯一性（`@unique` 装饰器）

**Validation**:
- 枚举值必须与配置文件中的节名匹配
- 自定义平台允许动态扩展

---

### 2. WebhookRequest (数据类)

表示一个完整的 webhook 请求。

```python
from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass
class WebhookRequest:
    """Webhook 请求数据容器。"""
    provider: Provider
    event: Optional[str]
    payload: bytes
    headers: Dict[str, str]
    post_data: Optional[Dict[str, Any]]
    content_type: str
    content_length: int

    @property
    def repo_identifier(self) -> Optional[str]:
        """从 post_data 提取仓库标识符。"""
        if self.post_data is None:
            return None

        extractors = {
            Provider.GITHUB: lambda d: d.get('repository', {}).get('full_name'),
            Provider.GITEE: lambda d: d.get('repository', {}).get('full_name'),
            Provider.GITLAB: lambda d: d.get('project', {}).get('path_with_namespace'),
            Provider.CUSTOM: self._extract_custom_identifier,
        }

        extractor = extractors.get(self.provider)
        return extractor(self.post_data) if extractor else None

    def _extract_custom_identifier(self, data: Dict[str, Any]) -> Optional[str]:
        """从自定义路径提取标识符（需要配置）。"""
        # 实现由配置的 identifier_path 驱动
        pass
```

**Attributes**:
- `provider`: Git 平台类型
- `event`: 事件类型（如 "push", "merge_request"）
- `payload`: 原始请求体字节（用于签名验证）
- `headers`: HTTP 请求头
- `post_data`: 解析后的 JSON/表单数据
- `content_type`: Content-Type 头值
- `content_length`: Content-Length 头值

**Validation Rules**:
- `payload` 必须是原始字节（签名验证需要）
- `content_length` 必须与 `payload` 长度匹配
- `post_data` 可能为 None（解析失败时）

---

### 3. ProviderConfig (配置类)

单个平台的配置信息。

```python
@dataclass
class ProviderConfig:
    """平台配置容器。"""
    provider: Provider
    verify: bool
    secret: str
    handle_events: list

    @classmethod
    def from_config_parser(cls, parser: ConfigParser, provider: Provider) -> 'ProviderConfig':
        """从 ConfigParser 加载平台配置。"""
        section = provider.value
        return cls(
            provider=provider,
            verify=parser.getboolean(section, 'verify', fallback=False),
            secret=parser.get(section, 'secret', fallback=''),
            handle_events=cls._parse_event_list(parser.get(section, 'handle_events', fallback=''))
        )

    @staticmethod
    def _parse_event_list(value: str) -> list:
        """解析逗号分隔的事件列表。"""
        return [e.strip() for e in value.split(',') if e.strip()]
```

**Attributes**:
- `provider`: 平台类型
- `verify`: 是否验证签名/token
- `secret`: 密钥或密码
- `handle_events`: 允许处理的事件列表（空列表表示全部）

**Validation Rules**:
- `secret` 当 `verify=True` 时不能为空
- `handle_events` 中的事件名不区分大小写
- 配置缺失时使用合理的默认值

---

### 4. RepositoryConfig (配置类)

单个仓库的部署配置。

```python
@dataclass
class RepositoryConfig:
    """仓库部署配置容器。"""
    name: str
    cwd: str
    cmd: str

    @classmethod
    def from_config_parser(cls, parser: ConfigParser, name: str) -> Optional['RepositoryConfig']:
        """从 ConfigParser 加载仓库配置。"""
        try:
            return cls(
                name=name,
                cwd=parser.get(name, 'cwd'),
                cmd=parser.get(name, 'cmd')
            )
        except NoOptionError:
            return None
```

**Attributes**:
- `name`: 仓库名称（如 "owner/repo"）
- `cwd`: 执行命令的工作目录
- `cmd`: 要执行的 shell 命令

**Validation Rules**:
- `cwd` 必须是存在的绝对路径
- `cmd` 不能为空
- 配置缺失关键项时返回 None

---

### 5. SignatureVerificationResult (结果类)

签名验证结果。

```python
@dataclass
class SignatureVerificationResult:
    """签名验证结果。"""
    is_valid: bool
    error_message: Optional[str] = None

    @classmethod
    def success(cls) -> 'SignatureVerificationResult':
        """创建成功结果。"""
        return cls(is_valid=True)

    @classmethod
    def failure(cls, message: str) -> 'SignatureVerificationResult':
        """创建失败结果。"""
        return cls(is_valid=False, error_message=message)
```

**Attributes**:
- `is_valid`: 验证是否通过
- `error_message`: 失败原因描述（成功时为 None）

---

### 6. WebhookServer (主应用类)

重构后的主应用类，管理配置和请求处理。

```python
class WebhookServer:
    """Webhook 服务器主类。"""

    def __init__(self, config_path: str, address: str = '0.0.0.0', port: int = 6789):
        """初始化服务器。

        Args:
            config_path: 配置文件路径
            address: 监听地址
            port: 监听端口
        """
        self.config_path = config_path
        self.config = self._load_config(config_path)
        self.address = address
        self.port = port
        self.provider_configs = self._load_provider_configs()
        self.repository_configs = self._load_repository_configs()
        self._setup_logging()

    def _load_config(self, path: str) -> ConfigParser:
        """加载配置文件。"""
        parser = ConfigParser()
        parser.read(path)
        return parser

    def _load_provider_configs(self) -> Dict[Provider, ProviderConfig]:
        """加载所有平台配置。"""
        return {
            provider: ProviderConfig.from_config_parser(self.config, provider)
            for provider in Provider
        }

    def _load_repository_configs(self) -> Dict[str, RepositoryConfig]:
        """加载所有仓库配置。"""
        configs = {}
        for section in self.config.sections():
            if section not in ['server', 'ssl', 'github', 'gitee', 'gitlab', 'custom']:
                config = RepositoryConfig.from_config_parser(self.config, section)
                if config:
                    configs[section] = config
        return configs

    def create_http_server(self) -> HTTPServer:
        """创建并配置 HTTP 服务器。"""
        handler_factory = self._create_handler_factory()
        server = HTTPServer((self.address, self.port), handler_factory)

        if self._is_ssl_enabled():
            server.socket = self._wrap_ssl(server.socket)

        return server

    def _create_handler_factory(self):
        """创建请求处理器工厂函数。"""
        def handler_class(*args, **kwargs):
            return ConfiguredRequestHandler(
                self.config,
                self.provider_configs,
                self.repository_configs,
                *args,
                **kwargs
            )
        return handler_class

    def run(self):
        """启动服务器主循环。"""
        server = self.create_http_server()
        logging.info(f'Serving on {self.address} port {self.port}...')
        server.serve_forever()
```

---

## State Transitions

### 请求处理流程

```
HTTP Request
    ↓
Parse Provider & Event
    ↓
Parse Request Body
    ↓
Verify Signature (if enabled)
    ↓
Extract Repository Identifier
    ↓
Find Repository Config
    ↓
Execute Command
    ↓
Send Response
```

### 错误状态转换

```
Normal Processing
    ↓ [Signature Invalid]
401 Unauthorized
    ↓
Log Error

Normal Processing
    ↓ [Event Not Allowed]
406 Not Acceptable
    ↓
Log Warning

Normal Processing
    ↓ [Repository Not Found]
404 Not Found
    ↓
Log Warning

Normal Processing
    ↓ [Parse Error]
400 Bad Request
    ↓
Log Warning
```

---

## Relationships

```
WebhookServer
    ├── contains → Dict[Provider, ProviderConfig]
    ├── contains → Dict[str, RepositoryConfig]
    └── creates → ConfiguredRequestHandler

ConfiguredRequestHandler
    ├── references → ProviderConfig
    ├── references → RepositoryConfig
    └── processes → WebhookRequest

WebhookRequest
    ├── contains → Provider
    ├── contains → bytes (payload)
    └── contains → Dict[str, Any] (post_data)
```

---

## Validation Rules Summary

| Entity | Validation Rule | Error Handling |
|--------|----------------|----------------|
| Provider | 枚举值必须存在于配置 | `UnsupportedProviderError` |
| WebhookRequest | payload 长度匹配 content-length | `BadRequestError` |
| ProviderConfig | verify=True 时 secret 非空 | `ConfigurationError` |
| RepositoryConfig | cwd 存在且可读，cmd 非空 | `ConfigurationError` |
| SignatureVerificationResult | 验证失败时包含错误消息 | 记录日志，返回 401 |

---

## Type Annotations Summary

所有公共 API 都包含完整的类型提示：

```python
from typing import Optional, Dict, List, Tuple, Any, Callable

def parse_provider(headers: Dict[str, str]) -> Optional[Tuple[Provider, Optional[str]]: ...
def verify_signature(...) -> SignatureVerificationResult: ...
def extract_repository(...) -> Optional[str]: ...
def execute_deployment(...) -> None: ...
```

---

## Notes

1. **单文件约束**: 所有类定义都在 `git-webhooks-server.py` 单文件中
2. **向后兼容**: 配置文件格式保持不变，仅改变代码内部结构
3. **测试友好**: 所有组件都可以通过依赖注入进行单元测试
4. **类型安全**: 使用 mypy 进行静态类型检查
