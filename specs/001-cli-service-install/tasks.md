# Tasks: CLI Service Installation

**Input**: Design documents from `/specs/001-cli-service-install/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: 本项目使用手动测试方式（参考宪法测试原则），不包含自动化测试任务。

**Organization**: 任务按用户故事分组，确保每个故事可独立实现和测试。

## Format: `[ID] [P?] [Story] Description`

- **[P]**: 可并行执行（不同文件，无依赖）
- **[Story]**: 任务所属用户故事（US1, US2, US3, US4）
- 包含精确文件路径

## Path Conventions

- **Python 包**: `gitwebhooks/` 在仓库根目录
- **CLI 子模块**: `gitwebhooks/cli/`
- **工具模块**: `gitwebhooks/utils/`
- **文档**: `README.md`, `README.zh.md` 在根目录

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: 项目初始化和基本结构

- [X] T001 创建 CLI 子模块目录结构 `gitwebhooks/cli/`
- [X] T002 创建 `gitwebhooks/cli/__init__.py` 导出 `register_subparsers()` 函数
- [X] T003 [P] 创建 `gitwebhooks/cli/service.py` 空模块文件
- [X] T004 [P] 创建 `gitwebhooks/cli/config.py` 空模块文件
- [X] T005 [P] 创建 `gitwebhooks/cli/prompts.py` 空模块文件
- [X] T006 [P] 创建 `gitwebhooks/utils/systemd.py` 空模块文件

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: 核心基础设施，必须在任何用户故事之前完成

**⚠️ CRITICAL**: 此阶段完成前，不能开始任何用户故事工作

- [X] T007 重构 `gitwebhooks/main/__init__.py` 使用 argparse 替代 getopt，支持子命令解析
- [X] T008 在 `gitwebhooks/main/__init__.py` 中更新默认配置路径为 `~/.gitwebhook.ini`
- [X] T009 在 `gitwebhooks/main/__init__.py` 中实现主命令帮助信息（包含子命令列表）
- [X] T010 在 `gitwebhooks/utils/systemd.py` 中实现 `check_systemd()` 检测 systemctl 可用性
- [X] T011 在 `gitwebhooks/utils/systemd.py` 中实现 `check_root_permission()` 检测 root 权限
- [X] T012 在 `gitwebhooks/utils/systemd.py` 中实现 `generate_service_file()` 生成 systemd 单元文件
- [X] T013 在 `gitwebhooks/utils/systemd.py` 中定义 `SERVICE_TEMPLATE` 常量（内嵌服务文件模板）
- [X] T014 在 `gitwebhooks/cli/prompts.py` 中实现 `ask_question()` 通用问答函数
- [X] T015 在 `gitwebhooks/cli/prompts.py` 中实现 `ask_yes_no()` 是/否确认函数
- [X] T016 在 `gitwebhooks/cli/prompts.py` 中实现输入验证器：`validate_port()`, `validate_address()`, `validate_path()`

**Checkpoint**: 基础设施就绪 - 用户故事实现现在可以并行开始

---

## Phase 3: User Story 1 - Install as systemd Service (Priority: P1) 🎯 MVP

**Goal**: 用户可以通过 `gitwebhooks-cli service install` 命令安装 systemd 服务

**Independent Test**: 运行 `sudo gitwebhooks-cli service install`，验证服务文件创建到 `/etc/systemd/system/`，服务已启用并运行

### Implementation for User Story 1

- [X] T017 [P] 在 `gitwebhooks/cli/service.py` 中实现 `cmd_install()` 主函数，使用 ~/.gitwebhook.ini 作为默认配置路径
- [X] T018 [US1] 在 `gitwebhooks/cli/service.py` 中实现 `install_service()` 执行服务安装逻辑
- [X] T019 [US1] 在 `gitwebhooks/cli/service.py` 中实现 `check_service_exists()` 检查服务是否已安装
- [X] T020 [US1] 在 `gitwebhooks/cli/service.py` 中实现 `confirm_overwrite()` 询问覆盖确认
- [X] T021 [US1] 在 `gitwebhooks/cli/service.py` 中实现 `enable_and_start_service()` 启用并启动服务
- [X] T022 [US1] 在 `gitwebhooks/cli/service.py` 中添加 `--force` 参数支持
- [X] T023 [US1] 在 `gitwebhooks/cli/service.py` 中实现权限检测和错误处理（E_PERM, E_SYSTEMD）
- [X] T024 [US1] 在 `gitwebhooks/cli/__init__.py` 中注册 `service` 子解析器和 `install` 子命令
- [X] T025 [US1] 在 `gitwebhooks/cli/__init__.py` 中实现 `service --help` 帮助信息
- [X] T026 [US1] 在 `gitwebhooks/main/__init__.py` 中集成子命令解析器，支持 `service install` 调用

**Checkpoint**: 此时 User Story 1 应完全功能且可独立测试

---

## Phase 4: User Story 2 - Uninstall systemd Service (Priority: P1)

**Goal**: 用户可以通过 `gitwebhooks-cli service uninstall` 命令卸载 systemd 服务

**Independent Test**: 运行 `sudo gitwebhooks-cli service uninstall`，验证服务停止、禁用，服务文件删除

### Implementation for User Story 2

- [X] T027 [P] 在 `gitwebhooks/cli/service.py` 中实现 `cmd_uninstall()` 主函数
- [X] T028 [US2] 在 `gitwebhooks/cli/service.py` 中实现 `uninstall_service()` 执行服务卸载逻辑
- [X] T029 [US2] 在 `gitwebhooks/cli/service.py` 中实现 `stop_and_disable_service()` 停止并禁用服务
- [X] T030 [US2] 在 `gitwebhooks/cli/service.py` 中实现 `remove_service_file()` 删除服务文件
- [X] T031 [US2] 在 `gitwebhooks/cli/service.py` 中实现 `handle_config_cleanup()` 处理配置文件删除
- [X] T032 [US2] 在 `gitwebhooks/cli/service.py` 中添加 `--purge` 参数支持
- [X] T033 [US2] 在 `gitwebhooks/cli/service.py` 中实现卸载错误处理（E_PERM, E_NOT_FOUND）
- [X] T034 [US2] 在 `gitwebhooks/cli/__init__.py` 中注册 `uninstall` 子命令
- [X] T035 [US2] 在 `gitwebhooks/cli/service.py` 中更新 `service --help` 包含 uninstall 信息

**Checkpoint**: 此时 User Stories 1 AND 2 都应独立工作

---

## Phase 5: User Story 3 - Initialize Configuration (Priority: P2)

**Goal**: 用户可以通过 `gitwebhooks-cli config init` 命令以交互式问答方式创建配置文件

**Independent Test**: 运行 `gitwebhooks-cli config init`，验证配置文件生成到 `~/.gitwebhook.ini`，内容有效

### Implementation for User Story 3

- [X] T036 [P] 在 `gitwebhooks/cli/config.py` 中实现 `cmd_init()` 主函数
- [X] T037 [P] 在 `gitwebhooks/cli/prompts.py` 中定义 `QUESTIONS` 列表（服务器地址、端口、日志、SSL、webhook平台）
- [X] T038 [P] 在 `gitwebhooks/cli/prompts.py` 中实现 `validate_bool()` 布尔值验证器
- [X] T039 [US3] 在 `gitwebhooks/cli/config.py` 中实现 `run_interactive_questions()` 执行问答流程
- [X] T040 [US3] 在 `gitwebhooks/cli/config.py` 中实现 `collect_server_config()` 收集服务器配置
- [X] T041 [US3] 在 `gitwebhooks/cli/config.py` 中实现 `collect_ssl_config()` 收集 SSL 配置
- [X] T042 [US3] 在 `gitwebhooks/cli/config.py` 中实现 `collect_webhook_config()` 收集 webhook 平台配置
- [X] T043 [US3] 在 `gitwebhooks/cli/config.py` 中实现 `write_config_file()` 写入 INI 配置文件
- [X] T044 [US3] 在 `gitwebhooks/cli/config.py` 中实现 `set_config_permissions()` 设置文件权限为 0600
- [X] T045 [US3] 在 `gitwebhooks/cli/config.py` 中实现 `handle_existing_config()` 处理已存在配置
- [X] T046 [US3] 在 `gitwebhooks/cli/config.py` 中实现 Ctrl+C 中断处理，捕获 KeyboardInterrupt 异常并询问确认退出
- [X] T047 [US3] 在 `gitwebhooks/cli/config.py` 中添加 `--output` 参数支持
- [X] T048 [US3] 在 `gitwebhooks/cli/config.py` 中实现输入验证和错误提示（端口、路径等）
- [X] T049 [US3] 在 `gitwebhooks/cli/__init__.py` 中注册 `config` 子解析器和 `init` 子命令
- [X] T050 [US3] 在 `gitwebhooks/cli/__init__.py` 中实现 `config --help` 帮助信息
- [X] T051 [US3] 在 `gitwebhooks/main/__init__.py` 中集成 `config init` 子命令调用

**Checkpoint**: 所有用户故事现在应独立功能

---

## Phase 6: User Story 4 - Updated Documentation (Priority: P2)

**Goal**: README.md 和 README.zh.md 更新为新的安装和使用方式，移除 install.sh 引用

**Independent Test**: 查看 README.md 和 README.zh.md，验证只包含 `pip install` 安装方式，无 install.sh 引用

### Implementation for User Story 4

- [X] T052 [P] 在 `README.md` 中更新安装章节为 `pip install gitwebhooks`
- [X] T053 [P] 在 `README.md` 中更新使用章节，添加 `gitwebhooks-cli service install` 说明
- [X] T054 [P] 在 `README.md` 中添加 `gitwebhooks-cli config init` 使用示例
- [X] T055 [P] 在 `README.md` 中更新默认配置路径为 `~/.gitwebhook.ini`
- [X] T056 [P] 在 `README.zh.md` 中更新安装章节为 `pip install gitwebhooks`
- [X] T057 [P] 在 `README.zh.md` 中更新使用章节，添加 CLI 子命令说明（中文）
- [X] T058 [P] 在 `README.zh.md` 中添加 `gitwebhooks-cli config init` 使用示例（中文）
- [X] T059 [P] 在 `README.zh.md` 中更新默认配置路径为 `~/.gitwebhook.ini`
- [X] T060 [US4] 验证 README.md 中无 install.sh 引用
- [X] T061 [US4] 验证 README.zh.md 中无 install.sh 引用

**Checkpoint**: 所有用户故事和文档更新完成

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: 影响多个用户故事的改进

- [X] T062 [P] 删除 `install.sh` 脚本文件
- [X] T063 [P] 删除 `message.sh` 脚本文件（install.sh 依赖）
- [X] T064 [P] 删除 `git-webhooks-server.service.sample` 文件（功能已集成到 CLI）
- [X] T065 [P] 删除 `installed.env` 相关代码引用（如有）
- [X] T066 更新 `.gitignore` 排除 `install.sh` 和相关文件（如果存在）
- [X] T067 更新 `CLAUDE.md` 移除 install.sh 相关文档引用
- [X] T068 验证 `gitwebhooks-cli --help` 输出完整且清晰
- [X] T069 验证 `gitwebhooks-cli service --help` 输出完整且清晰
- [X] T070 验证 `gitwebhooks-cli config --help` 输出完整且清晰
- [ ] T071 手动测试服务安装：`sudo gitwebhooks-cli service install`
- [ ] T072 手动测试服务卸载：`sudo gitwebhooks-cli service uninstall`
- [ ] T073 手动测试配置初始化：`gitwebhooks-cli config init`
- [X] T074 验证向后兼容：`gitwebhooks-cli -c /path/to/config.ini` 仍可工作

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: 无依赖 - 可立即开始
- **Foundational (Phase 2)**: 依赖 Setup 完成 - 阻塞所有用户故事
- **User Stories (Phase 3-6)**: 都依赖 Foundational 阶段完成
  - US1 (Phase 3) 和 US2 (Phase 4) 可并行开发
  - US3 (Phase 5) 和 US4 (Phase 6) 可并行开发
- **Polish (Phase 7)**: 依赖所有期望的用户故事完成

### User Story Dependencies

- **User Story 1 (P1)**: Foundational 完成后可开始 - 无其他故事依赖
- **User Story 2 (P1)**: Foundational 完成后可开始 - 与 US1 独立（但同一模块）
- **User Story 3 (P2)**: Foundational 完成后可开始 - 与 US1/US2 独立
- **User Story 4 (P2)**: Foundational 完成后可开始 - 与其他故事独立

### Within Each User Story

- 标记 [P] 的任务可并行执行
- US1: T017-T026 按顺序执行（T017 可与后续某些任务并行）
- US2: T027-T035 按顺序执行（T027 可与后续某些任务并行）
- US3: T036-T051 中 T037-T039 可并行
- US4: T052-T061 全部可并行

### Parallel Opportunities

- Setup 阶段 T003-T006 全部可并行
- US3 中 T037-T039 可并行（prompts.py 中的不同验证器）
- US4 中 T052-T061 全部可并行（两个文档文件）
- Polish 阶段 T062-T066 全部可并行（删除文件）

---

## Parallel Example: User Story 3 (Config Init)

```bash
# 并行创建验证器：
Task: "在 gitwebhooks/cli/prompts.py 中定义 QUESTIONS 列表"
Task: "在 gitwebhooks/cli/prompts.py 中实现 validate_bool() 布尔值验证器"

