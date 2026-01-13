# Tasks: 优化 git-webhooks-server.py 代码质量和规范性

**Input**: Design documents from `/specs/001-optimize-webhooks-server/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/webhooks-api.md

**Tests**: 本功能不包含新的测试任务。优化后必须确保现有测试 100% 通过。

**Organization**: 任务按用户故事分组，使每个故事可以独立实现和测试。

## Format: `[ID] [P?] [Story] Description`

- **[P]**: 可并行运行（不同文件，无依赖）
- **[Story]**: 任务所属用户故事（US1, US2, US3）
- 描述中包含精确文件路径

## Path Conventions

本项目为单文件 Python 应用，所有代码在 `git-webhooks-server.py` 中。

---

## Phase 1: Setup (共享基础设施)

**Purpose**: 准备代码质量检查工具和基线测试

- [ ] T001 运行 pylint 获取当前基线评分，记录到 specs/001-optimize-webhooks-server/baseline.md
- [ ] T002 [P] 运行现有测试套件并记录基线通过率
- [ ] T003 [P] 统计当前代码行数和圈复杂度基线
- [ ] T004 [P] 备份原始文件到 git-webhooks-server.py.backup

**Checkpoint**: 基线已建立，可以开始重构

---

## Phase 2: Foundational (基础重构 - 阻塞所有用户故事)

**Purpose**: 核心架构重构，必须在任何用户故事改进之前完成

**⚠️ CRITICAL**: 此阶段完成后才能进行用户故事的具体改进

- [ ] T005 添加必要的导入语句（typing 模块: Optional, Dict, Tuple, Any 等）到 git-webhooks-server.py
- [ ] T006 创建自定义异常类层次结构（WebhookError, SignatureValidationError, UnsupportedEventError, ConfigurationError）到 git-webhooks-server.py
- [ ] T007 定义常量（HTTP 状态码、Content-Type 值等）到 git-webhooks-server.py
- [ ] T008 创建 Provider 枚举类（GITHUB, GITEE, GITLAB, CUSTOM）到 git-webhooks-server.py
- [ ] T009 创建数据类（WebhookRequest, ProviderConfig, RepositoryConfig, SignatureVerificationResult）到 git-webhooks-server.py
- [ ] T010 创建 WebhookServer 主应用类框架到 git-webhooks-server.py
- [ ] T011 创建 ConfiguredRequestHandler 类框架到 git-webhooks-server.py

**Checkpoint**: 基础架构已就绪 - 用户故事实现现在可以开始

---

## Phase 3: User Story 1 - 提升 Python 代码规范性和可维护性 (Priority: P1) 🎯 MVP

**Goal**: 消除全局变量、添加类型提示、改进代码结构，使 pylint 评分从 6.5 提升到 8.0+

**Independent Test**: 运行 pylint 得分 ≥8.0，mypy 无关键错误，现有测试 100% 通过

### Implementation for User Story 1

- [ ] T012 [P] 为 Provider 枚举和所有数据类添加完整的类型提示到 git-webhooks-server.py
- [ ] T013 [P] 为 WebhookServer.__init__ 和配置加载方法添加类型提示和文档字符串到 git-webhooks-server.py
- [ ] T014 [P] 为 ConfiguredRequestHandler 添加依赖注入（通过 __init__ 接收配置）到 git-webhooks-server.py
- [ ] T015 重构 _parse_provider 方法：提取为独立函数，添加类型提示和文档字符串到 git-webhooks-server.py
- [ ] T016 [P] 重构 _parse_data 方法：提取为独立函数，具体化异常处理到 git-webhooks-server.py
- [ ] T017 提取 Github 签名验证逻辑为 _verify_github_signature 方法，添加类型提示到 git-webhooks-server.py
- [ ] T018 [P] 提取 Gitee 签名验证逻辑为 _verify_gitee_signature 方法，添加类型提示到 git-webhooks-server.py
- [ ] T019 [P] 提取 Gitlab token 验证逻辑为 _verify_gitlab_token 方法，添加类型提示到 git-webhooks-server.py
- [ ] T020 [P] 提取 Custom token 验证逻辑为 _verify_custom_token 方法，添加类型提示到 git-webhooks-server.py
- [ ] T021 重构 do_POST 方法：提取平台处理器为独立方法（_handle_github, _handle_gitee, _handle_gitlab, _handle_custom）到 git-webhooks-server.py
- [ ] T022 创建 _dispatch_to_provider 方法分发到平台处理器，添加类型提示到 git-webhooks-server.py
- [ ] T023 提取仓库标识提取逻辑为 _extract_repository_name 方法到 git-webhooks-server.py
- [ ] T024 提取部署命令执行逻辑为 _execute_deployment_command 方法到 git-webhooks-server.py
- [ ] T025 创建 _send_error 和 _send_success 辅助方法统一 HTTP 响应到 git-webhooks-server.py
- [ ] T026 [P] 为所有公共方法添加 Google 风格文档字符串到 git-webhooks-server.py
- [ ] T027 [P] 为 main 函数添加类型提示和重构（使用 WebhookServer 类）到 git-webhooks-server.py
- [ ] T028 消除所有魔法数字和字符串，使用具名常量替换到 git-webhooks-server.py

**Checkpoint**: User Story 1 完成 - 代码规范性和可维护性显著提升

---

## Phase 4: User Story 2 - 增强错误处理和日志记录 (Priority: P2)

**Goal**: 具体化异常处理，增强日志上下文，提升故障诊断效率

**Independent Test**: 触发各种错误场景，验证日志包含充分上下文信息

### Implementation for User Story 2

- [ ] T029 [P] 替换所有裸 `except:` 为具体异常类型（ValueError, KeyError, json.JSONDecodeError 等）到 git-webhooks-server.py
- [ ] T030 [P] 为配置加载添加具体异常处理（UnicodeDecodeError, configparser.Error）到 git-webhooks-server.py
- [ ] T031 [P] 为签名验证添加详细错误日志（包含失败原因）到 git-webhooks-server.py
- [ ] T032 为命令执行失败添加详细日志（包含命令、cwd、退出码、stdout、stderr）到 git-webhooks-server.py
- [ ] T033 [P] 为请求解析失败添加日志（包含 Content-Type、payload 大小）到 git-webhooks-server.py
- [ ] T034 [P] 为平台识别失败添加警告日志到 git-webhooks-server.py
- [ ] T035 为事件不允许处理添加警告日志（包含平台、事件、允许列表）到 git-webhooks-server.py
- [ ] T036 [P] 为仓库配置缺失添加警告日志到 git-webhooks-server.py
- [ ] T037 为所有日志使用合适的级别（DEBUG, INFO, WARNING, ERROR, CRITICAL）到 git-webhooks-server.py

**Checkpoint**: User Story 2 完成 - 错误处理和日志记录显著改进

---

## Phase 5: User Story 3 - 改进代码结构和可测试性 (Priority: P3)

**Goal**: 提升代码可测试性，使单元测试更容易编写

**Independent Test**: 验证所有关键组件可以通过依赖注入进行独立测试

### Implementation for User Story 3

- [ ] T038 [P] 确保 WebhookServer 可以通过依赖注入接收模拟 ConfigParser
- [ ] T039 [P] 确保 ConfiguredRequestHandler 可以通过构造函数接收所有依赖
- [ ] T040 [P] 提取签名验证为可独立测试的纯函数到 git-webhooks-server.py
- [ ] T041 [P] 提取仓库标识提取逻辑为可独立测试的函数到 git-webhooks-server.py
- [ ] T042 [P] 确保所有私有方法不依赖全局状态
- [ ] T043 验证函数长度不超过 50 行（拆分过长函数）到 git-webhooks-server.py
- [ ] T044 验证圈复杂度不超过 15（简化复杂逻辑）到 git-webhooks-server.py

**Checkpoint**: User Story 3 完成 - 代码结构和可测试性显著提升

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: 跨所有用户故事的最终改进和验证

- [ ] T045 [P] 运行 pylint 验证评分 ≥8.0/10
- [ ] T046 [P] 运行 mypy 验证无 ERROR 级别的类型错误（WARNING 级别可接受）
- [ ] T047 [P] 运行现有完整测试套件验证 100% 通过
- [ ] T048 [P] 统计代码行数增幅 ≤20%
- [ ] T049 [P] 统计圈复杂度平均值 ≤10，最大值 ≤15
- [ ] T050 [P] 统计代码重复率 <5%
- [ ] T051 [P] 运行 coverage.py 验证测试覆盖率 ≥75%（关键路径 100%）
- [ ] T052 [P] 执行 quickstart.md 中的所有示例验证功能正确性
- [ ] T053 [P] 验证 HTTP 响应状态码符合 RFC 7231 规范（403 拒绝 GET、401 签名验证失败等）
- [ ] T054 代码最终审查：确保无遗留裸 except、无全局变量、所有公共 API（非 __ 前缀方法）有文档字符串
- [ ] T055 [P] 更新 README.md 和 README.zh.md（如有需要）
- [ ] T056 运行代码质量最终验证并生成报告到 specs/001-optimize-webhooks-server/final-report.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: 无依赖 - 可立即开始
- **Foundational (Phase 2)**: 依赖 Setup 完成 - 阻塞所有用户故事
- **User Story 1 (Phase 3)**: 依赖 Foundational 完成 - 无其他故事依赖
- **User Story 2 (Phase 4)**: 依赖 Foundational 和 US1 完成 - 基于 US1 的代码结构
- **User Story 3 (Phase 5)**: 依赖 Foundational 和 US1 完成 - 进一步改进结构
- **Polish (Phase 6)**: 依赖所有用户故事完成

### User Story Dependencies

- **User Story 1 (P1)**: Foundational 完成后可开始 - 核心重构，其他故事基于此
- **User Story 2 (P2)**: 依赖 US1 - 在 US1 重构的代码结构上添加增强
- **User Story 3 (P3)**: 依赖 US1 - 进一步改进 US1 的代码结构

### Within Each User Story

- US1: 类型提示和文档（并行）→ 平台处理器提取（并行）→ 方法提取（顺序）
- US2: 异常处理（并行）→ 日志增强（并行）
- US3: 可测试性改进（并行）→ 复杂度验证（顺序）

### Parallel Opportunities

- Phase 1: T002, T003, T004 可并行
- Phase 2: T005, T006, T007, T008 可并行
- US1: T012-T020 可并行（不同方法），T021-T025 顺序
- US2: 所有任务可并行（不同错误处理路径）
- US3: T038-T042 可并行
- Polish: T045-T051 可并行

---

## Parallel Example: User Story 1

```bash
# 并行启动类型提示和文档任务：
Task: "为 Provider 枚举和所有数据类添加完整的类型提示到 git-webhooks-server.py"
Task: "为 WebhookServer.__init__ 和配置加载方法添加类型提示和文档字符串到 git-webhooks-server.py"
Task: "为 ConfiguredRequestHandler 添加依赖注入到 git-webhooks-server.py"

