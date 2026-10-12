---
name: code-review
description: gitwebhooks 代码审查 — 按项目宪章输出 P0-P3 结构化发现清单（含双语文档一致性、CLI 引用点、版本双源核对）。代码或文档改动交付前、全仓违规 sweep 时使用。
---

# gitwebhooks 代码审查（Code Review）

> 本技能是**代码审查（含文档一致性）的唯一口径与清单**。
> 执行者有两种：**主代理**（自己审、且能跑门禁）与**被派发的只读审查任务**（无写权限、不跑门禁）。
> 两者依据同一套清单；只读侧凡「必须运行才能确认」的项，一律标注「**需主代理跑门禁确认**」。

## 0. 与宪章的关系

- 判定依据以 [`CONSTITUTION.md`](../../../CONSTITUTION.md) 为准；[`AGENTS.md`](../../../AGENTS.md) 是入口摘录。
- **排除范围不判违规**：Python 标准库、第三方依赖及其安装产物、构建与缓存产物（`dist/`、`build/`、`*.egg-info/`、`__pycache__/`、`.pytest_cache/`、`.venv/`、`venv/`）、二进制截图（`doc/*.png`）。见宪章 §0.2。
- **不做门禁替代**：审查是静态判断，不等于「跑过了」。

## 1. 确定范围

```bash
# 默认：工作区全部改动（含未提交与已暂存）
git diff --stat
git diff
git diff --cached

# 或相对 master 的 branch diff
git diff master...HEAD --stat
git diff master...HEAD
```

- **禁止**只用 `git diff HEAD~1..HEAD`（漏掉未提交改动）。
- 用户指定文件时**只审指定路径**。
- 范围默认 = **本次改动文件及其直接约束条款**；全仓 sweep 是**单独派发**的任务，不在每次交付里做。

## 2. 加载上下文（按 diff 选择性 read）

| 文件 | 何时读 |
|------|--------|
| `CONSTITUTION.md` | **始终**（A 组判定依据） |
| `AGENTS.md` | **始终**（命令入口、门禁、已知基线） |
| `README.md` **和** `README.zh.md` | 改动涉及 CLI 命令 / 配置项 / 用户可见行为时 |
| `gitwebhooks.ini.sample` | 改动涉及配置项、`RESERVED_SECTIONS`、`config` 子命令时 |
| `scripts/pre-release-check.sh` | 改动涉及 CLI 入口 / 子命令 / 打包 / 版本时 |
| `gitwebhooks/utils/constants.py` | 改动涉及 Header、状态码、路径、敏感字段时 |

> 大文件纪律：`gitwebhooks/cli/init_wizard.py`（779 行）用 `grep` + 带 `offset`/`limit` 的 read 定位后再读，不要整文件读入下结论。

## 3. 审查清单（每项结论必须带 `file:line`）

### A. 宪章 / 架构不变量（宪章 §3.1、§3.3）

- [ ] **零运行时依赖**：`pyproject.toml` 的 `[project].dependencies` 仍为 `[]`；无新增 `import` 第三方运行时库（`pytest` 只能出现在测试文件）。
- [ ] **配置驱动**：无仓库名 / 仓库专属分支 / 部署命令被硬编码进 Python（必须全部来自 INI `[owner/repo]` 节）。
- [ ] **平台中立**：平台识别只依据 Header；除已文档化的 Header / 事件名差异外无平台特权分支；新增平台**同时**改了 `handlers/factory.py` 与 `auth/factory.py`，并新增两个平台文件。
- [ ] **常量集中**：HTTP 状态码、Header 名、消息文案、敏感字段关键词、配置路径均来自 `utils/constants.py`，无散落字面量（宪章 §1.2）。
- [ ] **请求解析兼容**：JSON 与 `application/x-www-form-urlencoded` 两条路径都仍被支持。
- [ ] **配置查找顺序**：`~/.gitwebhooks.ini` > `/usr/local/etc/gitwebhooks.ini` > `/etc/gitwebhooks.ini`，且只在 `CONFIG_SEARCH_PATHS` 定义。
- [ ] **版本双源同步**：`pyproject.toml` 的 `version` 与 `gitwebhooks/__init__.py` 的 `__version__` 一致（改一处未改另一处 = P1）。
- [ ] **命令执行不阻塞**：`execute_deployment` 仍为异步 `Popen`；`stdin=subprocess.DEVNULL`；stdout/stderr 的管道**必须有消费者持续排空**（当前为守护线程），且子进程**必须** `wait()` 回收——否则输出超过管道缓冲区（Linux 64 KiB）会永久卡死，且读端永不释放（宪章 §3.3；回归测试 `tests/unit/test_executor.py` 与 `tests/integration/test_command_execution.py`）。
- [ ] **CLI 约定**（宪章 §3.3）：`-h`/`--help` 在**每个层级**可用、输出到 **stdout**、退出码 **0**；`-v`/`--version` 主层可用；`help <cmd>` 与 `<cmd> --help` 输出**完全一致**；**没有**第二份手写帮助字符串（帮助由 argparse 从解析器定义生成）；用法错误走 stderr + 非 0 退出码。

