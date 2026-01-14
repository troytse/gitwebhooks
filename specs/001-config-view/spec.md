# Feature Specification: 配置文件查看命令

**Feature Branch**: `001-config-view`
**Created**: 2026-01-14
**Status**: Draft
**Input**: User description: "上一个特性分支将install/uninstall/config命令合并到cli中，其中config部分还没完善，还需要增加`gitwebhooks-cli config view` 命令查看目前读取的配置文件位置以及配置内容；在没有使用"-c xxx.ini" 指定配置文件时（默认）应该遵循优先级从 "~/.gitwebhooks.ini" "/usr/local/etc/gitwebhooks.ini" "/etc/gitwebhooks.ini" 这样的顺序读取配置文件。"

## Clarifications

### Session 2026-01-14

- Q: 对于敏感字段（如 `secret`、`password`、`token`），应该如何显示？ → A: 高亮但不隐藏，用颜色标记敏感字段
- Q: 当配置文件不是有效的 INI 格式时，应该如何向用户展示错误信息？ → A: 显示完整的解析错误信息和无效内容行号
- Q: 是否需要支持多种输出格式（如纯文本、JSON），以便于脚本解析或与其他工具集成？ → A: 仅支持默认的易读纯文本格式，不提供其他输出格式选项
- Q: 配置文件来源标识应该如何显示？ → A: 在输出顶部单独一行显示 `Config File: <path> (source: user-specified/auto-detected)`
- Q: 除了 `secret`、`password`、`token` 之外，还有哪些配置项键名应被视为敏感字段？ → A: 仅当配置项键名包含以下关键词时视为敏感：`secret`、`password`、`token`、`key`、`passphrase`
- Q: 敏感关键词匹配是否应该区分大小写？ → A: 不区分大小写，匹配时应忽略大小写（如 `Secret`、`SECRET`、`secret` 都应被识别）

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 查看当前配置文件信息 (Priority: P1)

作为系统管理员，我想要通过 `gitwebhooks-cli config view` 命令查看当前系统正在使用的配置文件位置和内容，以便快速了解服务器的配置状态，而不需要手动查找和打开多个可能的配置文件位置。

**Why this priority**: 这是核心功能，解决了配置文件分散在多个位置带来的查找困难问题，是用户诊断配置问题的首要需求。

**Independent Test**: 可以通过执行 `gitwebhooks-cli config view` 命令独立测试，命令输出应显示配置文件路径和配置内容。

**Acceptance Scenarios**:

1. **Given** 用户未指定配置文件（使用默认优先级）, **When** 执行 `gitwebhooks-cli config view`, **Then** 显示当前生效的配置文件路径（按优先级找到的第一个存在文件）及其完整内容
2. **Given** 用户通过 `-c` 参数指定了配置文件, **When** 执行 `gitwebhooks-cli config view -c /path/to/config.ini`, **Then** 显示指定的配置文件路径及其内容
3. **Given** 多个配置文件位置都存在文件, **When** 执行 `gitwebhooks-cli config view`, **Then** 只显示优先级最高的那个配置文件（`~/.gitwebhooks.ini` > `/usr/local/etc/gitwebhooks.ini` > `/etc/gitwebhooks.ini`）

---

### User Story 2 - 处理配置文件不存在的情况 (Priority: P2)

作为系统管理员，我想要当所有默认配置文件位置都不存在时获得清晰的提示信息，以便我知道需要创建配置文件或使用 `gitwebhooks-cli config init` 命令初始化配置。

**Why this priority**: 这是错误处理的重要部分，防止用户困惑但不是核心功能。

**Independent Test**: 可以通过删除所有默认配置文件位置后执行命令来独立测试。

**Acceptance Scenarios**:

1. **Given** 所有默认配置文件位置都不存在, **When** 执行 `gitwebhooks-cli config view`, **Then** 显示友好的错误信息，列出所有查找过的配置文件路径，并提示使用 `config init` 创建配置
2. **Given** 用户指定的配置文件不存在, **When** 执行 `gitwebhooks-cli config view -c /nonexistent/config.ini`, **Then** 显示清晰的错误信息，说明指定的文件不存在

---

### User Story 3 - 高亮显示敏感配置 (Priority: P3)

