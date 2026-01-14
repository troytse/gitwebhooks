# Feature Specification: CLI Service Installation

**Feature Branch**: `001-cli-service-install`
**Created**: 2026-01-14
**Status**: Draft
**Input**: User description: "目前改为使用pip包安装的形式安装，用户安装完成后应该只有gitwebhooks-cli命令，那么则应该不需要安装脚本了，把安装脚本的功能放到cli命令中更为合适，仅需要其中的安装为服务的功能即可，最后还需要更新README*中的如何使用的章节"

## Clarifications

### Session 2026-01-14

- Q: 命令格式应该如何组织？ → A: 使用子命令格式：`gitwebhooks-cli service install/uninstall` 和 `gitwebhooks-cli config init`
- Q: 默认配置文件路径应该放在哪里？ → A: 用户主目录 `~/.gitwebhook.ini`（而非系统级 `/usr/local/etc/`）
- Q: config init 如何工作？ → A: 交互式问答形式，引导用户逐步创建配置

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Install as systemd Service (Priority: P1)

用户通过 `pip install gitwebhooks` 安装包后，只需运行 `gitwebhooks-cli service install` 命令即可将 gitwebhooks 安装为 systemd 服务，无需手动复制文件或编辑配置。

**Why this priority**: 这是核心安装体验，直接影响用户能否快速部署服务。移除 install.sh 后，这是唯一的安装服务途径。

**Independent Test**: 可以独立测试通过 CLI 子命令安装服务，验证服务文件正确创建并启用。

**Acceptance Scenarios**:

1. **Given** 用户已通过 pip 安装 gitwebhooks，**When** 执行 `gitwebhooks-cli service install`，**Then** systemd 服务文件被创建到系统目录，服务已启用并运行
2. **Given** 服务已安装，**When** 再次执行 `gitwebhooks-cli service install`，**Then** 提示服务已存在，询问是否覆盖
3. **Given** 用户没有 root 权限，**When** 执行 `gitwebhooks-cli service install`，**Then** 显示需要 sudo 权限的友好提示

---

### User Story 2 - Uninstall systemd Service (Priority: P1)

用户可以通过 `gitwebhooks-cli service uninstall` 命令卸载已安装的 systemd 服务，清理相关文件。

**Why this priority**: 与安装功能对应，提供完整的生命周期管理能力。

**Independent Test**: 可以独立测试卸载命令，验证服务被正确停止、禁用和删除。

**Acceptance Scenarios**:

1. **Given** 服务已安装，**When** 执行 `gitwebhooks-cli service uninstall`，**Then** 服务被停止、禁用，服务文件被删除
2. **Given** 服务未安装，**When** 执行 `gitwebhooks-cli service uninstall`，**Then** 提示服务不存在
3. **Given** 卸载时配置文件存在，**Then** 询问是否同时删除配置文件

---

### User Story 3 - Initialize Configuration (Priority: P2)

首次安装时，用户可以通过 `gitwebhooks-cli config init` 命令以交互式问答方式创建配置文件到用户主目录（`~/.gitwebhook.ini`）。

**Why this priority**: 降低新用户上手难度，提供开箱即用的体验。交互式问答确保配置正确性。

**Independent Test**: 可以独立测试配置初始化功能，验证配置文件生成到正确位置且内容有效。

**Acceptance Scenarios**:

1. **Given** 配置文件不存在，**When** 执行 `gitwebhooks-cli config init`，**Then** 启动问答流程，引导用户输入服务器地址、端口、webhook secret 等配置
2. **Given** 配置文件已存在，**When** 执行 `gitwebhooks-cli config init`，**Then** 提示文件已存在，询问是否覆盖
3. **Given** 问答过程中用户输入无效值，**Then** 提示错误并重新询问该问题
4. **Given** 用户在问答中按 Ctrl+C，**Then** 询问是否确认退出，未保存的修改不写入文件

---

### User Story 4 - Updated Documentation (Priority: P2)

README.md 和 README.zh.md 文档更新为新的安装和使用方式，移除 install.sh 相关说明。

**Why this priority**: 文档是用户了解产品的第一入口，必须与实际安装方式保持一致。

**Independent Test**: 可以独立验证文档内容的准确性和完整性。

**Acceptance Scenarios**:

1. **Given** 用户阅读 README，**When** 查看安装章节，**Then** 看到 `pip install` 安装方式
2. **Given** 用户阅读 README，**When** 查看使用章节，**Then** 看到 `gitwebhooks-cli` 命令和服务安装说明
3. **Given** 用户阅读 README，**Then** 不再出现 install.sh 脚本的引用

---

### Edge Cases

- 如果 systemd 不在系统上（如非 Linux 系统），CLI 命令应友好提示不支持
- 如果服务目录不可写，应给出明确的错误提示和解决建议
- 如果配置文件路径已被其他文件占用，应询问用户操作
- 卸载时如果服务正在处理 webhook，应先优雅停止再卸载

## Requirements *(mandatory)*

### Functional Requirements

**CLI 子命令结构**:
- **FR-001**: CLI 必须支持 `gitwebhooks-cli service install` 子命令，安装 systemd 服务
- **FR-002**: CLI 必须支持 `gitwebhooks-cli service uninstall` 子命令，卸载 systemd 服务
- **FR-003**: CLI 必须支持 `gitwebhooks-cli config init` 子命令，交互式创建配置文件
- **FR-004**: CLI 必须支持 `gitwebhooks-cli --help` 显示所有可用子命令和选项
- **FR-005**: CLI 必须支持 `gitwebhooks-cli service --help` 和 `gitwebhooks-cli config --help` 显示子命令帮助
- **FR-005.5**: CLI 实现必须仅使用 Python 标准库，不得引入外部依赖（符合宪法原则 I）

**服务安装功能**:
- **FR-006**: 安装服务时必须检测是否有 sudo/root 权限，没有则提示用户
- **FR-007**: 服务文件必须包含正确的 ExecStart 指向，使用 `~/.gitwebhook.ini` 作为默认配置路径
- **FR-008**: 安装/卸载操作必须有确认提示，避免误操作
- **FR-009**: 服务安装必须使用 systemd 的标准目录结构（`/etc/systemd/system/`）

**配置初始化功能**:
- **FR-010**: `config init` 必须使用交互式问答格式，逐步引导用户输入配置
- **FR-011**: 问答必须覆盖：服务器监听地址、端口、日志文件路径、各平台的 webhook secret
- **FR-012**: 用户输入无效值时，必须显示错误原因并重新询问
- **FR-013**: 支持用户按 Ctrl+C 中断，询问确认后退出且不保存
- **FR-014**: 默认配置文件路径为 `~/.gitwebhook.ini`（用户主目录）

**文档和清理**:
- **FR-015**: 移除 install.sh 脚本文件
- **FR-016**: README.md 和 README.zh.md 必须更新为新的命令结构（子命令格式）
- **FR-017**: README 中更新默认配置路径为 `~/.gitwebhook.ini`

### Key Entities

- **Service File**: systemd 单元文件，定义服务启动参数和依赖关系
- **Configuration File**: INI 格式的配置文件，包含服务器和仓库设置
- **CLI Command**: gitwebhooks-cli 可执行文件，提供服务安装/卸载子命令

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 用户可以在 30 秒内完成服务安装（从执行命令到服务运行）
- **SC-002**: 新用户首次安装成功率超过 95%（无配置错误导致的失败）
- **SC-003**: 安装后的服务可以正常处理 webhook 请求（通过测试验证）
- **SC-004**: 卸载后系统无残留文件（服务文件、日志等被清理）
- **SC-005**: README 文档中不再出现 install.sh 的任何引用
- **SC-006**: CLI 帮助信息清晰完整，用户无需查阅文档即可完成安装

## Assumptions

1. 目标系统是支持 systemd 的 Linux 发行版
2. 用户有 sudo 权限或可以以 root 身份执行命令（仅用于服务安装/卸载）
3. Python 包已通过 pip 安装到系统 Python 环境或虚拟环境
4. systemd 服务目录为 `/etc/systemd/system/`
5. 默认配置文件位置为 `~/.gitwebhook.ini`（用户主目录，无需 sudo 权限）
6. 用户熟悉基本的命令行交互操作（回答问题、确认提示等）

## Dependencies

- systemd 服务必须在系统上可用
- Python 3.6+ 已安装
- pip 包管理器可用

## Out of Scope

- 非 Linux 系统的服务安装（如 Windows 服务、 macOS launchd）
- systemd 以外的服务管理器（如 sysvinit、 upstart）
- 图形化的安装向导
- 远程服务部署功能
- 服务健康检查和自动恢复配置
