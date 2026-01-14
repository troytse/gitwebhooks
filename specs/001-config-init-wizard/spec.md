# Feature Specification: config init 交互式向导

**Feature Branch**: `001-config-init-wizard`
**Created**: 2025-01-14
**Status**: Draft
**Input**: User description: "`config init`默认使用引导式创建配置文件，应该能支持指定配置文件位置如：`gitwebhooks-cli config init system` 生成到 /etc/gitwebhooks.ini `gitwebhooks-cli config init local` 生成到 /usr/local/etc/gitwebhooks.ini；另外初始化配置应该是以引导形式协助创建配置，如先询问用户创建什么级别的配置（如系统/本地/用户，仅未指定时）再询问用户使用什么供应商（github/gitee/gitlab/custom）再询问events、verify、secret，然后询问仓库和本地path以及命令（创建一个即可，如果需要多个用户应该自行编辑ini文件）。"

## Clarifications

### Session 2025-01-14

- Q: 服务器默认配置应如何处理？ → A: 询问每个参数但允许空输入使用默认值（address=0.0.0.0, port=6789, log_file 按配置级别确定）
- Q: webhook 事件类型如何选择？ → A: 提供常见事件的复选列表（push, release, pull_request, tag），并允许输入自定义事件
- Q: 密钥输入如何显示？ → A: 正常显示明文，便于用户确认输入正确
- Q: 工作目录不存在时如何处理？ → A: 报错并要求用户重新输入已存在的路径
- Q: 自定义平台配置如何引导？ → A: 依次询问所有必需参数（header_name、header_value、identifier_path、header_event），提供示例值作为默认值

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 快速初始化默认配置 (Priority: P1)

用户首次部署 git-webhooks-server，运行 `gitwebhooks-cli config init` 命令，通过交互式向导快速创建一个可用的配置文件。

**Why this priority**: 这是核心功能，使新用户能够快速上手，降低配置门槛，是整个 feature 的价值基础。

**Independent Test**: 可以通过运行 `gitwebhooks-cli config init` 并回答一系列问题来完整测试，完成后生成一个包含基本配置（服务器设置、一个平台、一个仓库）的 INI 文件。

**Acceptance Scenarios**:

1. **Given** 系统中不存在配置文件, **When** 用户运行 `gitwebhooks-cli config init` 不带参数, **Then** 系统询问配置级别（系统/本地/用户）
2. **Given** 用户选择配置级别, **When** 用户选择平台类型（如 github）, **Then** 系统询问该平台的相关配置（events、verify、secret）
3. **Given** 用户完成平台配置, **When** 用户输入仓库信息（仓库名、本地路径、部署命令）, **Then** 系统生成完整的 INI 配置文件
4. **Given** 配置文件已存在, **When** 用户再次运行 init 命令, **Then** 系统提示确认覆盖或取消操作

---

### User Story 2 - 指定配置级别创建 (Priority: P2)

用户明确知道需要创建哪个级别的配置，直接通过参数指定（system/local/user），跳过配置级别选择步骤。

**Why this priority**: 为高级用户提供快捷方式，减少交互步骤，提高效率。

**Independent Test**: 可以通过运行 `gitwebhooks-cli config init system` 测试，验证配置文件直接生成到 `/etc/gitwebhooks.ini` 且不询问配置级别。

**Acceptance Scenarios**:

1. **Given** 用户运行 `gitwebhooks-cli config init system`, **When** 命令执行, **Then** 配置文件生成到 `/etc/gitwebhooks.ini`
2. **Given** 用户运行 `gitwebhooks-cli config init local`, **When** 命令执行, **Then** 配置文件生成到 `/usr/local/etc/gitwebhooks.ini`
3. **Given** 用户运行 `gitwebhooks-cli config init user`, **When** 命令执行, **Then** 配置文件生成到 `~/.gitwebhooks.ini`

---

### User Story 3 - 配置多个仓库和平台 (Priority: P3)

用户需要配置多个平台或多个仓库，通过向导创建第一个配置后，手动编辑 INI 文件添加更多条目。

**Why this priority**: 这是次要场景，向导专注于创建最小可用配置，多仓库配置可以通过编辑完成，保持向导简洁。

**Independent Test**: 创建基础配置后，编辑 INI 文件添加第二个仓库配置，验证服务器能正确读取所有仓库配置。

**Acceptance Scenarios**:

1. **Given** 用户通过向导创建了第一个仓库配置, **When** 用户手动编辑 INI 文件添加第二个仓库, **Then** 服务器能同时处理两个仓库的 webhook

---

### Edge Cases

