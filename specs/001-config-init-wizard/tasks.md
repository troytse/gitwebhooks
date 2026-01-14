# Tasks: config init 交互式向导

**Input**: Design documents from `/specs/001-config-init-wizard/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/wizard.md

**Tests**: 本任务列表包含测试任务，根据规格说明的测试策略要求。

**Organization**: 任务按用户故事分组，以实现独立实现和测试。

## Format: `[ID] [P?] [Story] Description`

- **[P]**: 可并行执行（不同文件，无依赖）
- **[Story]**: 任务所属用户故事（US1, US2, US3）
- 包含精确文件路径

## Path Conventions

本项目使用单一项目结构，代码位于 `gitwebhooks/`，测试位于 `tests/`。

---

## Phase 1: Setup (共享基础设施)

**Purpose**: 项目初始化和基础结构

- [X] T001 创建测试目录结构 `tests/unit/cli/` 和 `tests/integration/`
- [X] T002 创建单元测试文件框架 `tests/unit/cli/test_init_wizard.py`
- [X] T003 创建集成测试文件框架 `tests/integration/test_config_init.sh`

---

## Phase 2: Foundational (阻塞性前置条件)

**Purpose**: 所有用户故事依赖的核心基础设施

**⚠️ CRITICAL**: 此阶段完成前，不能开始任何用户故事的实现

- [X] T004 创建向导模块文件 `gitwebhooks/cli/init_wizard.py`，定义模块级常量 CONFIG_LEVELS 和 PLATFORMS
- [X] T005 [P] 实现输入验证函数：`validate_repo_name()`, `validate_existing_path()`, `validate_non_empty()`, `validate_port()` 在 `gitwebhooks/cli/init_wizard.py`
- [X] T006 [P] 实现 `ConfigLevel` 数据类和相关辅助函数在 `gitwebhooks/cli/init_wizard.py`
- [X] T007 [P] 实现 `ServerConfig` 数据类在 `gitwebhooks/cli/init_wizard.py`
- [X] T008 [P] 实现 `PlatformConfig` 数据类在 `gitwebhooks/cli/init_wizard.py`
- [X] T009 [P] 实现 `RepositoryConfig` 数据类在 `gitwebhooks/cli/init_wizard.py`

**Checkpoint**: 基础设施就绪 - 用户故事实现现在可以并行开始

---

## Phase 3: User Story 1 - 快速初始化默认配置 (Priority: P1) 🎯 MVP

**Goal**: 通过交互式向导快速创建完整的配置文件，支持配置级别选择、服务器配置、平台配置和仓库配置。

**Independent Test**: 运行 `gitwebhooks-cli config init`，回答一系列问题后生成包含 [server]、[github]、[repo/owner/name] 的完整 INI 文件

### Tests for User Story 1

> **NOTE: 先编写这些测试，确保在实现前失败**

- [X] T010 [P] [US1] 单元测试：配置级别映射和验证在 `tests/unit/cli/test_init_wizard.py`
- [X] T011 [P] [US1] 单元测试：输入验证函数在 `tests/unit/cli/test_init_wizard.py`
- [X] T012 [P] [US1] 单元测试：INI 生成逻辑在 `tests/unit/cli/test_init_wizard.py`
- [X] T013 [P] [US1] 集成测试：完整向导流程（使用模拟输入）在 `tests/integration/test_config_init.sh`

### Implementation for User Story 1

- [X] T014 [US1] 实现 `Wizard` 类 `__init__()` 和 `run()` 方法框架在 `gitwebhooks/cli/init_wizard.py`
- [X] T015 [US1] 实现 `_select_level()` 方法，交互式选择配置级别在 `gitwebhooks/cli/init_wizard.py`
- [X] T016 [US1] 实现配置级别权限检测，`os.access()` 检查并提示错误在 `gitwebhooks/cli/init_wizard.py`
- [X] T017 [US1] 实现 `_collect_server_config()` 方法，收集服务器配置参数在 `gitwebhooks/cli/init_wizard.py`
- [X] T018 [US1] 实现 `_select_platform()` 方法，选择 Git 平台类型在 `gitwebhooks/cli/init_wizard.py`
- [X] T019 [US1] 实现 `_collect_platform_config()` 方法，收集平台配置参数（events、verify、secret）在 `gitwebhooks/cli/init_wizard.py`
- [X] T020 [US1] 实现事件选择逻辑：复选列表解析，空输入默认 push 在 `gitwebhooks/cli/init_wizard.py`
- [X] T021 [US1] 实现 `_collect_repository_config()` 方法，收集仓库配置参数在 `gitwebhooks/cli/init_wizard.py`
- [X] T022 [US1] 实现 `_confirm_overwrite()` 方法，文件覆盖确认逻辑在 `gitwebhooks/cli/init_wizard.py`
- [X] T023 [US1] 实现 `_generate_config()` 方法，使用 configparser 生成 INI 在 `gitwebhooks/cli/init_wizard.py`
- [X] T024 [US1] 实现 `_write_config()` 方法，写入配置文件并设置权限 0600 在 `gitwebhooks/cli/init_wizard.py`
- [X] T025 [US1] 实现 `_show_completion()` 方法，显示完成信息和后续步骤在 `gitwebhooks/cli/init_wizard.py`
- [X] T026 [US1] 实现信号处理：`KeyboardInterrupt` 捕获和部分文件清理在 `gitwebhooks/cli/init_wizard.py`
- [X] T027 [US1] 在 `gitwebhooks/cli/config.py` 中添加 `cmd_init()` 函数作为 CLI 入口点
- [X] T028 [US1] 在 `gitwebhooks/cli/__init__.py` 中注册 `init` 子命令到 argparse

**Checkpoint**: 此时 User Story 1 应该完全功能化并可独立测试

---

## Phase 4: User Story 2 - 指定配置级别创建 (Priority: P2)

**Goal**: 支持通过命令行参数直接指定配置级别，跳过交互式选择步骤。

**Independent Test**: 运行 `gitwebhooks-cli config init system`，验证配置文件直接生成到 `/etc/gitwebhooks.ini` 且不询问配置级别

### Tests for User Story 2

- [X] T029 [P] [US2] 单元测试：level 参数解析和验证在 `tests/unit/cli/test_init_wizard.py`
- [X] T030 [P] [US2] 集成测试：各配置级别参数在 `tests/integration/test_config_init.sh`

### Implementation for User Story 2

- [X] T031 [US2] 修改 `Wizard.__init__()` 接受 `level` 参数，实现参数验证在 `gitwebhooks/cli/init_wizard.py`
- [X] T032 [US2] 修改 `run()` 方法，当 level 已提供时跳过 `_select_level()` 在 `gitwebhooks/cli/init_wizard.py`
- [X] T033 [US2] 修改 `cmd_init()` 函数，添加 `level` 位置参数到 argparse 在 `gitwebhooks/cli/config.py`
- [X] T034 [US2] 实现无效 level 参数的错误处理和用户提示在 `gitwebhooks/cli/init_wizard.py`

**Checkpoint**: 此时 User Stories 1 和 2 都应该独立工作

---

## Phase 5: User Story 3 - Custom 平台配置引导 (Priority: P3)

**Goal**: 支持自定义平台的配置引导，询问额外的 header_name、header_value、identifier_path、header_event 参数。

**Independent Test**: 运行 `gitwebhooks-cli config init`，选择 custom 平台，验证询问所有额外参数并生成正确的 [custom] 配置节

### Tests for User Story 3

- [X] T035 [P] [US3] 单元测试：custom 平台额外参数收集在 `tests/unit/cli/test_init_wizard.py`
- [X] T036 [P] [US3] 集成测试：custom 平台完整流程在 `tests/integration/test_config_init.sh`

### Implementation for User Story 3

- [X] T037 [US3] 修改 `_collect_platform_config()` 方法，检测 custom 平台在 `gitwebhooks/cli/init_wizard.py`
- [X] T038 [US3] 实现 custom 平台额外参数收集：header_name、header_value、identifier_path、header_event 在 `gitwebhooks/cli/init_wizard.py`
- [X] T039 [US3] 为 custom 参数提供示例值作为默认值在 `gitwebhooks/cli/init_wizard.py`
- [X] T040 [US3] 修改 `_generate_config()` 方法，正确生成 custom 平台配置节在 `gitwebhooks/cli/init_wizard.py`

**Checkpoint**: 所有用户故事现在应该独立功能化

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: 影响多个用户故事的改进

- [X] T041 [P] 集成测试：权限不足错误处理在 `tests/integration/test_config_init.sh`
- [X] T042 [P] 集成测试：文件已存在覆盖确认在 `tests/integration/test_config_init.sh`
- [X] T043 [P] 集成测试：Ctrl+C 中断和清理在 `tests/integration/test_config_init.sh`
- [X] T044 [P] 集成测试：各平台（github/gitee/gitlab）配置生成在 `tests/integration/test_config_init.sh`
- [X] T045 [P] 集成测试：无效输入验证和错误提示在 `tests/integration/test_config_init.sh`
- [X] T046 添加向导完成后的提示信息，说明如何手动编辑添加更多平台/仓库在 `gitwebhooks/cli/init_wizard.py`
- [X] T047 运行 quickstart.md 验证，确保文档示例实际可用
- [X] T048 代码清理：移除未使用的导入，统一命名风格
- [X] T049 性能检查：确认向导响应时间 < 100ms，配置生成 < 1s
- [X] T050 更新 CLAUDE.md，添加 `config init` 子命令文档

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: 无依赖 - 可立即开始
- **Foundational (Phase 2)**: 依赖 Setup 完成 - 阻塞所有用户故事
- **User Stories (Phase 3-5)**: 都依赖 Foundational 阶段完成
  - 用户故事可以并行进行（如果有人力）
  - 或按优先级顺序执行（P1 → P2 → P3）
- **Polish (Phase 6)**: 依赖所有期望的用户故事完成

### User Story Dependencies

- **User Story 1 (P1)**: Foundational 完成后可开始 - 无其他故事依赖
- **User Story 2 (P2)**: Foundational 完成后可开始 - 扩展 US1，但应独立测试
- **User Story 3 (P3)**: Foundational 完成后可开始 - 扩展 US1，但应独立测试

### Within Each User Story

- 测试必须先编写并确保 FAIL 再实现
- 数据类（T006-T009）在向导类方法之前
- 核心实现在集成之前
- 故事完成前进行独立测试

### Parallel Opportunities

- Setup 的所有任务可并行
- Foundational 中标记 [P] 的任务可并行
- Foundational 完成后，所有用户故事可并行开始
- 每个故事中标记 [P] 的测试可并行
- 不同用户故事可由不同团队成员并行处理

---

## Parallel Example: User Story 1

```bash
# 并行启动 User Story 1 的所有测试：
Task: "单元测试：配置级别映射和验证"
Task: "单元测试：输入验证函数"
Task: "单元测试：INI 生成逻辑"
Task: "集成测试：完整向导流程"

