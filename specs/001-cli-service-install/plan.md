# Implementation Plan: CLI Service Installation

**Branch**: `001-cli-service-install` | **Date**: 2026-01-14 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-cli-service-install/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

将 `install.sh` 脚本的功能迁移到 CLI 子命令中，提供 `gitwebhooks-cli service install/uninstall` 和 `gitwebhooks-cli config init` 命令。技术方法是在现有 CLI 架构基础上添加子命令解析，使用 Python 标准库实现 systemd 服务文件生成和交互式配置初始化。

## Technical Context

**Language/Version**: Python 3.7+ (与宪法要求一致)
**Primary Dependencies**: Python 标准库（argparse 用于子命令，tempfile 用于文件操作，pathlib 用于路径处理）
**Storage**: INI 配置文件（`~/.gitwebhook.ini`），systemd 服务文件（`/etc/systemd/system/`）
**Testing**: pytest（现有测试框架）
**Target Platform**: Linux with systemd（与项目 V.5 原则一致）
**Project Type**: single（CLI 工具）
**Performance Goals**: 30秒内完成服务安装（SC-001）
**Constraints**: 无外部依赖（原则 I），仅支持 systemd（Out of Scope）
**Scale/Scope**: 17条功能需求，4个用户故事，3个优先级

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Required Compliance Gates

All features MUST pass the following gates from `.specify/memory/constitution.md`:

1. **Simplicity & Minimalism**: ✅ PASS
   - 使用 Python 标准库（argparse, subprocess, pathlib）
   - 无外部依赖
   - 配置保持 INI 格式
   - 每个子命令独立模块（< 400行）

2. **Platform Neutrality**: ✅ PASS
   - 服务安装仅针对 Linux systemd（平台特性，符合 Out of Scope）
   - 不影响 webhook 处理的平台中立性

3. **Configuration-Driven Behavior**: ✅ PASS
   - 配置初始化创建 INI 文件
   - 不修改仓库配置逻辑

4. **Security by Verification**: ✅ PASS
   - 配置文件权限设置为 0600
   - 不修改现有验证逻辑

5. **Service Integration**: ✅ PASS
   - 从 install.sh 迁移到 CLI，功能保持一致
   - 日志配置保持不变

6. **Professional Commit Standards**: ✅ PASS
   - 提交信息将遵循 `类型: 简短描述` 格式

### Violation Justification

无违规。所有门禁通过。

## Project Structure

### Documentation (this feature)

```text
specs/001-cli-service-install/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (CLI contracts)
└── tasks.md             # Phase 2 output (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
gitwebhooks/
├── cli.py               # 现有 CLI 入口，需要重构支持子命令
├── service.py           # 现有服务器类（不变）
├── cli/                 # 新增：CLI 子命令模块
│   ├── __init__.py
│   ├── service.py       # service install/uninstall 子命令
│   ├── config.py        # config init 子命令
│   └── prompts.py       # 交互式问答提示模板
├── utils/
│   ├── systemd.py       # 新增：systemd 服务文件生成
│   └── config.py        # 现有配置工具（可能需要扩展）
└── config/              # 现有配置模块（不变）
```

**Structure Decision**: 采用单一项目结构，在 `gitwebhooks/` 包内添加 `cli/` 子模块。这符合项目的模块化包结构原则，每个子模块职责单一（服务安装、配置初始化）。

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

无违规需要跟踪。

---

## Phase 0: Research

### Research Tasks

1. **CLI 子命令最佳实践**
   - 研究 argparse 子命令实现模式
   - 确定帮助信息格式

2. **systemd 服务文件规范**
   - 研究 systemd 单元文件格式
   - 确定 ExecStart、Restart、User 等标准配置

3. **交互式 CLI 模式**
   - 研究 Python 标准库输入验证方法
   - 确定 Ctrl+C 处理模式

4. **配置文件默认值**
   - 研究现有 git-webhooks-server.ini.sample
   - 确定默认服务器地址、端口等

### Research Output

参见 `research.md`（待生成）

---

## Phase 1: Design

### Data Model

参见 `data-model.md`（待生成）

- CLI 命令结构（子命令、选项、参数）
- 配置文件结构（INI sections 和 keys）
- systemd 服务文件结构

### CLI Contracts

参见 `contracts/` 目录（待生成）

- `service.md` - service install/uninstall 命令契约
- `config.md` - config init 命令契约

### Quickstart Guide

参见 `quickstart.md`（待生成）

- 开发环境设置
- 新增子命令使用示例
- 测试指南

---

## Phase 2: Implementation

### Implementation Tasks

参见 `tasks.md`（由 `/speckit.tasks` 命令生成）

**关键任务类别**:
1. CLI 架构重构（添加子命令支持）
2. service 子命令实现
3. config 子命令实现
4. 测试编写
5. 文档更新
6. install.sh 移除

---

## Gate Checklist

### Pre-Phase 0

- [x] Constitution Check 通过
- [x] Technical Context 已填充
- [x] Research.md 已生成

### Pre-Phase 1

- [x] 所有 NEEDS CLARIFICATION 已解决
- [x] Data Model 已设计
- [x] CLI Contracts 已定义
- [x] Agent Context 已更新

### Pre-Phase 2

- [x] Design 已完成
- [ ] tasks.md 已生成（通过 /speckit.tasks）
- [ ] 实现准备就绪

---

## Generated Artifacts

### Phase 0 Output

- **research.md** - 技术研究和设计决策
  - argparse 子命令最佳实践
  - systemd 服务文件规范
  - 交互式 CLI 模式
  - 配置文件默认值

### Phase 1 Output

- **data-model.md** - 数据结构和实体
  - CLI 命令结构
  - 配置文件结构
  - systemd 服务文件结构
  - 问答流程数据结构

- **contracts/service.md** - service 子命令契约
  - `service install` 命令规范
  - `service uninstall` 命令规范
  - 错误处理和输出格式

- **contracts/config.md** - config 子命令契约
  - `config init` 命令规范
  - 问答流程详细定义
  - 输入验证规则

- **quickstart.md** - 开发者快速入门
  - 开发环境设置
  - 使用示例
  - 测试指南

- **CLAUDE.md** - Agent 上下文已更新
