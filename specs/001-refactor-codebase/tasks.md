# Tasks: 代码库重构 - 模块化拆分与项目结构重组

**Input**: Design documents from `/specs/001-refactor-codebase/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: 本功能规格强调测试验证策略（FR-007: 完整测试套件验证），但现有测试套件作为验证基准。本任务列表专注于代码迁移，测试任务在 Phase 4。

**Organization**: 任务按模块组织，遵循一次性重写策略。由于这是重构项目，用户故事（US1=模块结构, US2=可测试性, US3=可扩展性）紧密相关，任务按依赖顺序排列。

## Format: `[ID] [P?] [Story] Description`

- **[P]**: 可并行执行（不同文件，无依赖）
- **[Story]**: 所属用户故事（US1, US2, US3）
- 包含精确文件路径

## Path Conventions

本项目使用 Python 包结构 `gitwebhooks/` 在仓库根目录。

---

## Phase 1: Setup (项目结构创建)

**Purpose**: 创建新的模块化包结构

- [ ] T001 创建 gitwebhooks/ 包目录结构（config/, handlers/, auth/, models/, utils/, logging/）
- [ ] T002 [P] 创建 gitwebhooks/config/__init__.py 空文件
- [ ] T003 [P] 创建 gitwebhooks/handlers/__init__.py 空文件
- [ ] T004 [P] 创建 gitwebhooks/auth/__init__.py 空文件
- [ ] T005 [P] 创建 gitwebhooks/models/__init__.py 空文件
- [ ] T006 [P] 创建 gitwebhooks/utils/__init__.py 空文件
- [ ] T007 [P] 创建 gitwebhooks/logging/__init__.py 空文件
- [ ] T008 创建 tests/ 测试目录结构（test_config/, test_handlers/, test_auth/, test_integration/）
- [ ] T009 [P] 创建 tests/__init__.py 空文件

---

## Phase 2: Foundational (核心基础设施)

**Purpose**: 所有模块依赖的基础类型、常量和异常

**⚠️ CRITICAL**: 必须完成此阶段才能开始模块实现

### 模型层基础

- [ ] T010 [US1] 定义 Provider 枚举在 gitwebhooks/models/provider.py（GITHUB, GITEE, GITLAB, CUSTOM）
- [ ] T011 [US1] 定义 SignatureVerificationResult 数据类在 gitwebhooks/models/result.py（is_valid, error_message, success(), failure()）
- [ ] T012 [US1] 定义 WebhookRequest 数据类在 gitwebhooks/models/request.py（provider, event, payload, headers, post_data, repo_identifier 属性）
- [ ] T013 [P] [US1] 更新 gitwebhooks/models/__init__.py 导出 Provider, WebhookRequest, SignatureVerificationResult

### 工具层基础

- [ ] T014 [US1] 定义 HTTP 常量在 gitwebhooks/utils/constants.py（HTTP状态码、Content-Type、Headers、Messages）
- [ ] T015 [US1] 定义异常类层次在 gitwebhooks/utils/exceptions.py（WebhookError 基类，SignatureValidationError, UnsupportedEventError, UnsupportedProviderError, ConfigurationError, RequestParseError）
- [ ] T016 [P] [US1] 更新 gitwebhooks/utils/__init__.py 导出 constants, exceptions

### 配置模型

- [ ] T017 [US1] 定义 ProviderConfig 数据类在 gitwebhooks/config/models.py（provider, verify, secret, handle_events, from_config_parser(), allows_event()）
- [ ] T018 [US1] 定义 RepositoryConfig 数据类在 gitwebhooks/config/models.py（name, cwd, cmd, from_config_parser(), validate()）
- [ ] T019 [US1] 定义 ServerConfig 数据类在 gitwebhooks/config/server.py（address, port, log_file, ssl_enabled, ssl_key_file, ssl_cert_file, from_loader(), validate()）
- [ ] T019a [US1] 实现 ServerConfig.from_loader() 方法，从 ConfigLoader 创建实例
- [ ] T020 [P] [US1] 更新 gitwebhooks/config/__init__.py 导出所有配置类

### 主包初始化

- [ ] T021 [US1] 更新 gitwebhooks/__init__.py 导出主要类（WebhookServer, Provider, WebhookRequest）

**Checkpoint**: 基础设施就绪 - 模块实现可以开始

---

## Phase 3: User Story 1 - 模块化实现 (Priority: P1) 🎯 MVP

**Goal**: 将单文件代码拆分为模块化包结构，每个模块 <400 行，清晰职责分离

**Independent Test**: 代码通过目录结构可导航，每个文件独立可读

### 配置加载模块

- [ ] T022 [US1] 实现 ConfigLoader 类在 gitwebhooks/config/loader.py（__init__, _load_file(), load_provider_config(), load_all_provider_configs(), load_repository_config(), load_all_repository_configs(), get_server_config(), get_ssl_config()）。职责：从 INI 文件加载和解析配置
- [ ] T023 [US1] 实现 ConfigurationRegistry 类在 gitwebhooks/config/registry.py（__init__, _load_all_configs(), server_config, provider_configs, repository_configs 属性, get_provider_config(), get_repository_config(), has_repository()）。职责：持有所有配置并提供统一访问接口
- [ ] T024 [P] [US1] 更新 gitwebhooks/config/__init__.py 导出 ConfigLoader, ConfigurationRegistry

### 认证模块

- [ ] T025 [US1] 定义 SignatureVerifier 抽象基类在 gitwebhooks/auth/verifier.py（verify() 抽象方法）
- [ ] T026 [US1] 实现 GithubSignatureVerifier 在 gitwebhooks/auth/github.py（verify() 使用 HMAC-SHA1, hmac.compare_digest()）
- [ ] T027 [US1] 实现 GiteeSignatureVerifier 在 gitwebhooks/auth/gitee.py（verify() 支持 HMAC-SHA256 和密码模式）
- [ ] T028 [US1] 实现 GitlabTokenVerifier 在 gitwebhooks/auth/gitlab.py（verify() 简单 token 比较）
- [ ] T029 [US1] 实现 CustomTokenVerifier 在 gitwebhooks/auth/custom.py（verify() 可选 token 验证）
- [ ] T030 [US1] 实现 VerifierFactory 工厂类在 gitwebhooks/auth/factory.py（get_verifier(), create_github_verifier() 等）
- [ ] T031 [P] [US1] 更新 gitwebhooks/auth/__init__.py 导出所有认证类

### 处理器模块

- [ ] T032 [US1] 定义 WebhookHandler 抽象基类在 gitwebhooks/handlers/base.py（get_provider(), verify_signature(), extract_repository(), is_event_allowed(), handle_request() 模板方法）
- [ ] T033 [US1] 实现 GithubHandler 在 gitwebhooks/handlers/github.py（继承 WebhookHandler，实现所有抽象方法）
- [ ] T034 [US1] 实现 GiteeHandler 在 gitwebhooks/handlers/gitee.py（继承 WebhookHandler，实现所有抽象方法）
- [ ] T035 [US1] 实现 GitlabHandler 在 gitwebhooks/handlers/gitlab.py（继承 WebhookHandler，实现所有抽象方法）
- [ ] T036 [US1] 实现 CustomHandler 在 gitwebhooks/handlers/custom.py（继承 WebhookHandler，使用 identifier_path 提取仓库）
- [ ] T037 [US1] 实现 HandlerFactory 工厂类在 gitwebhooks/handlers/factory.py（from_headers(), from_handler_type()）
- [ ] T038 [P] [US1] 更新 gitwebhooks/handlers/__init__.py 导出所有处理器类

### 日志模块

- [ ] T039 [US1] 实现日志配置函数在 gitwebhooks/logging/setup.py（setup_logging() 函数，配置格式、文件和 stdout 输出）
- [ ] T040 [P] [US1] 更新 gitwebhooks/logging/__init__.py 导出 setup_logging

### 命令执行器

- [ ] T041 [US1] 实现命令执行器在 gitwebhooks/utils/executor.py（execute_deployment() 函数，使用 subprocess.Popen 异步执行）
- [ ] T042 [P] [US1] 更新 gitwebhooks/utils/__init__.py 导出 executor

**Checkpoint**: 核心模块实现完成 - 模块结构清晰，职责分离

---

## Phase 4: User Story 2 - 测试基础设施 (Priority: P2)

**Goal**: 确保模块化后可独立测试各个组件

**Independent Test**: 可以独立导入和测试单个模块（如仅测试签名验证）

- [ ] T043 [US2] 创建测试配置在 tests/test_config/__init__.py
- [ ] T044 [US2] 创建测试处理器在 tests/test_handlers/__init__.py
- [ ] T045 [US2] 创建测试认证在 tests/test_auth/__init__.py
- [ ] T046 [US2] 创建集成测试在 tests/test_integration/__init__.py
- [ ] T047 [P] [US2] 添加测试辅助工具在 tests/test_helpers.py（mock 配置、mock 请求等）
- [ ] T048 [US2] 确保现有测试套件可以运行（运行 python3 -m unittest discover tests/）

**Checkpoint**: 测试基础设施就绪 - 模块可独立测试

---

## Phase 5: User Story 3 - 扩展性验证 (Priority: P3)

**Goal**: 验证模块化架构支持新平台扩展（通过现有代码结构验证）

**Independent Test**: 代码结构允许添加新平台而无需修改核心服务器

- [ ] T049 [US3] 验证 HandlerFactory.from_headers() 支持新平台（检查代码结构是否支持扩展）
- [ ] T050 [US3] 验证 VerifierFactory.get_verifier() 支持新平台（检查代码结构是否支持扩展）
- [ ] T051 [US3] 验证配置系统支持新平台（检查 Provider 枚举和配置加载是否可扩展）

**Checkpoint**: 扩展性验证完成 - 架构支持新平台

---

## Phase 6: Integration (服务器和 CLI)

**Purpose**: 将模块集成为完整的服务器应用

### HTTP 请求处理器

- [ ] T052 实现 WebhookRequestHandler 类在 gitwebhooks/handlers/request.py（继承 BaseHTTPRequestHandler, do_GET(), do_POST(), _parse_request(), _identify_provider(), _execute_deployment(), _send_response(), _send_error(), log_message()）
- [ ] T053 [P] 更新 gitwebhooks/handlers/__init__.py 导出 WebhookRequestHandler

### HTTP 服务器

- [ ] T054 实现 WebhookServer 类在 gitwebhooks/server.py（__init__, _setup_logging(), create_http_server(), _wrap_socket_ssl(), run()）
- [ ] T055 [P] 创建 gitwebhooks/server.py 主入口（直接运行支持）

### CLI 模块

- [ ] T056 实现 CLI 主函数在 gitwebhooks/cli.py（main(), print_help()）
- [ ] T057 [P] 添加 gitwebhooks/__main__.py 支持（python3 -m gitwebhooks.cli）

**Checkpoint**: 服务器和 CLI 完成 - 可运行应用

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: 最终集成、验证和清理

### 测试验证

- [ ] T058 运行完整测试套件验证（python3 -m unittest discover tests/）确保 100% 通过（FR-007）
- [ ] T059 [P] 验证所有模块文件 <400 行（使用 `wc -l` 或 `cloc --exclude-blank` 检查代码行数）
- [ ] T060 [P] 验证代码导航性（可在 30 秒内定位任何功能）
- [ ] T060a [P] 验证目录结构符合 plan.md 定义（检查所有模块和子目录存在）
- [ ] T060b [P] 验证错误处理覆盖（测试各种错误场景：签名失败、配置缺失、无效请求等）

### CLI 入口点

- [ ] T061 创建 gitwebhooks-cli 包装脚本在仓库根目录（shell 脚本调用 python3 -m gitwebhooks.cli）
- [ ] T062 设置 gitwebhooks-cli 可执行权限（chmod +x）

### 安装脚本更新

- [ ] T063 更新 install.sh 安装 gitwebhooks-cli 而非 git-webhooks-server.py
- [ ] T064 更新 git-webhooks-server.service.sample 使用 gitwebhooks-cli 入口点

### 文档更新

- [ ] T065 [P] 更新 CLAUDE.md 反映新的项目结构（gitwebhooks/ 包组织）
- [ ] T066 [P] 更新 README.md（如果需要）反映新的 CLI 入口点

### 清理

- [ ] T067 备份原 git-webhooks-server.py 到 git-webhooks-server.py.backup
- [ ] T068 验证完整测试套件在新架构上通过（最终验证）

### 边界情况验证

- [ ] T069 [P] 验证无循环依赖：使用 `python3 -c "import gitwebhooks; print('OK')"` 测试导入
- [ ] T070 [P] 验证依赖注入正确性：确保所有模块通过构造函数接收依赖
- [ ] T071 [P] 验证性能不低于原实现：使用相同测试负载比较响应时间

**Checkpoint**: 重构完成 - 所有功能迁移并验证

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: 无依赖 - 可立即开始
- **Foundational (Phase 2)**: 依赖 Setup 完成 - 阻塞所有模块实现
- **User Story 1 (Phase 3)**: 依赖 Foundational 完成 - 核心模块实现
- **User Story 2 (Phase 4)**: 依赖 US1 模块完成 - 测试基础设施
- **User Story 3 (Phase 5)**: 依赖 US1 模块完成 - 扩展性验证
- **Integration (Phase 6)**: 依赖 US1 完成 - 服务器和 CLI
- **Polish (Phase 7)**: 依赖所有阶段完成 - 最终验证和清理

### Task Dependencies

### Phase 2 内部依赖

- T010-T013 (模型层) 可并行
- T014-T015 (工具层) 可并行，依赖模型
- T017-T020 (配置模型) 依赖模型层
- T021 (主包) 依赖所有之前任务

### Phase 3 内部依赖

- T022-T024 (配置加载) 可并行，依赖 Phase 2
- T025-T031 (认证模块) 可并行，依赖 Phase 2
- T032-T038 (处理器模块) 依赖认证模块 T025
- T039-T042 (日志和执行器) 可并行

### Phase 6 依赖

- T052 (请求处理器) 依赖 Phase 3 所有处理器
- T054 (服务器) 依赖 T039 (日志) 和 T052
- T056-T057 (CLI) 可并行，依赖 T054

### Parallel Opportunities

- Phase 1 所有任务（T002-T009）可并行
- Phase 2 模型层（T010-T013）可并行
- Phase 2 工具层（T014-T015）可并行
- Phase 3 配置、认证、日志模块可并行
- Phase 4 测试结构创建可并行
- Phase 7 文档更新可并行

---

## Parallel Example: Phase 2 Models

```bash
# 可同时创建三个核心模型文件:
T010: "定义 Provider 枚举在 gitwebhooks/models/provider.py"
T011: "定义 SignatureVerificationResult 数据类在 gitwebhooks/models/result.py"
T012: "定义 WebhookRequest 数据类在 gitwebhooks/models/request.py"
T013: "更新 gitwebhooks/models/__init__.py 导出所有模型类"
```

---

## Parallel Example: Phase 3 Auth Module

```bash
# 认证模块实现（依赖 Phase 2 完成）:
T025: "定义 SignatureVerifier 抽象基类在 gitwebhooks/auth/verifier.py"
T026: "实现 GithubSignatureVerifier 在 gitwebhooks/auth/github.py"
T027: "实现 GiteeSignatureVerifier 在 gitwebhooks/auth/gitee.py"
T028: "实现 GitlabTokenVerifier 在 gitwebhooks/auth/gitlab.py"
T029: "实现 CustomTokenVerifier 在 gitwebhooks/auth/custom.py"
T030: "实现 VerifierFactory 工厂类在 gitwebhooks/auth/factory.py"
```

---

## Implementation Strategy

### 一次性重写策略

根据澄清决策，采用一次性重写：

1. **Phase 1-2**: 创建新结构（不影响现有代码）
2. **Phase 3-6**: 实现所有新模块
3. **Phase 7**: 验证测试通过后，删除原文件

### 测试验证检查点

- **Checkpoint 1** (Phase 2 后): 基础类型定义完成
- **Checkpoint 2** (Phase 3 后): 所有模块实现完成
- **Checkpoint 3** (Phase 6 后): 服务器和 CLI 可运行
- **Checkpoint 4** (Phase 7): 100% 测试通过，可删除原文件

### 风险缓解

- 保持原文件作为参考（git-webhooks-server.py.backup）
- 每个阶段完成后可运行测试验证
- 依赖注入模式使模块可独立测试

---

## Notes

- [P] 任务 = 不同文件，无依赖，可并行
- [Story] 标签将任务映射到用户故事（US1=模块结构, US2=可测试性, US3=可扩展性）
- 遵循契约文档（contracts/）的接口定义
- 遵循数据模型（data-model.md）的实体定义
- 保持 Python 3.6+ 兼容性，无外部依赖
- 每个模块目标 <400 行代码
