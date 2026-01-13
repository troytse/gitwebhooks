# Config Module Contract

**Module**: `gitwebhooks.config`
**Version**: 1.0.0
**Status**: Design Phase

## Overview

配置管理模块负责加载、解析和管理 INI 格式的配置文件。提供类型安全的配置对象和验证机制。

---

## Config Parser Contract

**Class**: `ConfigLoader`
**Module**: `gitwebhooks.config.loader`
**Type**: Service class

```python
from configparser import ConfigParser
from typing import Dict, Optional
from pathlib import Path

from gitwebhooks.config.models import ProviderConfig, RepositoryConfig
from gitwebhooks.models.provider import Provider
from gitwebhooks.utils.exceptions import ConfigurationError

class ConfigLoader:
    """配置加载器

    负责从 INI 文件加载和验证配置
    """

    def __init__(self, config_path: str):
        """初始化配置加载器

        Args:
            config_path: INI 配置文件路径

        Raises:
            ConfigurationError: 文件不存在或无法解析
        """
        self.config_path = Path(config_path)
        self.parser = ConfigParser()
        self._load_file()

    def _load_file(self) -> None:
        """加载配置文件

        Raises:
            ConfigurationError: 文件不存在或解析失败
        """
        if not self.config_path.exists():
            raise ConfigurationError(f'Config file not found: {self.config_path}')

        try:
            self.parser.read(str(self.config_path))
        except (configparser.Error, UnicodeDecodeError) as e:
            raise ConfigurationError(f'Failed to parse config: {e}')

    def load_provider_config(self, provider: Provider) -> ProviderConfig:
        """加载指定提供者的配置

        Args:
            provider: 提供者类型

        Returns:
            ProviderConfig 实例

        Raises:
            ConfigurationError: 配置节不存在
        """
        try:
            return ProviderConfig.from_config_parser(self.parser, provider)
        except configparser.NoSectionError:
            # 返回默认配置
            return ProviderConfig(
                provider=provider,
                verify=False,
                secret='',
                handle_events=[]
            )

    def load_all_provider_configs(self) -> Dict[Provider, ProviderConfig]:
        """加载所有提供者配置

        Returns:
            提供者到配置的映射
        """
        configs = {}
        for provider in Provider:
            configs[provider] = self.load_provider_config(provider)
        return configs

    def load_repository_config(self, name: str) -> Optional[RepositoryConfig]:
        """加载指定仓库的配置

        Args:
            name: 仓库名称（配置节名称）

        Returns:
            RepositoryConfig 实例，如果节不存在返回 None
        """
        return RepositoryConfig.from_config_parser(self.parser, name)

    def load_all_repository_configs(self) -> Dict[str, RepositoryConfig]:
        """加载所有仓库配置

        Returns:
            仓库名称到配置的映射

        Note:
            跳过保留节名: server, ssl, github, gitee, gitlab, custom
        """
        configs = {}
        reserved_sections = self._get_reserved_sections()

        for section in self.parser.sections():
            if section not in reserved_sections:
                repo_config = self.load_repository_config(section)
                if repo_config is not None:
                    configs[section] = repo_config

        return configs

    def _get_reserved_sections(self) -> set:
        """获取保留的配置节名称

        Returns:
            保留节名集合
        """
        return {'server', 'ssl', 'github', 'gitee', 'gitlab', 'custom'}

    def get_server_config(self) -> Dict[str, any]:
        """获取服务器配置

        Returns:
            包含 server 配置的字典，键包括:
            - address: 监听地址
            - port: 监听端口
            - log_file: 日志文件路径
        """
        return {
            'address': self.parser.get('server', 'address', fallback='0.0.0.0'),
            'port': self.parser.getint('server', 'port', fallback=6789),
            'log_file': self.parser.get('server', 'log_file', fallback='').strip(),
        }

    def get_ssl_config(self) -> Optional[Dict[str, str]]:
        """获取 SSL 配置

        Returns:
            包含 SSL 配置的字典，如果未启用则返回 None
            键包括:
            - enable: 是否启用 SSL
            - key_file: SSL 密钥文件路径
            - cert_file: SSL 证书文件路径
        """
        try:
            if not self.parser.getboolean('ssl', 'enable'):
                return None
        except (configparser.NoSectionError, ValueError):
            return None

        return {
            'enable': True,
            'key_file': self.parser.get('ssl', 'key_file'),
            'cert_file': self.parser.get('ssl', 'cert_file'),
        }

    def validate_repository_configs(self) -> None:
        """验证所有仓库配置

        Raises:
            ConfigurationError: 配置无效
        """
        configs = self.load_all_repository_configs()

        for name, config in configs.items():
            try:
                config.validate()
            except ConfigurationError as e:
                raise ConfigurationError(f'Repository {name}: {e}')
```

