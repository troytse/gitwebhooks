# Research: 配置文件查看命令

**Feature**: 001-config-view
**Date**: 2026-01-14

## Overview

本文档记录 `config view` 命令的技术研究和设计决策。

## Configuration File Path Resolution

### Decision: 使用标准优先级顺序查找配置文件

配置文件按以下优先级顺序查找（第一个存在的文件将被使用）：
1. `~/.gitwebhooks.ini` - 用户主目录配置
2. `/usr/local/etc/gitwebhooks.ini` - 系统本地配置
3. `/etc/gitwebhooks.ini` - 系统全局配置

**Rationale**:
- 遵循 Unix/Linux 配置文件约定（用户配置优先于系统配置）
- 与现有代码中隐含的查找逻辑保持一致
- 用户可以在不同级别覆盖配置，提供灵活性

**Alternatives considered**:
- 仅支持单一配置文件路径：不够灵活，用户无法在不同环境中使用不同配置
- 环境变量指定：增加了配置复杂度，不符合项目简单性原则

## Output Format

### Decision: 使用纯文本格式，按节分组显示配置

配置内容以易读的纯文本格式输出，不提供 JSON 等其他格式选项。

**Rationale**:
- INI 配置文件本身就是人类可读的纯文本格式
- 符合项目"简单性"原则，避免引入额外的格式化逻辑
- 用户可以直接使用 `cat` 或文本编辑器查看配置

**Alternatives considered**:
- JSON 输出：需要额外序列化逻辑，且 INI → JSON 转换可能丢失语义
- YAML 输出：引入外部依赖（PyYAML），违反宪法要求

## Sensitive Field Highlighting

### Decision: 使用 ANSI 颜色代码高亮敏感字段

敏感字段（包含 `secret`、`password`、`token`、`key`、`passphrase` 关键词）使用 ANSI 颜色代码高亮显示，但不隐藏实际值。

**Rationale**:
- ANSI 颜色代码是终端标准，无需外部依赖
- 用户已确认希望看到完整值（仅高亮标记）
- 有助于用户识别敏感信息，谨慎处理

**Alternatives considered**:
- 隐藏敏感值：用户明确不希望隐藏
- 使用特殊符号标记：ANSI 颜色在终端中更直观

## Configuration Source Display

### Decision: 在输出顶部单独一行显示配置来源

格式：`Config File: <path> (source: user-specified/auto-detected)`

**Rationale**:
- 清晰区分用户指定的配置文件和自动查找的配置文件
- 将元信息与内容分离，便于用户快速识别
- 符合 CLI 工具的常见输出模式

**Alternatives considered**:
- 将来源信息嵌入配置节中：不够清晰，难以快速定位
- 在输出末尾显示：用户可能需要滚动才能看到

## Error Handling

### Decision: 显示完整的解析错误信息

当配置文件格式无效时，显示完整的解析错误信息，包括错误类型、无效内容的行号和具体问题描述。

**Rationale**:
- 用户可以快速定位和修复配置错误
- configparser 本身提供详细的错误信息
- 不涉及敏感信息泄露风险（错误信息来自配置文件内容）

**Alternatives considered**:
- 仅提示"配置文件格式无效"：用户无法知道哪里出错
- 隐藏行号和内容：降低诊断效率

## ANSI Color Support

### Decision: 检测终端颜色支持，自动降级

使用环境变量 `NO_COLOR` 或检测终端类型来决定是否启用颜色高亮。如果终端不支持颜色或 `NO_COLOR` 环境变量已设置，则不使用颜色。

**Rationale**:
- 遵循 [no-color.org](https://no-color.org/) 标准
- 兼容不支持 ANSI 颜色的终端
- 不影响输出内容的可读性

**Alternatives considered**:
- 强制启用颜色：在某些终端中会产生乱码
- 完全不支持颜色：失去高亮敏感字段的功能

## Code Structure

### Decision: 在 gitwebhooks/cli/config.py 中添加 cmd_view() 函数

扩展现有的配置 CLI 模块，添加 `cmd_view()` 函数实现 `config view` 子命令。

**Rationale**:
- 现有 `config.py` 已经包含 `cmd_init()` 函数
- 保持配置相关 CLI 命令在同一模块
- 符合单一职责原则

**Alternatives considered**:
- 创建新的 view.py 模块：增加不必要的模块数量
- 将功能放在 server.py 中：违反职责分离原则

## Implementation Phases

1. **Phase 1**: 实现基本的配置文件显示功能
   - 配置文件路径查找逻辑
   - 读取和解析配置文件
   - 基础输出格式

2. **Phase 2**: 添加敏感字段高亮
   - 敏感关键词检测
   - ANSI 颜色代码应用
   - 终端颜色支持检测

3. **Phase 3**: 完善错误处理
   - 详细的错误信息
   - 边缘情况处理（空文件、权限问题、符号链接等）

4. **Phase 4**: 测试和文档
   - 单元测试
   - 集成测试
   - 更新 README
