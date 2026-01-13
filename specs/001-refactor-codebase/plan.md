# Implementation Plan: 代码库重构 - 模块化拆分与项目结构重组

**Branch**: `001-refactor-codebase` | **Date**: 2025-01-13 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-refactor-codebase/spec.md`

## Summary

重构现有的单文件 Git Webhooks Server（1200+ 行）为模块化包结构。采用一次性重写策略，创建 `gitwebhooks/` Python 包，使用依赖注入模式消除全局状态，提供新的 CLI 入口点，保持100%测试通过率和向后兼容性。

## Technical Context

**Language/Version**: Python 3.7+ (使用 dataclass 需要至少 3.7)
**Primary Dependencies**: Python 3 标准库仅（不引入外部依赖）
**Storage**: INI 配置文件 (configparser.ConfigParser)
**Testing**: Python 标准库 unittest（现有测试套件）
**Target Platform**: Linux 服务器（systemd 集成）
**Project Type**: 单项目 - Python 包重构
**Performance Goals**: 保持现有性能水平（重构不优化性能）
**Constraints**: Python 3.6+ 兼容性，无外部依赖，保持 INI 配置格式
**Scale/Scope**: ~1200 行代码拆分为 8-10 个模块，目标每模块 <400 行

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Required Compliance Gates

All features MUST pass the following gates from `.specify/memory/constitution.md`:

1. **Simplicity & Minimalism**: Does this maintain a simple, modular Python architecture?
   - ✅ Are external dependencies absolutely essential? 否，仅使用 Python 标准库
   - ✅ Can this be achieved with Python 3 standard library only? 是
   - ✅ Does the configuration remain INI-based and human-readable? 是
   - ✅ Does each module follow single responsibility principle? 是
   - ✅ Are modules kept under 400 lines where possible? 是

2. **Platform Neutrality**: Does this treat all Git platforms equally?
   - ✅ Are there platform-specific hardcoded paths or assumptions? 否
   - ✅ Is platform identification header-based only? 是

3. **Configuration-Driven Behavior**: Is repository-specific logic in configuration?
   - ✅ Can behavior be changed via INI configuration without code changes? 是
   - ✅ Are we adding repository-specific code to the server? 否

4. **Security by Verification**: Are security requirements met?
   - ✅ Is signature/token verification supported for affected platforms? 是
   - ✅ Are secrets stored in configuration only (never hardcoded)? 是
   - ✅ Are SSL/TLS options preserved if applicable? 是

5. **Service Integration**: Does this maintain systemd compatibility?
   - ✅ Will the install script still work? 是（需更新）
   - ✅ Are logs written to configurable file paths? 是

6. **Professional Commit Standards**: Do commits follow the required standards?
   - ✅ Are commit messages free of AI-generated attribution signatures? 是
   - ✅ Do commit messages follow the format: `类型: 简短描述` (Chinese description)? 是
   - ✅ Are valid commit types used (feat, fix, docs, refactor, test, chore)? 是

### Violation Justification

无违规。宪法 v2.0.0 已更新以支持模块化包结构。

## Project Structure

### Documentation (this feature)

```text
specs/001-refactor-codebase/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
gitwebhooks/
├── __init__.py          # 包初始化，导出主要类
├── cli.py               # CLI 入口点 (gitwebhooks-cli)
├── server.py            # HTTP 服务器主逻辑
├── config/              # 配置管理模块
│   ├── __init__.py
│   ├── parser.py        # INI 配置解析
│   ├── models.py        # 配置数据类 (ProviderConfig, RepositoryConfig)
│   └── loader.py        # 配置加载器
├── handlers/            # Webhook 处理器模块
│   ├── __init__.py
│   ├── base.py          # 处理器基类
│   ├── github.py        # Github webhook 处理
│   ├── gitee.py         # Gitee webhook 处理
│   ├── gitlab.py        # Gitlab webhook 处理
│   └── custom.py        # 自定义 webhook 处理
├── auth/                # 认证和签名验证模块
│   ├── __init__.py
│   ├── verifier.py      # 验证器基类和接口
│   ├── github.py        # Github HMAC-SHA1 签名验证
│   ├── gitee.py         # Gitee HMAC-SHA256/密码验证
│   └── gitlab.py        # Gitlab token 验证
├── models/              # 数据模型模块
│   ├── __init__.py
│   ├── provider.py      # Provider 枚举
│   ├── request.py       # WebhookRequest 数据类
│   └── result.py        # SignatureVerificationResult 数据类
├── utils/               # 工具模块
│   ├── __init__.py
│   ├── constants.py     # HTTP 常量、消息常量
│   ├── exceptions.py    # 自定义异常类
│   └── executor.py      # 命令执行器
└── logging/             # 日志配置模块
    ├── __init__.py
    └── setup.py         # 日志配置

tests/
├── __init__.py
├── test_config/         # 配置模块测试
├── test_handlers/       # 处理器测试
├── test_auth/           # 认证模块测试
└── test_integration/    # 集成测试

git-webhooks-server.py   # 旧文件（将在迁移后删除）
gitwebhooks-cli          # 新的 CLI 入口点（符号链接或脚本）
install.sh               # 安装脚本（需更新）
.gitwebhooks-server.ini.sample  # 配置示例
```

**Structure Decision**: 采用 Python 包结构（Option 1 变体），将核心逻辑组织为 `gitwebhooks/` 包，保持根目录简洁。每个子模块（handlers, auth, config, models）负责单一职责，便于测试和扩展。

## Complexity Tracking

> 宪法已更新至 v2.0.0 以支持模块化架构，无需复杂度跟踪。

无违规。此变更通过正式的宪法修订流程完成。

---

## Phase 0: Research & Technical Decisions

**Status**: ✅ Complete

Research tasks completed and documented in `research.md`.

**Decisions Made**:
1. ✅ Python 3.6 包结构：传统包结构（每个目录包含 `__init__.py`）
2. ✅ 依赖注入：构造函数注入 + 工厂模式
3. ✅ 向后兼容性：保留命令行接口，内部迁移到新架构
4. ✅ 模块接口：基于抽象基类（ABC）的接口定义

*Output: `research.md`*

## Phase 1: Design & Contracts

**Status**: ✅ Complete

所有设计文档和契约定义已完成。

**Deliverables**:
1. ✅ `data-model.md` - 实体定义、关系、验证规则
2. ✅ `contracts/handlers.md` - 处理器模块接口
3. ✅ `contracts/config.md` - 配置模块接口
4. ✅ `contracts/auth.md` - 认证模块接口
5. ✅ `contracts/server.md` - 服务器模块接口
6. ✅ `contracts/cli.md` - CLI 模块接口
7. ✅ `quickstart.md` - 开发者快速入门指南
8. ✅ Agent context updated - `CLAUDE.md` 已更新

## Phase 2: Task Generation

**Status**: ✅ Complete

任务列表已生成，包含 75 个任务，组织为 7 个阶段。

**任务摘要**:
- Phase 1: Setup (9 tasks) - 创建目录结构
- Phase 2: Foundational (13 tasks) - 核心模型、工具、配置
- Phase 3: US1 - 模块化实现 (20 tasks) - 处理器、认证、配置、日志
- Phase 4: US2 - 测试基础设施 (6 tasks) - 测试目录和辅助工具
- Phase 5: US3 - 扩展性验证 (3 tasks) - 验证架构可扩展性
- Phase 6: Integration (6 tasks) - 服务器和 CLI
- Phase 7: Polish (18 tasks) - 测试验证、文档、清理、边界验证

**可并行机会**: 30+ 任务标记为 [P] 可并行执行

*Output: `tasks.md`*