---

## Configuration Models Contract

### ProviderConfig

**File**: `gitwebhooks/config/models.py`
**Reference**: See `data-model.md` for full definition

Key methods:
- `from_config_parser(parser, provider)`: 从 ConfigParser 创建实例
- `allows_event(event)`: 检查事件是否被允许

### RepositoryConfig

**File**: `gitwebhooks/config/models.py`
**Reference**: See `data-model.md` for full definition

Key methods:
- `from_config_parser(parser, name)`: 从 ConfigParser 创建实例
- `validate()`: 验证配置有效性

---

## Server Configuration Contract

**Class**: `ServerConfig`
**Module**: `gitwebhooks.config.server` (文件: `gitwebhooks/config/server.py`)
**Type**: Dataclass

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
    def from_loader(cls, loader: ConfigLoader) -> 'ServerConfig':
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

            # 验证文件存在
            key_path = Path(self.ssl_key_file)
            cert_path = Path(self.ssl_cert_file)

            if not key_path.exists():
                raise ConfigurationError(f'SSL key file not found: {self.ssl_key_file}')
            if not cert_path.exists():
                raise ConfigurationError(f'SSL cert file not found: {self.ssl_cert_file}')

        # 验证端口范围
        if not (1 <= self.port <= 65535):
            raise ConfigurationError(f'Invalid port number: {self.port}')

        # 验证日志文件可写（如果指定）
        if self.log_file:
            log_path = Path(self.log_file)
            parent_dir = log_path.parent
            if parent_dir.exists() and not os.access(parent_dir, os.W_OK):
                raise ConfigurationError(f'Log directory not writable: {parent_dir}')
```

---

## Configuration Registry Contract

**Class**: `ConfigurationRegistry`
**Module**: `gitwebhooks.config`
**Type**: Service class

```python
class ConfigurationRegistry:
    """配置注册表

    持有所有配置并提供访问接口
    """

    def __init__(self, loader: ConfigLoader):
        """初始化配置注册表

        Args:
            loader: 配置加载器实例
        """
        self.loader = loader
        self._server_config: Optional[ServerConfig] = None
        self._provider_configs: Optional[Dict[Provider, ProviderConfig]] = None
        self._repository_configs: Optional[Dict[str, RepositoryConfig]] = None
        self._load_all_configs()

    def _load_all_configs(self) -> None:
        """加载所有配置

        Raises:
            ConfigurationError: 配置加载或验证失败
        """
        self._server_config = ServerConfig.from_loader(self.loader)
        self._server_config.validate()

        self._provider_configs = self.loader.load_all_provider_configs()
        self._repository_configs = self.loader.load_all_repository_configs()

        self.loader.validate_repository_configs()

    @property
    def server_config(self) -> ServerConfig:
        """获取服务器配置"""
        if self._server_config is None:
            raise ConfigurationError('Server config not loaded')
        return self._server_config

    @property
    def provider_configs(self) -> Dict[Provider, ProviderConfig]:
        """获取提供者配置字典"""
        if self._provider_configs is None:
            raise ConfigurationError('Provider configs not loaded')
        return self._provider_configs

    @property
    def repository_configs(self) -> Dict[str, RepositoryConfig]:
        """获取仓库配置字典"""
        if self._repository_configs is None:
            raise ConfigurationError('Repository configs not loaded')
        return self._repository_configs

    def get_provider_config(self, provider: Provider) -> ProviderConfig:
        """获取指定提供者的配置

        Args:
            provider: 提供者类型

        Returns:
            ProviderConfig 实例
        """
        return self.provider_configs.get(provider, ProviderConfig(
            provider=provider,
            verify=False,
            secret='',
            handle_events=[]
        ))

    def get_repository_config(self, name: str) -> Optional[RepositoryConfig]:
        """获取指定仓库的配置

        Args:
            name: 仓库名称

        Returns:
            RepositoryConfig 实例，未找到返回 None
        """
        return self.repository_configs.get(name)

    def has_repository(self, name: str) -> bool:
        """检查仓库是否存在

        Args:
            name: 仓库名称

        Returns:
            True 如果存在，False 否则
        """
        return name in self.repository_configs
