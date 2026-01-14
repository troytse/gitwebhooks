# Tasks: 配置文件查看命令

**Input**: Design documents from `/specs/001-config-view/`
**Prerequisites**: plan.md, spec.md, data-model.md, research.md, quickstart.md

**Tests**: 本功能包含单元测试和集成测试任务。

**Organization**: 任务按用户故事分组，以支持每个故事的独立实现和测试。

## Format: `[ID] [P?] [Story] Description`

- **[P]**: 可并行运行（不同文件，无依赖）
- **[Story]**: 任务所属的用户故事（US1, US2, US3）
- 描述中包含精确的文件路径

## Path Conventions

本项目使用单一 Python 包结构：
- 源代码: `gitwebhooks/`
- 测试: `tests/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: 项目初始化和常量定义

- [X] T001 在 gitwebhooks/utils/constants.py 中添加配置文件路径常量（CONFIG_PATH_USER, CONFIG_PATH_LOCAL, CONFIG_PATH_SYSTEM, CONFIG_SEARCH_PATHS）
- [X] T002 [P] 在 gitwebhooks/utils/constants.py 中添加敏感字段关键词常量（SENSITIVE_KEYWORDS）
- [X] T003 [P] 在 gitwebhooks/utils/constants.py 中添加 ANSI 颜色代码常量（COLOR_SENSITIVE, COLOR_RESET）

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: 所有用户故事依赖的核心基础设施

**⚠️ CRITICAL**: 完成此阶段前不能开始任何用户故事的实现

- [X] T004 在 gitwebhooks/cli/config.py 中创建 cmd_view() 函数框架，接受 argparse.Namespace 参数并返回 int
- [X] T005 在 gitwebhooks/cli/__init__.py 中注册 config view 子命令（添加 'view' 子命令到 config 子命令组）
- [X] T006 在 gitwebhooks/cli/config.py 中实现 locate_config_file() 函数，支持 -c 参数和默认优先级查找，正确处理包含特殊字符或空格的路径

**Checkpoint**: 基础设施就绪 - 用户故事实现现在可以并行开始

---

## Phase 3: User Story 1 - 查看当前配置文件信息 (Priority: P1) 🎯 MVP

**Goal**: 实现配置文件路径查找和内容显示的核心功能

**Independent Test**: 执行 `gitwebhooks-cli config view` 命令，输出应显示配置文件路径和按节分组的配置内容

### Tests for User Story 1

- [X] T007 [P] [US1] 在 tests/unit/cli/test_config_view.py 中编写测试：locate_config_file() 正确查找默认配置文件
- [X] T008 [P] [US1] 在 tests/unit/cli/test_config_view.py 中编写测试：locate_config_file() 支持 -c 参数指定路径
- [X] T008a [P] [US1] 在 tests/unit/cli/test_config_view.py 中编写测试：locate_config_file() 按优先级顺序查找配置文件（~/.gitwebhooks.ini > /usr/local/etc/gitwebhooks.ini > /etc/gitwebhooks.ini）
- [X] T009 [P] [US1] 在 tests/unit/cli/test_config_view.py 中编写测试：cmd_view() 正确格式化配置头部信息
- [X] T010 [P] [US1] 在 tests/unit/cli/test_config_view.py 中编写测试：cmd_view() 按节分组显示配置内容
- [X] T011 [P] [US1] 在 tests/integration/test_config_view_integration.py 中编写测试：完整的 config view 命令端到端测试

### Implementation for User Story 1

- [X] T012 [US1] 在 gitwebhooks/cli/config.py 中实现 format_config_header() 函数，格式：`Config File: <path> (source: user-specified/auto-detected)`
- [X] T013 [US1] 在 gitwebhooks/cli/config.py 中实现 format_config_content() 函数，按节分组显示配置内容
- [X] T014 [US1] 在 gitwebhooks/cli/config.py 中实现 cmd_view() 函数主体，集成 locate_config_file()、format_config_header() 和 format_config_content()
- [X] T015 [US1] 在 gitwebhooks/cli/config.py 中添加配置文件读取和解析逻辑（使用 configparser，明确使用 UTF-8 编码）
- [X] T016 [US1] 在 gitwebhooks/cli/config.py 中添加命令行参数解析（-c 参数支持）

**Checkpoint**: 此时 User Story 1 应完全可用且可独立测试

---

## Phase 4: User Story 2 - 处理配置文件不存在的情况 (Priority: P2)

**Goal**: 实现友好的错误提示，帮助用户理解配置文件缺失问题

**Independent Test**: 删除所有默认配置文件后执行命令，应显示友好的错误信息和下一步操作提示

### Tests for User Story 2

- [X] T017 [P] [US2] 在 tests/unit/cli/test_config_view.py 中编写测试：配置文件不存在时显示所有搜索路径
- [X] T018 [P] [US2] 在 tests/unit/cli/test_config_view.py 中编写测试：-c 指定的文件不存在时显示清晰错误
- [X] T019 [P] [US2] 在 tests/integration/test_config_view_integration.py 中编写测试：无配置文件时的端到端错误处理

### Implementation for User Story 2

- [X] T020 [US2] 在 gitwebhooks/cli/config.py 中实现 format_file_not_found_error() 函数，列出所有搜索路径
- [X] T021 [US2] 在 gitwebhooks/cli/config.py 中实现 format_custom_file_not_found_error() 函数，处理 -c 参数指定的文件不存在
- [X] T022 [US2] 在 gitwebhooks/cli/config.py 中更新 cmd_view() 函数，集成配置文件缺失的错误处理
- [X] T023 [US2] 在 gitwebhooks/cli/config.py 中添加提示使用 `config init` 的帮助信息

**Checkpoint**: 此时 User Stories 1 AND 2 都应独立可用

---

## Phase 5: User Story 3 - 高亮显示敏感配置 (Priority: P3)

**Goal**: 使用 ANSI 颜色代码高亮显示敏感字段，帮助用户识别敏感信息

**Independent Test**: 查看包含敏感信息的配置文件，敏感字段应以黄色高亮显示

### Tests for User Story 3

- [X] T024 [P] [US3] 在 tests/unit/cli/test_config_view.py 中编写测试：is_sensitive_key() 正确识别敏感关键词
- [X] T025 [P] [US3] 在 tests/unit/cli/test_config_view.py 中编写测试：format_sensitive_field() 正确应用 ANSI 颜色代码
- [X] T026 [P] [US3] 在 tests/unit/cli/test_config_view.py 中编写测试：检测 NO_COLOR 环境变量并禁用颜色
- [X] T027 [P] [US3] 在 tests/unit/cli/test_config_view.py 中编写测试：检测 TERM=dumb 环境变量并禁用颜色
- [X] T028 [P] [US3] 在 tests/integration/test_config_view_integration.py 中编写测试：敏感字段高亮显示的端到端测试

### Implementation for User Story 3

- [X] T029 [US3] 在 gitwebhooks/cli/config.py 中实现 is_sensitive_key() 函数，检测敏感关键词（secret, password, token, key, passphrase）
- [X] T030 [US3] 在 gitwebhooks/cli/config.py 中实现 should_use_color() 函数，检测 NO_COLOR 和 TERM 环境变量
- [X] T031 [US3] 在 gitwebhooks/cli/config.py 中实现 format_sensitive_field() 函数，应用 ANSI 颜色代码（黄色），完整显示字段值（不隐藏）仅用颜色标记
- [X] T032 [US3] 在 gitwebhooks/cli/config.py 中更新 format_config_content() 函数，集成敏感字段高亮逻辑
- [X] T033 [US3] 在 gitwebhooks/cli/config.py 中添加不区分大小写的敏感关键词匹配

**Checkpoint**: 所有用户故事现在都应独立可用

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: 影响多个用户故事的改进和边缘情况处理

- [X] T034 [P] 在 gitwebhooks/cli/config.py 中添加空配置文件处理（显示文件路径和空文件提示）
- [X] T035 [P] 在 gitwebhooks/cli/config.py 中添加无效 INI 格式的详细错误处理（显示解析错误和行号）
- [X] T036 [P] 在 gitwebhooks/cli/config.py 中添加符号链接处理（显示链接路径和实际文件路径）
- [X] T036a [P] 在 tests/integration/test_config_view_integration.py 中编写测试：符号链接配置文件的端到端测试
- [X] T037 [P] 在 gitwebhooks/cli/config.py 中添加权限错误处理（显示清晰的权限错误信息）
- [X] T037a [P] 在 tests/integration/test_config_view_integration.py 中编写测试：无读取权限时的错误处理测试
- [X] T038 在 README.md 和 README.zh.md 中添加 `config view` 命令文档
- [X] T039 运行 quickstart.md 中的所有示例命令进行验证

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

- **User Story 1 (P1)**: Foundational 完成后可开始 - 不依赖其他故事
- **User Story 2 (P2)**: Foundational 完成后可开始 - 可与 US1 集成但应独立可测
- **User Story 3 (P3)**: Foundational 完成后可开始 - 可与 US1/US2 集成但应独立可测

### Within Each User Story

- 测试必须在实现前编写并确保失败（TDD 方法）
- 核心实现在集成任务之前
- 故事完成后停止并独立验证

### Parallel Opportunities

- Setup 阶段所有标记 [P] 的任务可并行运行
- 一旦 Foundational 阶段完成，所有用户故事可以并行开始（如果团队容量允许）
- 每个用户故事中标记 [P] 的测试可以并行编写
- 不同用户故事可以由不同团队成员并行开发

---

## Parallel Example: User Story 1

```bash
# 一起启动 User Story 1 的所有测试：
Task: "编写测试：locate_config_file() 正确查找默认配置文件"
Task: "编写测试：locate_config_file() 支持 -c 参数指定路径"
Task: "编写测试：cmd_view() 正确格式化配置头部信息"
Task: "编写测试：cmd_view() 按节分组显示配置内容"
```

---

## Parallel Example: User Story 3

```bash
# 一起启动 User Story 3 的所有测试：
Task: "编写测试：is_sensitive_key() 正确识别敏感关键词"
Task: "编写测试：format_sensitive_field() 正确应用 ANSI 颜色代码"
Task: "编写测试：检测 NO_COLOR 环境变量并禁用颜色"
Task: "编写测试：检测 TERM=dumb 环境变量并禁用颜色"
Task: "编写测试：敏感字段高亮显示的端到端测试"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. 完成 Phase 1: Setup
2. 完成 Phase 2: Foundational（关键 - 阻塞所有故事）
3. 完成 Phase 3: User Story 1
4. **停止并验证**: 独立测试 User Story 1
5. 如准备就绪则部署/演示

### Incremental Delivery

1. 完成 Setup + Foundational → 基础就绪
2. 添加 User Story 1 → 独立测试 → 部署/演示（MVP！）
3. 添加 User Story 2 → 独立测试 → 部署/演示
4. 添加 User Story 3 → 独立测试 → 部署/演示
5. 每个故事都在不破坏之前故事的情况下增加价值

### Parallel Team Strategy

如果有多个开发者：

1. 团队一起完成 Setup + Foundational
2. Foundational 完成后：
   - 开发者 A: User Story 1
   - 开发者 B: User Story 2
   - 开发者 C: User Story 3
3. 故事独立完成和集成

---

## Notes

- [P] 任务 = 不同文件，无依赖
- [Story] 标签将任务映射到特定用户故事以便追溯
- 每个用户故事应独立可完成和可测试
- 实现前验证测试失败
- 每个任务或逻辑组后提交
- 在任何检查点停止以独立验证故事
- 避免：模糊任务、同一文件冲突、破坏独立性的跨故事依赖
