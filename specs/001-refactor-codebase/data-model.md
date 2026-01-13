# Data Model

**Feature**: 代码库重构 - 模块化拆分与项目结构重组
**Date**: 2025-01-13
**Phase**: Phase 1 - Design & Contracts

## Overview

本文档定义 Git Webhooks Server 的核心数据模型。基于现有单文件代码的分析，将数据类组织为清晰的层次结构，使用 Python 标准库的 `dataclass` 和 `Enum`。

---

## Entity Relationships

```
┌─────────────────┐
│  Provider       │
│  (Enum)         │
└────────┬────────┘
         │
         │ used by
         ▼
┌─────────────────────────────────────────────────┐
│           ProviderConfig                         │
│  ┌─────────────────────────────────────────┐    │
│  │ provider: Provider                       │    │
│  │ verify: bool                             │    │
│  │ secret: str                              │    │
│  │ handle_events: List[str]                 │    │
│  │ header_name: str (custom only)           │    │
│  │ header_value: str (custom only)          │    │
│  │ header_event: str (custom only)          │    │
│  │ header_token: str (custom only)          │    │
│  │ identifier_path: str (custom only)       │    │
│  └─────────────────────────────────────────┘    │
└─────────────────────────────────────────────────┘
         │
         │ loads
         ▼
┌─────────────────────────────────────────────────┐
│         RepositoryConfig                         │
│  ┌─────────────────────────────────────────┐    │
│  │ name: str                                │    │
│  │ cwd: str                                 │    │
│  │ cmd: str                                 │    │
│  └─────────────────────────────────────────┘    │
└─────────────────────────────────────────────────┘
         │
         │ processes
         ▼
┌─────────────────────────────────────────────────┐
│          WebhookRequest                          │
│  ┌─────────────────────────────────────────┐    │
│  │ provider: Provider                       │    │
│  │ event: Optional[str]                     │    │
│  │ payload: bytes                           │    │
│  │ headers: Dict[str, str]                  │    │
│  │ post_data: Optional[Dict[str, Any]]      │    │
│  │ content_type: str                        │    │
│  │ content_length: int                      │    │
│  │ repo_identifier: Optional[str] (prop)    │    │
│  └─────────────────────────────────────────┘    │
└─────────────────────────────────────────────────┘
         │
         │ verifies
         ▼
┌─────────────────────────────────────────────────┐
│   SignatureVerificationResult                    │
│  ┌─────────────────────────────────────────┐    │
│  │ is_valid: bool                           │    │
│  │ error_message: Optional[str]             │    │
│  │ + success(): SignatureVerificationResult │    │
│  │ + failure(msg): SignatureVerificationResult│   │
│  └─────────────────────────────────────────┘    │
└─────────────────────────────────────────────────┘
```

---

## Core Entities

### 1. Provider (Enum)

**Module**: `gitwebhooks.models.provider`

**Description**: Git 平台提供者枚举

```python
from enum import Enum, unique

@unique
class Provider(Enum):
    """Git 平台提供者类型

    支持的 Git 托管平台：
    - GITHUB: Github 平台
    - GITEE: Gitee 平台（中国）
    - GITLAB: Gitlab 平台
    - CUSTOM: 自定义 webhook 平台
    """
    GITHUB = 'github'
    GITEE = 'gitee'
    GITLAB = 'gitlab'
    CUSTOM = 'custom'
```

**Validation Rules**:
- 枚举值小写，与配置文件中的节名一致
- 使用 `@unique` 装饰器确保值唯一

**Relationships**:
- 被 `ProviderConfig` 使用
- 被所有 `WebhookHandler` 子类使用

---

### 2. SignatureVerificationResult (Dataclass)

**Module**: `gitwebhooks.models.result`