### B. 分层与职责（宪章 §1.1）

- [ ] `server.py` 只做编排（识别 → 验证 → 查表 → 派发），平台专属逻辑在 `handlers/<platform>.py`。
- [ ] 依赖方向单向，`models/`、`config/`、`auth/`、`handlers/` 之间无循环导入。
- [ ] 交互式逻辑留在 `cli/`，未被业务层调用；`cli/service.py` 是内部模块而非子命令。
- [ ] 单文件未超过 400 行；**未扩大**宪章 §1.2 已标注的存量偏差（`init_wizard.py` 779 / `service.py` 352 / `prompts.py` 322）。
- [ ] 圈复杂度 ≤ 10、嵌套 ≤ 3、方法 ≤ 80 行、参数 ≤ 5 个。
- [ ] 私有方法用**单下划线**前缀（非双下划线，dunder 除外）；公有 API 无下划线。

### C. 零死代码与调试输出（宪章 §3.2）

- [ ] 无未被调用的函数 / 方法 / 类 / 常量、无未使用 import、无已废弃配置项。
- [ ] 生产路径无调试输出（`print()` 调试、`breakpoint()`、`pdb`）；日志走 `logging` 且级别恰当。
- [ ] **子命令移除已全查引用点**（最容易漏的一类）：`cli/__init__.py` 注册、`cli/help.py` 文案、`README.md`、`README.zh.md`、`scripts/pre-release-check.sh`、相关测试。任一处残留 = A 级。

### D. 错误处理与安全（宪章 §4、§5）

- [ ] 缺失的必需配置项在**启动时**报错退出；找不到配置文件时报错**含已尝试路径**，不静默用默认值。
- [ ] 外部输入（请求体、Header、配置值）在使⽤前经显式校验；JSON 路径不存在时明确失败而非未捕获异常。
- [ ] 密钥 / token **未**硬编码进源码、测试或文档示例；配置示例值为空或占位。
- [ ] secret / token 原文**未**写入日志或错误输出；敏感字段判定走 `SENSITIVE_KEYWORDS`。
- [ ] 生成的配置文件权限为 **0600**。
- [ ] `shell=True` 的命令来源仅限本地配置文件，且代码中写明该信任边界；**请求体内容未被拼入命令**（命令注入）。
- [ ] 命令执行失败仅记 warning，不冒泡终止 HTTP 处理线程。
- [ ] webhook 端点拒绝不支持的方法（如 GET → 403）；`verify=False` 是显式配置选择，不是代码跳过校验。
- [ ] SSL 证书 / 私钥路径在启动前校验。

### E. 测试覆盖设计（读测试代码，不执行）（宪章 §6）

- [ ] Bug 修复是否附**能复现该 bug 的测试**（先 Red 后 Green）？
- [ ] 新增 / 改动行为是否覆盖成功路径 **和** 失败路径（签名验证失败、仓库不存在、缺失配置）？
- [ ] 平台逻辑改动是否覆盖该平台的签名验证与仓库识别（两个方向）？
- [ ] 测试是否**未新增 `pytest` 依赖**（新测试用 `unittest.TestCase`；这是宪章 §6.1 的硬约定）？
- [ ] 测试是否不依赖外部网络、真实 Git 平台或固定端口（用 `tests/conftest.py` 的 `get_free_port()` 等夹具）？
- [ ] **不执行**任何测试；覆盖只能读代码判定。运行性结论一律标注「需主代理跑门禁确认」。

### F. 文档一致性

- [ ] `README.md` 与 `README.zh.md` 是否**同步**改动？只改一边 = P2。
- [ ] README 中的命令示例引用的子命令**真实存在**（尤其 `serve` vs 已删除的 `service`）？
- [ ] README 配置示例与 `gitwebhooks.ini.sample` 一致？
- [ ] 配置项增删是否同步了 `gitwebhooks.ini.sample`、`RESERVED_SECTIONS`、两个 README？
- [ ] `AGENTS.md` 的文件结构 / 命令 / 已知基线是否因本次改动而过时？
- [ ] **`CHANGELOG.md`**：用户可感知的变更是否写进「未发布 / Unreleased」小节？发布时是否已移入新版本小节并填上日期？条目是否描述**用户可感知**的变更（而非轮次日志、过程叙述、门禁回执）？
- [ ] 相对链接与 `§N` 交叉引用是否仍然有效（本技能、宪章、AGENTS.md 之间）？