# 并行更新两个 README：
Task: "在 README.md 中更新安装章节"
Task: "在 README.zh.md 中更新安装章节"

# 并行删除文件：
Task: "删除 install.sh 脚本文件"
Task: "删除 message.sh 脚本文件"
Task: "删除 git-webhooks-server.service.sample 文件"
```

---

## Implementation Strategy

### MVP First (User Stories 1 & 2 Only)

1. 完成 Phase 1: Setup
2. 完成 Phase 2: Foundational（关键 - 阻塞所有故事）
3. 完成 Phase 3: User Story 1（服务安装）
4. 完成 Phase 4: User Story 2（服务卸载）
5. **停止并验证**: 独立测试 US1 和 US2
6. 如准备好则部署/演示

### Incremental Delivery

1. 完成 Setup + Foundational → 基础就绪
2. 添加 User Story 1 & 2 → 独立测试 → 部署/演示（MVP！）
3. 添加 User Story 3 → 独立测试 → 部署/演示
4. 添加 User Story 4 → 独立测试 → 部署/演示
5. 完成 Polish → 最终发布

### Parallel Team Strategy

单个开发者时：
1. 顺序完成 Setup → Foundational
2. 优先完成 US1 & US2（P1，核心功能）
3. 再完成 US3 & US4（P2，增强功能）

多个开发者时：
1. 团队一起完成 Setup + Foundational
2. Foundational 完成后：
   - Developer A: User Story 1
   - Developer B: User Story 2
   - Developer C: User Story 3
3. US1/US2 完成后 Developer A/B 转 US4

---

## Notes

- [P] 任务 = 不同文件，无依赖，可并行
- [Story] 标签将任务映射到特定用户故事以便跟踪
- 每个用户故事应可独立完成和测试
- 使用宪法中的手动测试方法验证功能
- 每个任务或逻辑组后提交代码
- 在任何检查点停止以独立验证故事
- 避免：模糊任务、同文件冲突、破坏独立性的跨故事依赖

---

## Task Summary

- **Total Tasks**: 74
- **Setup Phase**: 6 tasks
- **Foundational Phase**: 10 tasks
- **User Story 1**: 10 tasks
- **User Story 2**: 9 tasks
- **User Story 3**: 16 tasks
- **User Story 4**: 10 tasks
- **Polish Phase**: 13 tasks

**MVP Scope** (User Stories 1 & 2): 35 tasks + Setup (6) + Foundational (10) = 51 tasks