# 并行启动平台处理器提取：
Task: "提取 Github 签名验证逻辑为 _verify_github_signature 方法，添加类型提示到 git-webhooks-server.py"
Task: "提取 Gitee 签名验证逻辑为 _verify_gitee_signature 方法，添加类型提示到 git-webhooks-server.py"
Task: "提取 Gitlab token 验证逻辑为 _verify_gitlab_token 方法，添加类型提示到 git-webhooks-server.py"
Task: "提取 Custom token 验证逻辑为 _verify_custom_token 方法，添加类型提示到 git-webhooks-server.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. 完成 Phase 1: Setup（建立基线）
2. 完成 Phase 2: Foundational（核心架构）
3. 完成 Phase 3: User Story 1（代码规范性和可维护性）
4. **验证**: 运行 pylint, mypy, 测试套件
5. **检查点**: pylint ≥8.0, 测试 100% 通过

### Incremental Delivery

1. Setup + Foundational → 基础架构就绪
2. + User Story 1 → 代码质量达标 → MVP 完成
3. + User Story 2 → 错误处理和日志增强
4. + User Story 3 → 可测试性改进
5. + Polish → 最终验证和报告

---

## Notes

- **单文件约束**: 所有代码在 `git-webhooks-server.py` 中
- **无新依赖**: 仅使用 Python 3 标准库
- **向后兼容**: HTTP API 和配置文件格式完全不变
- **测试要求**: 现有测试必须 100% 通过
- **质量目标**:
  - pylint: ≥8.0/10
  - mypy: 0 关键错误
  - 圈复杂度: ≤15 (max)
  - 代码重复: <5%
  - 行数增幅: ≤20%