作为系统管理员，我想要在查看配置时能够识别出敏感信息（如密钥、密码），以便我更加谨慎地处理和分享配置信息。

**Why this priority**: 这是一个用户体验增强，不影响核心功能。

**Independent Test**: 可以通过查看包含敏感信息的配置文件来独立测试。

**Acceptance Scenarios**:

1. **Given** 配置文件中包含敏感关键词（如 `secret`、`password`、`token`、`key`、`passphrase`）, **When** 执行 `gitwebhooks-cli config view`, **Then** 输出中的敏感字段值应完整显示但使用颜色高亮标记（不隐藏实际值）
2. **Given** 配置文件中没有敏感信息, **When** 执行 `gitwebhooks-cli config view`, **Then** 正常显示所有配置内容

---

### Edge Cases

- **空配置文件**: 显示配置文件路径并提示文件为空或无有效配置节
- **无效的 INI 格式**: 显示完整的解析错误信息，包括错误类型、无效内容的行号和具体问题描述
- **路径包含特殊字符或空格**: 正确转义和显示路径，确保路径被完整解析
- **无读取权限**: 显示清晰的权限错误信息，告知用户需要的权限级别
- **符号链接配置文件**: 显示符号链接的路径和实际指向的真实文件路径

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: 系统必须支持 `gitwebhooks-cli config view` 子命令
- **FR-002**: `config view` 命令必须显示当前生效的配置文件的完整路径
- **FR-003**: `config view` 命令必须以可读格式显示配置文件的完整内容
- **FR-004**: 系统必须按以下优先级顺序查找默认配置文件：
  1. `~/.gitwebhooks.ini`（用户主目录）
  2. `/usr/local/etc/gitwebhooks.ini`（系统本地配置）
  3. `/etc/gitwebhooks.ini`（系统全局配置）
- **FR-005**: 系统必须支持 `-c <path>` 参数覆盖默认配置文件查找
- **FR-006**: 当找不到任何配置文件时，系统必须列出所有查找过的文件路径
- **FR-007**: 当配置文件格式无效时，系统必须显示完整的解析错误信息，包括错误类型、无效内容的行号和具体问题描述
- **FR-008**: 系统必须以易读的纯文本格式展示配置内容，按节分组显示（不支持 JSON 等其他输出格式）
- **FR-009**: 输出必须在顶部单独一行显示配置来源标识，格式为 `Config File: <path> (source: user-specified/auto-detected)`
- **FR-010**: 对于包含以下敏感关键词的配置项，系统必须使用颜色高亮显示完整值（不隐藏）：`secret`、`password`、`token`、`key`、`passphrase`

### Key Entities

- **配置文件路径 (Configuration File Path)**: 表示 INI 格式配置文件的文件系统位置，可以是绝对路径或波浪号扩展的用户目录路径
- **配置优先级 (Configuration Priority)**: 定义多个配置文件位置的查找顺序，决定哪个配置文件生效
- **配置节 (Configuration Section)**: 配置文件中的逻辑分组（如 `[server]`、`[github]`、`[repo/name]`）
- **配置项 (Configuration Key)**: 配置节内的具体设置项（如 `port`、`secret`、`cmd`）

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 用户可以在 5 秒内通过执行单个命令获取当前配置文件路径和内容
- **SC-002**: 系统能够正确识别并显示 100% 的有效 INI 格式配置文件内容
- **SC-003**: 当配置文件不存在时，用户能够在 10 秒内理解错误信息并知道下一步操作（如使用 `config init`）
- **SC-004**: 配置查看命令的输出格式清晰易读，90% 的用户能够快速定位所需配置项
- **SC-005**: 系统支持在所有支持的操作系统平台上正确处理路径分隔符和用户目录扩展

## Assumptions

- 用户已安装 gitwebhooks-cli 工具
- 配置文件使用标准的 INI 格式
- 用户对主目录 (`~`) 有读取权限
- 用户对目标配置文件有读取权限
- 配置文件使用 UTF-8 编码

## Dependencies

- 现有的 CLI 命令框架（已实现 `config init` 子命令）
- 配置文件加载器（ConfigLoader）
- 配置注册表（ConfigurationRegistry）