### G. 治理文档「误导条款」核对

> 判据：**看它引用的实体是否还存在**，不看文字里有没有「废弃 / 遗留」字样。

- [ ] `CONSTITUTION.md` / `AGENTS.md` / 本技能引用的**文件路径、子命令、模块名、配置键**是否都还存在？
- [ ] 是否有只写否定句（「不得…」）却缺「谁负责 / 在哪做」肯定句的条款？
- [ ] 变更后是否需同步宪章 §1.2 的「已知存量偏差」或 §6.1 的 pytest 偏差清单（例如已修好却仍列为偏差，或新偏差未登记）？

### H. Agent 纪律（宪章 §9）

- [ ] 无未授权的 `git commit` / `push` / 历史改写。
- [ ] 提交信息为 `<类型>: <中文描述>`，**无** AI 归属签名、`Co-Authored-By:` 署名或 emoji。
- [ ] 无无关 drive-by 重构、无超范围改动、无一次提交夹带多项工作。
- [ ] 无「顺手修一下」式夹带——审查发现只回报，由主代理决定并转实现者。

## 4. 严重级别与合规分级

每条发现给 **P0–P3**，并映射到宪章的 A/B/C（§10.2）：

| 级别 | 含义 | 宪章分级 | 处理 |
|------|------|----------|------|
| **P0** | 安全漏洞、凭据泄露、数据 / 部署破坏、命令注入 | A | 阻塞交付，修复后**重跑门禁** |
| **P1** | 违反 MUST 条款（架构不变量、零依赖、版本双源不一致、死代码、CLI 引用点残留） | A | 阻塞交付，修复后**重跑门禁** |
| **P2** | 违反 SHOULD，或双语文档只改一边、文档示例过时 | B | 本轮修复或登记 backlog |
| **P3** | 存量偏差、不影响本次改动的风格问题 | C | 登记跟踪，不阻塞 |

- 存量偏差不因一次无关改动而阻塞；但**扩大**既有偏差 = P1。
- 同一改动对 P2 / P3 **只报一次**，登记后放行；P0 / P1 修复后**重跑门禁**，不是重跑同一审查实例。

## 5. 回报格式

```markdown
## 审查范围
<git diff 范围 / 指定路径；依据文件清单>

## 发现清单
### P1
1. [P1] `gitwebhooks/cli/__init__.py:42` — 依据宪章 §3.2 — `service` 子命令已移除但 `help.py` 仍列出该入口；证据：<复现/引用>
### P2
...
### P3
...

## 未覆盖项
- <本轮未能检查的范围，必须列出，不得默认无问题>
- 需主代理跑门禁确认：<...>

## 状态
DONE | WAITING
```

**硬要求**：

- 每条必须有 `P级别 × file:line × 依据条款 × 证据`；**禁止**编造路径、行号、条款号或工具返回值。
- 未读过的文件不得声称已审；行号对不上时如实说明。
- 「未覆盖项」**必须**给出，宁可报「未覆盖」也不臆测。
- 只读侧**不写任何文件**（含日志、临时文件）；发现只回报。

## 6. 分工与边界

| 角色 | 能力 | 结论边界 |
|------|------|----------|
| 主代理 | 可读可写、能跑门禁 | 负责编码与文档产出；执行 `python3 -m tests`、`compileall`、`pre-release-check.sh` |
| 只读审查任务 | 只读（无 `edit`/`write`） | 只给发现清单；凡「必须运行才能确认」标「需主代理跑门禁确认」 |

- 审查者**不审自己的产出**，不做「审查 → 修复 → 再审」的无限循环。
- 审查者**不提「顺手修一下」**；修复由主代理决定并执行。
- 若被派发的任务超出 prompt 所述范围（例如「顺便把文档也改好」）→ 立即回报 `TASK_MISUNDERSTOOD` 并停止。

## 7. 快速核对速查（本次改动的最小自检）

```bash
git diff --stat                        # 范围
grep -n "dependencies" pyproject.toml  # 零依赖（须为 dependencies = []）
grep -rn "__version__" gitwebhooks/__init__.py pyproject.toml   # 版本双源
grep -rn "^import pytest" tests/       # 不得新增 pytest 依赖（宪章 §6.1）
# 过时子命令引用（精确匹配真实调用，避免命中 AGENTS.md/本技能的说明文字）
grep -rnE "gitwebhooks-cli service (install|uninstall)" \
     README.md README.zh.md scripts/ gitwebhooks/ AGENTS.md CONSTITUTION.md
python3 -m compileall -q gitwebhooks   # 语法（主代理跑）
python3 -m tests -q                    # 回归（主代理跑；与 AGENTS.md 基线对比）
```

> 最后两条属**门禁**，只读审查侧不得执行，也不得据此下结论。
