# Research & Technical Decisions

**Feature**: 代码库重构 - 模块化拆分与项目结构重组
**Date**: 2025-01-13
**Phase**: Phase 0 - Research & Technical Decisions

## Overview

本文档记录代码库重构过程中的技术研究和决策。基于对现有单文件架构（1200+ 行）的分析，制定模块化重组的技术方案。

---

## Research Questions & Decisions

### RQ-001: Python 3.6 包结构最佳实践

**Question**: 在 Python 3.6+ 环境中，如何组织包结构以保持兼容性和简洁性？

**Decision**: 使用传统包结构（每个目录包含 `__init__.py`）

**Rationale**:
- Python 3.6 需要显式的 `__init__.py` 文件来标识包
- 传统包结构在所有 Python 版本中表现一致
- 明确的包边界有助于代码组织
- 空的 `__init__.py` 文件可以保留为占位符，或用于导出公共 API

**Alternatives Considered**:
- **命名空间包（PEP 420）**: 不适用，需要 Python 3.3+
- **单一扁平模块**: 不符合模块化目标

**Implementation Guidance**:
```python
# gitwebhooks/__init__.py
"""Git Webhooks Server - Modular package structure."""

# 导出主要类，提供便利的导入路径
from .server import WebhookServer
from .models.provider import Provider
from .models.request import WebhookRequest

__all__ = ['WebhookServer', 'Provider', 'WebhookRequest']
```

---

### RQ-002: 依赖注入模式实现方式

**Question**: 在无外部依赖的约束下，如何实现依赖注入模式？

**Decision**: 使用构造函数注入 + 工厂模式

**Rationale**:
- 构造函数注入是 Python 标准库中最直接的方式
- 不需要引入 DI 框架
- 类型提示（typing）提供良好的 IDE 支持
- 工厂模式集中管理依赖关系

**Alternatives Considered**:
- **全局单例模式**: 违反"消除全局状态"的目标
- **属性注入**: 使对象状态不一致，难以测试
- **第三方 DI 框架**: 违反"无外部依赖"约束

**Implementation Pattern**:
```python
# 配置对象作为依赖传递
class WebhookServer:
    def __init__(self, config_path: str, provider_registry: ProviderRegistry,
                 repository_registry: RepositoryRegistry):
        self.config_path = config_path
        self.provider_registry = provider_registry
        self.repository_registry = repository_registry
        self.config = self._load_config()
        self._setup_logging()

# 工厂创建依赖
class ServerFactory:
    @staticmethod
    def create_server(config_path: str) -> WebhookServer:
        config = configparser.ConfigParser()
        config.read(config_path)

        provider_registry = ProviderFactory.create_registry(config)
        repository_registry = RepositoryFactory.create_registry(config)

        return WebhookServer(config_path, provider_registry, repository_registry)
```

---

### RQ-003: 向后兼容性策略（一次性重写）

**Question**: 在一次性重写策略下，如何确保向后兼容性？

**Decision**: 保留命令行接口，内部迁移到新架构

**Rationale**:
- 命令行参数是用户的主要交互方式
- 配置文件格式保持不变（INI）
- HTTP 接口行为保持一致
- 服务器监听地址和端口配置不变

**Migration Strategy**:
1. **命令行兼容**: 新的 `gitwebhooks-cli` 接受相同的参数（`-c`, `--config`, `-h`）
2. **配置兼容**: 配置文件格式、节名称、选项名称完全一致
3. **行为兼容**: HTTP 响应代码、错误消息、日志格式保持一致
4. **测试兼容**: 所有现有测试用例无需修改即可通过

**Compatibility Matrix**:

| Aspect | Old Behavior | New Behavior | Compatible? |
|--------|--------------|--------------|-------------|
| CLI arguments | `-c config.ini` | `-c config.ini` | ✅ Yes |
| Config format | INI sections | INI sections | ✅ Yes |
| HTTP responses | 200/401/403/404/500 | 200/401/403/404/500 | ✅ Yes |
| Log format | `%(asctime)s %(message)s` | `%(asctime)s %(message)s` | ✅ Yes |
| Entry point | `git-webhooks-server.py` | `gitwebhooks-cli` | ⚠️ Path change |
| Internal API | Global `config` | DI + classes | ⚠️ Breaking (internal only) |

---

### RQ-004: 模块间接口设计

**Question**: 处理器、验证器、配置模块之间的接口如何设计？

**Decision**: 基于抽象基类（ABC）的接口定义

**Rationale**:
- Python `abc` 模块是标准库的一部分
- 强制子类实现必需方法
- 提供清晰的接口契约
- 便于单元测试（mock 接口）

**Interface Definitions**:

#### 1. 处理器接口（Handler）

```python
from abc import ABC, abstractmethod
from typing import Optional

from gitwebhooks.models.request import WebhookRequest
from gitwebhooks.models.result import SignatureVerificationResult

class WebhookHandler(ABC):
    """Webhook 处理器基类"""

    @abstractmethod
    def get_provider(self) -> Provider:
        """返回此处理器支持的提供者类型"""
        pass

    @abstractmethod
    def verify_signature(self, request: WebhookRequest) -> SignatureVerificationResult:
        """验证 webhook 签名"""
        pass

    @abstractmethod
    def extract_repository(self, request: WebhookRequest) -> Optional[str]:
        """从请求中提取仓库标识符"""
        pass

    @abstractmethod
    def is_event_allowed(self, event: Optional[str]) -> bool:
        """检查事件类型是否被允许处理"""
        pass
```