```

---

## Module Exports

**File**: `gitwebhooks/config/__init__.py`

```python
from .loader import ConfigLoader
from .models import ProviderConfig, RepositoryConfig
from .server import ServerConfig
from .registry import ConfigurationRegistry

__all__ = [
    'ConfigLoader',
    'ProviderConfig',
    'RepositoryConfig',
    'ServerConfig',
    'ConfigurationRegistry',
]
```

---

## Configuration File Format

### Example INI Structure

```ini
[server]
address = 0.0.0.0
port = 6789
log_file = /var/log/git-webhooks-server.log

[ssl]
enable = true
key_file = /path/to/server.key
cert_file = /path/to/server.crt

[github]
verify = true
secret = your_github_webhook_secret
handle_events = push,pull_request

[gitee]
verify = true
secret = your_gitee_webhook_password
handle_events = Push Hook

[gitlab]
verify = true
secret = your_gitlab_webhook_token
handle_events =

[custom]
verify = false
secret =
handle_events =
header_name = X-Custom-Webhook
header_value = my-service
header_event = X-Custom-Event
header_token = X-Custom-Token
identifier_path = project.full_name

[owner/repository]
cwd = /path/to/repository
cmd = git pull && ./deploy.sh

[group/project]
cwd = /var/www/project
cmd = /usr/local/bin/rebuild.sh
```

---

## Validation Rules

### Provider Configuration

| Field | Type | Required | Validation |
|-------|------|----------|------------|
| provider | Provider | Yes | Must be valid enum value |
| verify | bool | No | Default: false |
| secret | str | Conditional | Required if verify=true |
| handle_events | list | No | Empty list = all events |
| header_name | str | No | Custom provider only |
| header_value | str | No | Custom provider only |
| header_event | str | No | Custom provider only |
| header_token | str | No | Custom provider only |
| identifier_path | str | No | Custom provider only |

### Repository Configuration

| Field | Type | Required | Validation |
|-------|------|----------|------------|
| name | str | Yes | Not in reserved sections |
| cwd | str | Yes | Must be valid directory path |
| cmd | str | Yes | Non-empty string |

### Server Configuration

| Field | Type | Required | Validation |
|-------|------|----------|------------|
| address | str | No | Default: 0.0.0.0 |
| port | int | No | Range: 1-65535, Default: 6789 |
| log_file | str | No | Empty or writable path |
| ssl_enabled | bool | No | Default: false |
| ssl_key_file | str | Conditional | Required if ssl_enabled |
| ssl_cert_file | str | Conditional | Required if ssl_enabled |

---

## Error Handling

1. **文件不存在**: 抛出 `ConfigurationError` 并包含文件路径
2. **解析失败**: 抛出 `ConfigurationError` 并包含原始错误信息
3. **缺少必需字段**: 抛出 `configparser.NoOptionError`（由 ConfigParser 自动抛出）
4. **类型转换失败**: 抛出 `ValueError`（由 getboolean/getint 自动抛出）
5. **验证失败**: 抛出 `ConfigurationError` 并包含具体原因

---

## Testing Strategy

1. **加载器测试**: 测试各种配置文件格式
2. **验证测试**: 测试有效和无效配置
3. **默认值测试**: 测试可选字段的默认值
4. **错误处理测试**: 测试缺失文件、格式错误等情况