**Description**: 签名验证结果

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class SignatureVerificationResult:
    """签名验证结果

    Attributes:
        is_valid: 验证是否通过
        error_message: 验证失败时的错误描述
    """
    is_valid: bool
    error_message: Optional[str] = None

    @classmethod
    def success(cls) -> 'SignatureVerificationResult':
        """创建成功的验证结果

        Returns:
            is_valid=True 的结果对象
        """
        return cls(is_valid=True)

    @classmethod
    def failure(cls, message: str) -> 'SignatureVerificationResult':
        """创建失败的验证结果

        Args:
            message: 错误描述

        Returns:
            is_valid=False 且包含错误消息的结果对象
        """
        return cls(is_valid=False, error_message=message)
```

**Validation Rules**:
- 当 `is_valid=False` 时，`error_message` 应该非空
- 当 `is_valid=True` 时，`error_message` 应该为 `None`

**State Transitions**:
```
Initial → success() → is_valid=True, error_message=None
Initial → failure(msg) → is_valid=False, error_message=msg
```

---

### 3. ProviderConfig (Dataclass)

**Module**: `gitwebhooks.config.models`

**Description**: Git 平台提供者配置

```python
from dataclasses import dataclass
from typing import List
from gitwebhooks.models.provider import Provider

@dataclass
class ProviderConfig:
    """Git 平台提供者配置

    Attributes:
        provider: 提供者类型
        verify: 是否验证签名/token
        secret: 验证用的密钥
        handle_events: 要处理的事件列表（空列表=处理所有事件）
        header_name: 自定义识别 header（仅 CUSTOM）
        header_value: 自定义识别值（仅 CUSTOM）
        header_event: 自定义事件 header（仅 CUSTOM）
        header_token: 自定义 token header（仅 CUSTOM）
        identifier_path: 仓库标识符 JSON 路径（仅 CUSTOM）
    """
    provider: Provider
    verify: bool
    secret: str
    handle_events: List[str]

    # Custom provider only
    header_name: str = ''
    header_value: str = ''
    header_event: str = ''
    header_token: str = ''
    identifier_path: str = ''

    @classmethod
    def from_config_parser(cls, parser: configparser.ConfigParser,
                          provider: Provider) -> 'ProviderConfig':
        """从 ConfigParser 加载提供者配置

        Args:
            parser: ConfigParser 实例
            provider: 提供者类型

        Returns:
            ProviderConfig 实例

        Raises:
            configparser.NoSectionError: 配置节不存在
        """
        section = provider.value
        handle_events_str = parser.get(section, 'handle_events',
                                       fallback='').strip()
        handle_events = [e.strip() for e in handle_events_str.split(',')
                        if e.strip()] if handle_events_str else []

        config = cls(
            provider=provider,
            verify=parser.getboolean(section, 'verify', fallback=False),
            secret=parser.get(section, 'secret', fallback=''),
            handle_events=handle_events
        )

        # Custom provider 额外字段
        if provider == Provider.CUSTOM:
            config.header_name = parser.get(section, 'header_name',
                                           fallback='X-Custom-Webhook')
            config.header_value = parser.get(section, 'header_value',
                                            fallback='custom')
            config.header_event = parser.get(section, 'header_event',
                                            fallback='X-Custom-Event')
            config.header_token = parser.get(section, 'header_token',
                                            fallback='X-Custom-Token')
            config.identifier_path = parser.get(section, 'identifier_path',
                                               fallback='')

        return config

    def allows_event(self, event: Optional[str]) -> bool:
        """检查事件是否被允许处理

        Args:
            event: 事件类型（None 表示所有事件）

        Returns:
            True 如果事件被允许，False 否则
        """
        if not self.handle_events:
            return True  # 空列表 = 处理所有事件
        return event in self.handle_events
```

**Validation Rules**:
- `handle_events` 中的字符串去除前后空格
- `verify=True` 时，`secret` 应该非空（运行时检查）

**Conditional Fields**:
- `header_*` 和 `identifier_path` 仅在 `provider == Provider.CUSTOM` 时使用

---

### 4. RepositoryConfig (Dataclass)

**Module**: `gitwebhooks.config.models`

**Description**: 仓库部署配置

```python
from dataclasses import dataclass