- **目标目录无写权限**: 选择的配置级别对应的目录用户无写权限时，向导应提示错误并建议使用其他级别或 sudo
- **配置文件已存在**: 目标位置已存在同名配置文件时，提示用户确认覆盖、备份旧文件或取消操作
- **用户中断输入**: 用户在向导过程中按 Ctrl+C，应清理部分创建的文件并优雅退出
- **无效输入验证**: 仓库名称格式不正确（非 owner/repo 格式）、本地路径不存在（必须使用已存在的目录，不自动创建）等，应提示并允许重新输入
- **多个平台配置**: 向导专注于创建最小可用配置，每次仅引导配置一个平台。如需配置多个平台，用户在向导完成后手动编辑 INI 文件添加（符合 MVP 简洁原则）

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: 系统必须支持通过 `gitwebhooks-cli config init [level]` 命令启动交互式配置向导，其中 level 可选值为 `system`、`local`、`user` 或省略
- **FR-002**: 当 level 参数省略时，系统必须提示用户选择配置级别（system/local/user），并说明每个级别的文件位置
- **FR-003**: 系统必须根据配置级别将配置文件生成到对应位置：
  - `system`: `/etc/gitwebhooks.ini`
  - `local`: `/usr/local/etc/gitwebhooks.ini`
  - `user`: `~/.gitwebhooks.ini` (用户主目录)
- **FR-004**: 系统必须引导用户选择至少一个 Git 平台（github/gitee/gitlab/custom）进行配置
- **FR-005**: 对于选中的平台，系统必须询问并配置以下参数：
  - `handle_events`: 使用数字索引选择常见事件（1=push、2=release、3=pull_request、4=tag），支持逗号分隔多选和自定义事件输入。当用户直接按 Enter（未选择任何事件）时，默认使用 `push` 事件
  - `verify`: 是否启用签名验证
  - `secret`: 验证密钥（当启用验证时），正常显示明文
  - 对于 `custom` 平台，还需询问：header_name、header_value、identifier_path、header_event，提供示例值作为默认值
- **FR-006**: 系统必须询问用户配置至少一个仓库，包括：
  - 仓库标识（owner/repo 格式）
  - 本地工作目录路径（cwd）
  - 部署命令（cmd）
- **FR-007**: 系统必须生成符合 INI 格式标准的配置文件，包含以下必要部分：
  - `[server]` 部分：address、port、log_file（向导依次询问每个参数，允许空输入使用默认值：address=0.0.0.0, port=6789, log_file 根据配置级别自动确定）
  - 选中的平台部分（如 `[github]`）：handle_events、verify、secret
  - 仓库部分（如 `[repo/owner/name]`）：cwd、cmd
- **FR-008**: 当目标配置文件已存在时，系统必须提示用户确认操作（覆盖/备份/取消）
- **FR-009**: 系统必须在配置生成成功后显示文件路径和后续操作建议，包括：
  - 配置文件的完整路径
  - 如何启动服务：`systemctl start git-webhooks-server` 或 `gitwebhooks-cli -c <config-file>`
  - 如何查看服务状态：`systemctl status git-webhooks-server`
  - 如何测试 Webhook：使用 curl 或 Git 平台测试功能
  - 如何添加更多平台/仓库：手动编辑 INI 文件的提示
- **FR-010**: 向导必须在任何时候允许用户输入 Ctrl+C 退出，并清理已创建的部分文件
- **FR-011**: 系统必须验证用户输入的有效性：
  - 仓库名称必须符合 owner/repo 格式
  - 本地路径必须是已存在的有效目录路径（不自动创建目录）
  - 部署命令不能为空
- **FR-012**: 当用户选择配置级别对应目录无写权限时，系统必须提示错误并建议使用其他级别或 sudo

### Key Entities

- **Config Level (配置级别)**: 表示配置文件的作用域，包含 system、local、user 三种，决定了文件的存储位置和权限要求。文档中统一使用英文术语 "Config Level" 或中英对照 "Config Level (配置级别)"
- **平台配置 (Platform Config)**: 表示一个 Git 平台的配置信息，包含平台类型、事件处理、验证设置和密钥
- **仓库配置 (Repository Config)**: 表示一个仓库的部署配置，包含仓库标识、工作目录和部署命令
- **配置文件 (Config File)**: INI 格式的配置文件，包含服务器、平台和仓库的所有配置信息

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 新用户可以在 3 分钟内通过向导完成第一个可用的配置文件创建
- **SC-002**: 向导生成的配置文件能够被服务器正确加载并处理 webhook 请求
- **SC-003**: 用户首次尝试配置成功率达到 90% 以上（无需查阅文档）
- **SC-004**: 配置文件生成位置准确率达到 100%（system/local/user 对应正确路径）
- **SC-005**: 所有无效输入都能被正确识别并提示用户重新输入，不会生成无效配置文件