#### 2. 验证器接口（Verifier）

```python
class SignatureVerifier(ABC):
    """签名验证器基类"""

    @abstractmethod
    def verify(self, payload: bytes, signature: str, secret: str) -> SignatureVerificationResult:
        """验证签名"""
        pass
```

#### 3. 配置加载器接口（ConfigLoader）

```python
class ConfigLoader(ABC):
    """配置加载器基类"""

    @abstractmethod
    def load_provider_config(self, provider: Provider) -> ProviderConfig:
        """加载提供者配置"""
        pass

    @abstractmethod
    def load_repository_configs(self) -> Dict[str, RepositoryConfig]:
        """加载所有仓库配置"""
        pass
```

---

## Architecture Patterns

### 1. 分层架构（Layered Architecture）

```
┌─────────────────────────────────────┐
│         CLI Layer (cli.py)          │  入口点，参数解析
├─────────────────────────────────────┤
│      Server Layer (server.py)       │  HTTP 服务器，请求路由
├─────────────────────────────────────┤
│     Handler Layer (handlers/)       │  平台特定处理逻辑
├─────────────────────────────────────┤
│      Auth Layer (auth/)             │  签名/Token 验证
├─────────────────────────────────────┤
│     Config Layer (config/)          │  配置解析和加载
├─────────────────────────────────────┤
│     Model Layer (models/)           │  数据模型和枚举
└─────────────────────────────────────┘
```

### 2. 策略模式（Strategy Pattern）

不同平台的签名验证策略：
- `GithubHmacVerifier`: HMAC-SHA1
- `GiteeHmacVerifier`: HMAC-SHA256 with timestamp
- `GitlabTokenVerifier`: Simple token comparison
- `CustomTokenVerifier`: Configurable token header

### 3. 工厂模式（Factory Pattern）

处理器和验证器的创建：
- `HandlerFactory`: 根据请求 headers 创建对应的处理器
- `VerifierFactory`: 根据提供者类型创建验证器

---

## Code Organization Principles

### 单一职责原则（SRP）

每个模块只负责一个功能域：
- `handlers/`: 只处理 webhook 请求分发
- `auth/`: 只负责签名验证
- `config/`: 只负责配置管理
- `models/`: 只定义数据结构

### 依赖倒置原则（DIP）

高层模块不依赖低层模块，都依赖抽象：
- `server.py` 依赖 `WebhookHandler` 接口
- 不直接依赖 `github.py` 或 `gitlab.py`

### 开闭原则（OCP）

对扩展开放，对修改关闭：
- 添加新平台：创建新的 handler 和 verifier
- 不需要修改现有 `server.py` 代码

---

## Testing Strategy

### 单元测试结构

```
tests/
├── test_config/
│   ├── test_parser.py      # 配置解析测试
│   └── test_models.py      # 配置模型测试
├── test_handlers/
│   ├── test_base.py        # 基类测试
│   ├── test_github.py      # Github 处理器测试
│   ├── test_gitee.py       # Gitee 处理器测试
│   └── test_gitlab.py      # Gitlab 处理器测试
├── test_auth/
│   ├── test_github.py      # Github 签名验证测试
│   ├── test_gitee.py       # Gitee 签名验证测试
│   └── test_gitlab.py      # Gitlab token 验证测试
└── test_integration/
    └── test_server.py      # 完整请求流程测试
```

### 依赖注入的测试优势

```python
# 可以轻松 mock 依赖
def test_github_handler_with_mock_verifier():
    mock_verifier = Mock(spec=SignatureVerifier)
    mock_verifier.verify.return_value = SignatureVerificationResult.success()

    handler = GithubHandler(mock_verifier)
    result = handler.verify_request(mock_request)

    assert result.is_valid
    mock_verifier.verify.assert_called_once()
```

---

## Performance Considerations

### 目标：保持现有性能水平

1. **导入开销**: 按需导入，避免循环依赖
2. **对象创建**: 使用工厂缓存常用配置对象
3. **签名验证**: 保持原有的 HMAC 计算方式
4. **I/O 操作**: 异步执行部署命令（保持 `subprocess.Popen`）

---

## Risk Mitigation

### 1. 一次性重写的风险

**风险**: 可能遗漏边界情况

**缓解措施**:
- 完整的测试套件验证（100% 通过）
- 保留原代码作为参考
- 详细的代码审查

### 2. 依赖注入的复杂度

**风险**: 可能使代码过于复杂

**缓解措施**:
- 保持简单的构造函数注入
- 避免过度抽象
- 每个类不超过 3 个依赖

### 3. 向后兼容性破坏

**风险**: 现有部署可能失效

**缓解措施**:
- 更新安装脚本
- 提供迁移文档
- 保持配置格式不变

---

## Next Steps

Phase 0 完成后，进入 Phase 1: Design & Contracts

1. **data-model.md**: 定义所有数据模型和关系
2. **contracts/**: 详细的模块接口定义
3. **quickstart.md**: 开发者快速入门指南
4. **Agent Context Update**: 更新 AI 助手上下文

---

## References

- Python 3.6 Documentation: https://docs.python.org/3.6/
- PEP 20 -- The Zen of Python: https://peps.python.org/pep-0020/
- PEP 484 -- Type Hints: https://peps.python.org/pep-0484/
- Existing codebase: `git-webhooks-server.py` (1210 lines)
