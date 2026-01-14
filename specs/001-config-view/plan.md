# Implementation Plan: 配置文件查看命令

**Branch**: `001-config-view` | **Date**: 2026-01-14 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-config-view/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

为 `gitwebhooks-cli` 添加 `config view` 子命令，用于查看当前生效的配置文件位置和内容。该命令支持配置文件优先级查找（`~/.gitwebhooks.ini` > `/usr/local/etc/gitwebhooks.ini` > `/etc/gitwebhooks.ini`），显示配置来源标识，并可高亮显示敏感字段。实现将扩展现有的 CLI 配置模块，使用 Python 标准库完成所有功能。

## Technical Context

**Language/Version**: Python 3.7+ (与项目保持一致)
**Primary Dependencies**: Python 标准库（configparser、pathlib、os、sys）
**Storage**: INI 配置文件（只读）
**Testing**: pytest（项目现有测试框架）
**Target Platform**: Linux/macOS（支持 systemd 和标准 shell 环境）
**Project Type**: 单一 Python 包项目（gitwebhooks/）
**Performance Goals**: 命令应在 5 秒内完成配置文件读取和显示（与 spec.md SC-001 保持一致）
**Constraints**: 无外部依赖，仅使用 Python 标准库；必须支持 ANSI 颜色代码
**Scale/Scope**: 新增约 200-300 行代码，单个新模块函数

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Required Compliance Gates

All features MUST pass the following gates from `.specify/memory/constitution.md`:

1. **Simplicity & Minimalism**: ✅ PASS
   - 使用 Python 标准库（configparser、pathlib、os）
   - 无外部依赖
   - 扩展现有 CLI 配置模块（gitwebhooks/cli/config.py）
   - 单一职责：仅负责显示配置，不修改配置
   - 代码量约 200-300 行，符合模块大小要求

2. **Platform Neutrality**: ✅ PASS
   - 不涉及 Git 平台特定逻辑
   - 配置文件路径使用标准优先级，适用于所有平台

3. **Configuration-Driven Behavior**: ✅ PASS
   - 本功能只读取和显示配置，不修改配置驱动行为

4. **Security by Verification**: ✅ PASS
   - 仅读取配置文件，不修改
   - 敏感字段高亮显示但不隐藏（用户已确认）
   - 不涉及签名验证逻辑

5. **Service Integration**: ✅ PASS
   - 不影响 systemd 服务集成
   - 不修改日志配置

6. **Professional Commit Standards**: ✅ PASS
   - 提交时需遵循项目规范：`类型: 简短描述`
   - 不包含 AI 签名

### Violation Justification

无违规。所有门控检查通过。

## Project Structure

### Documentation (this feature)

```text
specs/001-config-view/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (N/A for CLI command)
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
gitwebhooks/
├── cli/
│   ├── __init__.py
│   ├── config.py         # MODIFY: Add cmd_view() function
│   ├── service.py
│   └── prompts.py
├── config/
│   ├── __init__.py
│   ├── loader.py         # USE: Existing ConfigLoader class
│   └── models.py
└── utils/
    ├── __init__.py
    ├── constants.py      # MODIFY: Add config path constants
    └── exceptions.py     # USE: ConfigurationError

tests/
├── unit/
│   └── cli/
│       └── test_config_view.py  # NEW: Unit tests for config view
└── integration/
    └── test_config_view_integration.py  # NEW: Integration tests
```

**Structure Decision**: 选择单一项目结构（Option 1），这是项目现有的结构。新功能将扩展现有的 `gitwebhooks/cli/config.py` 模块，添加 `cmd_view()` 函数实现 `config view` 子命令。

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

无违规。本节不需要填写。