@dataclass
class RepositoryConfig:
    """仓库部署配置

    Attributes:
        name: 仓库名称（格式：'owner/repo' 或 'group/project/repo'）
        cwd: 部署命令执行的工作目录
        cmd: 部署命令（shell 字符串）
    """
    name: str
    cwd: str
    cmd: str

    @classmethod
    def from_config_parser(cls, parser: configparser.ConfigParser,
                          name: str) -> Optional['RepositoryConfig']:
        """从 ConfigParser 加载仓库配置

        Args:
            parser: ConfigParser 实例
            name: 配置节名称（仓库名称）

        Returns:
            RepositoryConfig 实例，如果节不存在则返回 None

        Raises:
            configparser.NoOptionError: 节存在但缺少必需选项
        """
        if not parser.has_section(name):
            return None

        return cls(
            name=name,
            cwd=parser.get(name, 'cwd'),
            cmd=parser.get(name, 'cmd')
        )

    def validate(self) -> None:
        """验证配置有效性

        Raises:
            ConfigurationError: 配置无效
        """
        if not self.cwd:
            raise ConfigurationError(f'Repository {self.name}: cwd is required')
        if not self.cmd:
            raise ConfigurationError(f'Repository {self.name}: cmd is required')
```

**Validation Rules**:
- `name` 不能是保留节名（server, ssl, github, gitee, gitlab, custom）
- `cwd` 必须是有效目录路径（运行时验证）
- `cmd` 必须是非空字符串

---

### 5. ServerConfig (Dataclass)

**Module**: `gitwebhooks.config.server`

**Description**: 服务器配置

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class ServerConfig:
    """服务器配置

    Attributes:
        address: 监听地址
        port: 监听端口
        log_file: 日志文件路径（空字符串表示不记录到文件）
        ssl_enabled: 是否启用 SSL
        ssl_key_file: SSL 密钥文件路径
        ssl_cert_file: SSL 证书文件路径
    """
    address: str
    port: int
    log_file: str
    ssl_enabled: bool = False
    ssl_key_file: Optional[str] = None
    ssl_cert_file: Optional[str] = None

    @classmethod
    def from_loader(cls, loader: 'ConfigLoader') -> 'ServerConfig':
        """从 ConfigLoader 创建服务器配置

        Args:
            loader: 配置加载器实例

        Returns:
            ServerConfig 实例
        """
        server_cfg = loader.get_server_config()
        ssl_cfg = loader.get_ssl_config()

        return cls(
            address=server_cfg['address'],
            port=server_cfg['port'],
            log_file=server_cfg['log_file'],
            ssl_enabled=ssl_cfg is not None,
            ssl_key_file=ssl_cfg['key_file'] if ssl_cfg else None,
            ssl_cert_file=ssl_cfg['cert_file'] if ssl_cfg else None,
        )

    def validate(self) -> None:
        """验证服务器配置

        Raises:
            ConfigurationError: 配置无效
        """
        if self.ssl_enabled:
            if not self.ssl_key_file:
                raise ConfigurationError('SSL enabled but key_file not specified')
            if not self.ssl_cert_file:
                raise ConfigurationError('SSL enabled but cert_file not specified')

        # 验证端口范围
        if not (1 <= self.port <= 65535):
            raise ConfigurationError(f'Invalid port number: {self.port}')
```

**Validation Rules**:
- 端口范围: 1-65535
- SSL 启用时必须提供 key_file 和 cert_file
- SSL 文件必须存在（运行时验证）

---

### 6. WebhookRequest (Dataclass)

**Module**: `gitwebhooks.models.request`

**Description**: Webhook 请求数据封装

```python
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
```

**Validation Rules**:
- `content_length` 应该等于 `len(payload)`
- `payload` 应该能根据 `content_type` 解析为 `post_data`