# Foundational 阶段的并行示例：
Task: "实现输入验证函数"
Task: "实现 ConfigLevel 数据类"
Task: "实现 ServerConfig 数据类"
Task: "实现 PlatformConfig 数据类"
Task: "实现 RepositoryConfig 数据类"
```

---

## Implementation Strategy

### MVP First (仅 User Story 1)

1. 完成 Phase 1: Setup
2. 完成 Phase 2: Foundational (关键 - 阻塞所有故事)
3. 完成 Phase 3: User Story 1
4. **停止并验证**: 独立测试 User Story 1
5. 如准备就绪则部署/演示

### Incremental Delivery

1. 完成 Setup + Foundational → 基础就绪
2. 添加 User Story 1 → 独立测试 → 部署/演示 (MVP!)
3. 添加 User Story 2 → 独立测试 → 部署/演示
4. 添加 User Story 3 → 独立测试 → 部署/演示
5. 每个故事都增加价值而不破坏之前的故事

### Parallel Team Strategy

有多位开发人员时：

1. 团队一起完成 Setup + Foundational
2. Foundational 完成后：
   - 开发者 A: User Story 1
   - 开发者 B: User Story 2
   - 开发者 C: User Story 3
3. 故事独立完成和集成

---

## Notes

- [P] 任务 = 不同文件，无依赖
- [Story] 标签将任务映射到特定用户故事以跟踪
- 每个用户故事应独立完成和测试
- 实现前验证测试失败
- 每个任务或逻辑组后提交
- 在任何检查点停止以独立验证故事
- 避免：模糊任务、同文件冲突、破坏独立性的跨故事依赖

---

## Task Summary

| 阶段 | 任务数 | 说明 |
|------|--------|------|
| Phase 1: Setup | 3 | 项目初始化 |
| Phase 2: Foundational | 6 | 核心基础设施 |
| Phase 3: User Story 1 | 19 | MVP 核心功能 |
| Phase 4: User Story 2 | 6 | 配置级别参数 |
| Phase 5: User Story 3 | 6 | Custom 平台支持 |
| Phase 6: Polish | 10 | 跨故事改进 |
| **总计** | **50** | - |

### Task Count by User Story

| User Story | Tasks | Priority |
|------------|-------|----------|
| US1 - 快速初始化默认配置 | 19 (T010-T028) | P1 🎯 MVP |
| US2 - 指定配置级别创建 | 6 (T029-T034) | P2 |
| US3 - Custom 平台配置 | 6 (T035-T040) | P3 |

### Parallel Opportunities

- **Phase 2**: 5 个任务可并行 (T005-T009)
- **Phase 3**: 4 个测试可并行 (T010-T013)
- **Phase 4**: 2 个测试可并行 (T029-T030)
- **Phase 5**: 2 个测试可并行 (T035-T036)
- **Phase 6**: 5 个测试可并行 (T041-T045)

### Suggested MVP Scope

**MVP = Phase 1 + Phase 2 + Phase 3 (User Story 1)**

共 28 个任务（T001-T028），完成后可实现：
- 交互式配置向导
- 支持所有配置级别
- 支持 github/gitee/gitlab 平台
- 完整的输入验证和错误处理
- 配置文件生成和覆盖确认
