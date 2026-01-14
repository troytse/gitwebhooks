# Implementation Plan: config init 交互式向导

**Branch**: `001-config-init-wizard` | **Date**: 2025-01-14 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-config-init-wizard/spec.md`

## Summary

本功能为 `gitwebhooks-cli config` 命令添加 `init` 子命令，提供交互式向导帮助用户快速创建配置文件。用户可以通过回答一系列问题生成包含服务器配置、平台配置和仓库配置的完整 INI 文件。支持指定配置级别（system/local/user），并针对每个平台类型提供定制化的配置引导。

## Technical Context

**Language/Version**: Python 3.7+
**Primary Dependencies**: Python 标准库（configparser, os, sys, re, pathlib）
**Storage**: INI 配置文件（无数据库）
**Testing**: pytest（现有测试框架）
**Target Platform**: Linux 服务器环境
**Project Type**: CLI 工具（单一项目结构）
**Performance Goals**: 向导响应时间 < 100ms，配置生成 < 1s
**Constraints**: 无外部依赖，仅使用 Python 标准库
**Scale/Scope**: 单次运行生成单个配置文件，支持 4 种平台类型

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Required Compliance Gates

所有需求已通过宪章检查：

1. **Simplicity & Minimalism**: ✅ PASS
   - 使用 Python 标准库实现，无外部依赖
   - 配置保持 INI 格式，人类可读
   - 模块职责单一：向导类专注于收集配置
   - 预计代码行数 < 400 行

2. **Platform Neutrality**: ✅ PASS
   - 向导对所有平台（github/gitee/gitlab/custom）一视同仁
   - 平台识别基于配置选择，无硬编码偏好
   - custom 平台支持完全自定义参数

3. **Configuration-Driven Behavior**: ✅ PASS
   - 所有仓库特定逻辑存储在 INI 配置中
   - 向导仅生成配置，不添加仓库特定代码

4. **Security by Verification**: ✅ PASS
   - 支持所有平台的签名验证配置
   - 密钥仅存储在配置文件中
   - 配置文件权限设置为 0600（用户读写）

5. **Service Integration**: ✅ PASS
   - 生成的配置与现有 systemd 服务兼容
   - 日志路径可配置

6. **Professional Commit Standards**: ✅ PASS
   - 不涉及此检查项（计划阶段）

### Violation Justification

无违规。

## Project Structure

### Documentation (this feature)

```text
specs/001-config-init-wizard/
├── plan.md              # 本文件
├── research.md          # 技术研究文档
├── data-model.md        # 数据模型定义
├── quickstart.md        # 快速上手指南
├── contracts/           # API 合约
│   └── wizard.md        # Wizard 类接口
└── tasks.md             # 任务分解（由 /speckit.tasks 生成）
```

### Source Code (repository root)

```text
gitwebhooks/
├── cli/
│   ├── __init__.py
│   ├── service.py       # 现有：service 子命令
│   ├── config.py        # 现有：config view 子命令
│   └── init_wizard.py   # 新增：init 交互式向导
│
├── config/
│   └── ...             # 现有配置模块
│
└── ...

tests/
├── unit/
│   └── cli/
│       └── test_init_wizard.py  # 新增：向导单元测试
│
└── integration/
    └── test_config_init.sh     # 新增：集成测试脚本
```

**Structure Decision**: 单一项目结构（Option 1）
- 本功能是 CLI 工具的扩展，不涉及前后端分离
- 所有代码位于 `gitwebhooks/cli/` 目录下
- 测试遵循现有项目结构

## Complexity Tracking

无违规需要记录。

## Implementation Phases

### Phase 0: Research ✅ COMPLETE

研究 Python 标准库交互式输入方案，确定使用自建轻量级 Wizard 类。详见 [research.md](research.md)。

**关键决策**:
- 使用 `input()` 封装实现交互式输入
- 使用 `configparser.ConfigParser` 生成 INI 文件
- 使用 `os.access()` 检测权限
- 数字索引选择，逗号分隔多选

### Phase 1: Design ✅ COMPLETE

#### 数据模型设计

详见 [data-model.md](data-model.md)。

核心实体：
- `ConfigLevel`: 配置级别（system/local/user）
- `ServerConfig`: 服务器配置
- `PlatformConfig`: 平台配置
- `RepositoryConfig`: 仓库配置
- `ConfigFile`: 完整配置文件

#### API 合约设计

详见 [contracts/wizard.md](contracts/wizard.md)。

公共接口：
- `Wizard.__init__(level: Optional[str] = None)`
- `Wizard.run() -> str`
- 私有方法处理各步骤配置收集

#### 用户指南

详见 [quickstart.md](quickstart.md)。

### Phase 2: Task Decomposition

任务分解将由 `/speckit.tasks` 命令生成 `tasks.md`。

**预计任务模块**:
1. 创建 `init_wizard.py` 模块结构
2. 实现 `Wizard` 类核心框架
3. 实现配置级别选择和权限检测
4. 实现服务器配置收集
5. 实现平台选择和配置
6. 实现仓库配置收集
7. 实现 INI 文件生成
8. 实现覆盖确认逻辑
9. 实现信号处理和清理
10. 更新 CLI 入口点
11. 编写单元测试
12. 编写集成测试

## Dependencies

### Internal Dependencies

| 模块 | 用途 |
|------|------|
| `gitwebhooks.config.loader` | 配置加载（验证生成的配置） |
| `gitwebhooks.models.provider` | Provider 枚举 |
| `gitwebhooks.cli.config` | 现有 config 子命令 |

### External Dependencies

无（仅 Python 3.7+ 标准库）

## Testing Strategy

**Environment Setup**: 按照项目宪章 (Constitution) 要求，所有 Python 开发和测试必须在虚拟环境中进行：
1. 激活虚拟环境：`source venv/bin/activate`
2. 安装依赖：`pip install -e .`
3. 安装开发依赖：`pip install -e ".[dev]"`

1. **单元测试** (`tests/unit/cli/test_init_wizard.py`):
   - 测试各输入验证函数
   - 测试配置级别映射
   - 测试 INI 生成逻辑
   - Mock 用户输入

2. **集成测试** (`tests/integration/test_config_init.sh`):
   - 完整向导流程测试
   - 生成配置文件验证
   - 各平台配置测试
   - 权限错误处理测试

3. **手动测试**:
   - 各平台真实场景测试
   - 覆盖/备份功能验证

## Risks & Mitigations

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| 用户输入不可预测 | 向导崩溃 | 严格验证 + 友好错误提示 |
| 权限问题复杂 | 用户体验差 | 提前检测 + 清晰建议 |
| INI 格式兼容性 | 配置无法加载 | 使用 configparser 生成 |
| 中断状态残留 | 文件系统混乱 | try-finally 清理 |

## Success Criteria

| 标准 | 目标 |
|------|------|
| 新用户完成时间 | < 3 分钟 |
| 首次配置成功率 | > 90% |
| 配置文件准确率 | 100% |
| 无效输入识别率 | 100% |
| 代码行数 | < 400 行 |

## Next Steps

执行 `/speckit.tasks` 生成详细任务分解。