**Derived Values**:
- `repo_identifier`: 动态计算的属性，不是存储的字段

---

## Constants

**Module**: `gitwebhooks.utils.constants`

```python
# HTTP Status Codes
HTTP_OK = 200
HTTP_BAD_REQUEST = 400
HTTP_UNAUTHORIZED = 401
HTTP_FORBIDDEN = 403
HTTP_NOT_FOUND = 404
HTTP_NOT_ACCEPTABLE = 406
HTTP_PRECONDITION_FAILED = 412
HTTP_INTERNAL_SERVER_ERROR = 500

# HTTP Content Types
CONTENT_TYPE_JSON = 'application/json'
CONTENT_TYPE_FORM_URLENCODED = 'application/x-www-form-urlencoded'

# HTTP Headers
HEADER_CONTENT_TYPE = 'Content-Type'
HEADER_CONTENT_LENGTH = 'Content-Length'
HEADER_GITHUB_EVENT = 'X-GitHub-Event'
HEADER_GITHUB_SIGNATURE = 'X-Hub-Signature'
HEADER_GITEE_EVENT = 'X-Gitee-Event'
HEADER_GITEE_TOKEN = 'X-Gitee-Token'
HEADER_GITEE_TIMESTAMP = 'X-Gitee-Timestamp'
HEADER_GITLAB_EVENT = 'X-Gitlab-Event'
HEADER_GITLAB_TOKEN = 'X-Gitlab-Token'

# Response Messages
MESSAGE_OK = b'OK'
MESSAGE_FORBIDDEN = 'Forbidden'
MESSAGE_BAD_REQUEST = 'Bad Request'
MESSAGE_UNAUTHORIZED = 'Unauthorized'
MESSAGE_NOT_FOUND = 'Not Found'
MESSAGE_NOT_ACCEPTABLE = 'Not Acceptable'
MESSAGE_PRECONDITION_FAILED = 'Precondition Failed'
MESSAGE_INTERNAL_SERVER_ERROR = 'Internal Server Error'

# Reserved configuration sections
RESERVED_SECTIONS = {'server', 'ssl', 'github', 'gitee', 'gitlab', 'custom'}
```

---

## Exception Hierarchy

**Module**: `gitwebhooks.utils.exceptions`

```python
class WebhookError(Exception):
    """Webhook 处理错误基类"""
    pass

class SignatureValidationError(WebhookError):
    """签名验证失败"""
    pass

class UnsupportedEventError(WebhookError):
    """不支持的事件类型"""
    pass

class UnsupportedProviderError(WebhookError):
    """无法识别的平台提供者"""
    pass

class ConfigurationError(WebhookError):
    """配置错误或缺失"""
    pass

class RequestParseError(WebhookError):
    """请求解析失败"""
    pass
```

---

## Data Flow

```
1. ConfigParser (INI file)
   ↓
2. ProviderConfig.repository (per provider)
   RepositoryConfig (per repository section)
   ↓
3. WebhookServer (holds configs)
   ↓
4. HTTP Request received
   ↓
5. WebhookRequest created (parsed from HTTP)
   ↓
6. Handler.get_provider() → Provider
   ↓
7. ProviderConfig.for_provider(provider)
   ↓
8. Handler.verify_signature() → SignatureVerificationResult
   ↓
9. Handler.extract_repository() → repo_identifier
   ↓
10. RepositoryConfig.for_name(repo_identifier)
    ↓
11. Executor.run_command(repo_config.cmd, repo_config.cwd)
```

---

## Type Hints

所有数据类使用完整的类型提示：

```python
from typing import Any, Dict, List, Optional, Tuple

def example_function(
    required: str,
    optional: Optional[str] = None,
    multiple: List[str] = None
) -> bool:
    """使用类型提示的示例"""
    pass
```

---

## Next Steps

Phase 1 继续：
1. `contracts/` - 模块接口详细定义
2. `quickstart.md` - 开发者快速入门指南
3. Agent Context Update
