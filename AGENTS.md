# AGENTS.md — gitwebhooks

> 轻量级 Git Webhook 服务器：接收 GitHub / Gitee / GitLab / 自定义平台的 webhook，按 INI 配置执行仓库部署命令。纯 Python 3 标准库实现，无外部运行时依赖。
>
> **⚠️ 最高编码准则见 [`CONSTITUTION.md`](./CONSTITUTION.md)（项目编码宪章）——所有 MUST 条款、合规分级与审查口径以宪章为准，冲突时宪章优先**。本文档为入口摘录，不重复宪章长文。

## 项目概述

| 项 | 值 |
|----|----|
| 语言 | Python（`requires-python = ">=3.7"`，classifiers 覆盖 3.7–3.14） |
| 运行时依赖 | **无**（仅标准库；`pyproject.toml` 的 `dependencies = []` 是硬约定） |
| 开发依赖 | `pytest`、`pytest-cov`（dev extra；**全量测试套件的运行器**） |
| 代码规模 | 4.6k 行（`gitwebhooks/`，4570 行） |
| 配置格式 | INI（`configparser`） |
| HTTP | 标准库 `http.server` |
| 打包 | `setuptools`，可发布 PyPI，亦支持原地从源码运行 |
| 当前版本 | `2.4.1`（`pyproject.toml` 与 `gitwebhooks/__init__.py` **两处**） |

**支持平台**：GitHub（HMAC-SHA1 签名）、Gitee（签名或密码）、GitLab（token）、custom（自定义 Header + JSON 路径识别）。

## 宪章与文档层级

**最高编码准则：[`CONSTITUTION.md`](./CONSTITUTION.md)** —— 所有贡献者与 AI 代理必须遵守其 MUST 条款；本文档与 `README*.md`、`.dsh/skills/` 不得弱化宪章要求，**冲突时以宪章为准**。

| 优先级 | 文件 | 职责 |
|--------|------|------|
| 1 | `CONSTITUTION.md` | 编码宪章（MUST 条款、架构不变量、合规分级 A/B/C、审查矩阵） |
| 2 | `AGENTS.md`（本文档） | Agent 入口：架构、命令、约束摘录 |
| 3 | `README.md` / `README.zh.md` | 用户手册（安装、配置、使用；两语言须同步） |
| 4 | `.dsh/skills/*` | 操作技能（`code-review` 代码审查口径） |

## 架构

依赖方向单向（上层依赖下层）：

```
main/  cli/        入口：参数解析、子命令分发、交互式向导
   ↓
server.py          HTTP 服务器、请求生命周期编排
   ↓
handlers/          平台事件识别 → 仓库分发 → 调用部署命令
auth/              各平台签名 / token 校验（工厂 + 每平台一文件）
   ↓
config/            INI 加载、注册表、配置数据模型
models/            与框架无关的数据类与枚举（Provider / WebhookRequest / 验证结果）
utils/             常量、异常、命令执行、systemd 辅助
```

**请求处理流程**：`do_POST()` → `_parse_provider()`（按 Header 识别平台）→ `_parse_data()`（JSON / form-urlencoded）→ 平台处理器验证签名 / token → 提取仓库标识 → 查配置 → 异步执行配置的命令。

**平台差异**（识别 Header / 仓库标识 / 验证方式）：

| 平台 | 事件 Header | 仓库标识 | 验证 |
|------|-------------|----------|------|
| GitHub | `X-GitHub-Event` | `repository.full_name` | `X-Hub-Signature`（HMAC-SHA1） |
| Gitee | `X-Gitee-Event` | `repository.full_name` | 签名或密码 |
| GitLab | `X-Gitlab-Event` | `project.path_with_namespace` | `X-Gitlab-Token` |
| custom | 配置的 `header_event` | 配置的 `identifier_path` | 配置的 `header_token` |

## 文件结构

```
gitwebhooks-cli              # Bash 包装脚本：自动定位包并以 python3 -m gitwebhooks.main 运行
pyproject.toml               # 打包、版本号（源 1）、入口点 gitwebhooks.main:main
MANIFEST.in                  # sdist 清单
CHANGELOG.md                 # 更新日志（Keep a Changelog；发布时必须更新）
gitwebhooks.ini.sample       # 配置模板（改配置项须同步）
scripts/pre-release-check.sh # 发布前校验（构建 + 隔离环境安装 + CLI 冒烟）
gitwebhooks/
├── __init__.py              # 包入口、__version__（源 2）、导出 WebhookServer / Provider / WebhookRequest
├── server.py                # WebhookServer 与请求处理器：编排与派发
├── main/
│   ├── __init__.py          # create_parser / find_config_file / main（CLI 主函数）
│   ├── __main__.py          # python3 -m gitwebhooks.main 入口
│   └── version.py           # 版本输出
├── cli/
│   ├── __init__.py          # 子命令注册（serve / config / help）
│   ├── serve.py             # cmd_serve：启动服务器 / systemd 安装卸载分发
│   ├── service.py           # systemd 安装卸载实现（被 serve.py 调用，非子命令）
│   ├── config.py            # cmd_init / cmd_view
│   ├── init_wizard.py       # 交互式配置向导（⚠️ 785 行，见宪章 §1.2）
│   ├── prompts.py           # 交互提示辅助
│   └── help.py              # help 子命令（输出由 argparse format_help 生成，与 --help 同源）
├── config/
│   ├── loader.py            # INI 加载与自动查找
│   ├── registry.py          # 配置注册表
│   ├── models.py            # 配置数据类
│   └── server.py            # 服务器 / SSL 配置
├── auth/
│   ├── verifier.py          # 验证器基类
│   ├── factory.py           # 验证器工厂
│   └── github.py gitee.py gitlab.py custom.py
├── handlers/
│   ├── base.py              # 处理器基类
│   ├── request.py           # 请求数据解析
│   ├── factory.py           # 处理器工厂
│   └── github.py gitee.py gitlab.py custom.py
├── models/
│   ├── provider.py          # Provider 枚举（Github / Gitee / Gitlab / Custom）
│   ├── request.py           # WebhookRequest 数据类
│   ├── result.py            # 验证结果
│   └── config.py            # 配置模型
├── utils/
│   ├── constants.py         # HTTP 常量、Header 名、路径、RESERVED_SECTIONS、SENSITIVE_KEYWORDS
│   ├── exceptions.py        # 自定义异常（含 ConfigurationError）
│   ├── executor.py          # execute_deployment（异步 subprocess；守护线程排空输出 + wait 回收）
│   └── systemd.py           # systemd 检测与服务文件生成
└── logging/setup.py         # 日志配置
tests/
├── __main__.py              # 项目自带 runner：python3 -m tests
├── conftest.py              # 共享夹具（临时目录、空闲端口、服务器管理等）
├── unit/                    # 单元测试（unit/cli/ 为 CLI 子命令测试）
├── integration/             # 端到端 webhook / 配置发现 / 命令执行
├── fixtures/                # 各平台 payload 与签名构造器
└── utils/                   # 测试辅助（HTTP 客户端、线程内测试服务器）
doc/                         # README 截图（二进制资源）
.dsh/skills/                 # DSH 项目技能（项目唯一技能来源）
```

## 配置结构

INI 格式（`configparser`），保留节名以 `utils/constants.py` 的 `RESERVED_SECTIONS` 为准：

| 节 | 内容 |
|----|------|
| `[server]` | `address`、`port`、`log_file` |
| `[ssl]` | `enable`、`key_file`、`cert_file` |
| `[github]` / `[gitee]` / `[gitlab]` | `handle_events`、`verify`、`secret` |
| `[custom]` | `header_name`、`header_value`、`header_token`、`header_event`、`identifier_path`、`handle_events`、`verify`、`secret` |
| `[owner/repo]` | **仓库节**：`cwd`（工作目录）、`cmd`（收到 webhook 时执行的 shell 命令） |

- 仓库节名必须为 `owner/repo`；`identifier_path` 是 JSON 路径（如 `project.path_with_namespace`），用点号分隔。
- 改配置项**必须**同步 `gitwebhooks.ini.sample`、`RESERVED_SECTIONS` 与两个 README。

**默认部署路径**：配置 `/usr/local/etc/gitwebhooks.ini`、日志 `/var/log/gitwebhooks.log`、CLI `/usr/local/bin/gitwebhooks-cli`、systemd 单元 `/usr/lib/systemd/system/gitwebhooks.service`。

## 常用命令

### 运行服务

```bash
# 从源码运行（开发模式，推荐）
./gitwebhooks-cli serve -c gitwebhooks.ini.sample

# 模块方式（等价）
python3 -m gitwebhooks.main serve -c gitwebhooks.ini.sample

# 不指定 -c：按优先级自动查找配置并打印所用路径
./gitwebhooks-cli serve
```

> ⚠️ 启动服务器**必须**带 `serve` 子命令。`./gitwebhooks-cli -c file.ini`（无子命令）只会打印帮助并返回 0，不会启动服务。

**配置文件查找优先级**（唯一出处 `utils/constants.py` 的 `CONFIG_SEARCH_PATHS`）：

1. `~/.gitwebhooks.ini`（用户级，最高）
2. `/usr/local/etc/gitwebhooks.ini`（本地级）
3. `/etc/gitwebhooks.ini`（系统级）

### 子命令

```bash
./gitwebhooks-cli --help              # 总览帮助（亦可 -h；每层级均支持）
./gitwebhooks-cli help                # 等价形式：help 子命令
./gitwebhooks-cli help serve          # 指定子命令帮助（serve / config）
./gitwebhooks-cli serve --help        # 同上，标准 flag 形式（两者输出完全一致）
./gitwebhooks-cli --version           # 版本（亦可 -v）

# 配置：交互式向导（可指定级别 system/local/user）
./gitwebhooks-cli config init
sudo ./gitwebhooks-cli config init system
./gitwebhooks-cli config view         # 查看配置，敏感字段高亮
./gitwebhooks-cli config view -c /path/to/config.ini

# systemd 服务（注意：是 serve 的子动作，不是独立的 service 子命令）
sudo ./gitwebhooks-cli serve install [--force] [--dry-run] [--verbose] [--config-level user|local|system]
./gitwebhooks-cli serve install --config-level user
sudo ./gitwebhooks-cli serve uninstall [--purge]

# systemd 运行时
systemctl {start,stop,restart,status} gitwebhooks
```

> ⚠️ 独立的 `service` 子命令**已被移除**（见 git log `refactor: 彻底移除 service 命令`），改为 `serve install` / `serve uninstall`。文档或脚本中出现 `gitwebhooks-cli service ...` 即为过时引用。

### 安装与发布

```bash
pip install .                          # 安装（无外部依赖）
pip install -e ".[dev]"                # 开发安装（含 pytest）

./scripts/pre-release-check.sh         # 发布前必须通过：构建 + 隔离 venv 安装 + CLI 冒烟
python3 -m build && python3 -m twine upload dist/*
```

## 测试与质量门禁

**全量测试（权威，必须用这个）** — 先装 dev extra：

```bash
pip install -e ".[dev]"     # 含 pytest
python3 -m pytest tests/    # 228 个测试全跑，约 10 秒
```

**零依赖子集 runner**（`unittest`，**不是**全量）：

```bash
python3 -m tests            # 只跑到不依赖 pytest 的模块（当前 128 个）
python3 -m tests -q         # 仅摘要
python3 -m tests -f         # 失败即停
python3 -m tests -v         # 详细
```

> ⚠️ `python3 -m tests` 跑不到 `tests/unit/test_main.py` 等 7 个 pytest 风格模块
> （当前约 100 个测试），因此**不能**用它声称「测试全通过」。

**语法静态校验**：

```bash
python3 -m compileall -q gitwebhooks
```

### 门禁纪律

- 交付前跑 `python3 -m compileall -q gitwebhooks` + **全量** `python3 -m pytest tests/`；
- **如实区分**「本机真跑过 / 只做了静态检查 / 未执行」；声称通过时给出**实际计数**（跑了多少 / 失败 / 跳过）；
- **禁止吞输出**（`>/dev/null`、`2>/dev/null`、`-q` 用于可能失败的命令）；
- CLI 子命令增删时，**必须**核对全部引用点：`cli/__init__.py` 注册、`cli/help.py`、`README.md`、`README.zh.md`、`scripts/pre-release-check.sh`、相关测试。

### 测试基线

**`python3 -m pytest tests/`（Python 3.14）**：`228 passed`，约 10 秒，**0 挂起**。

**`python3 -m tests`（无 pytest）**：`Ran 128 tests`，5 个 error（pytest 风格模块无法导入）。这些 error 是**子集 runner 的已知限制**，不是代码缺陷。

判定改动是否引入回归时，必须以**全量 pytest 结果**为准。

## 代码审查

代码 / 文档改动交付前，加载 **`.dsh/skills/code-review/SKILL.md`** 执行审查：按宪章输出 `P0–P3 × file:line × 依据条款 × 证据` 的结构化发现清单。

- 审查**只报不改**；发现自己问题的「顺手修一下」不属于审查结论。
- 涉及**必须运行才能确认**的项（如某失败是否被修复、某分支是否真的到达），标注「需主代理跑门禁确认」，**禁止**把推测写成已验证。
- 合规分级与审查矩阵见宪章 §10.2 / §10.3。

## Git 纪律

- 提交格式 `<类型>: <简短描述>`（feat / fix / docs / refactor / test / chore），**使用中文**；
- **禁止** AI 归属签名（`🤖 Generated with ...`）、`Co-Authored-By:` 形式的 AI 署名、emoji；
- 一次提交只含一项已完成工作，禁止夹带无关文件；未过门禁不得提交；
- 未经用户明确授权，**不得** `git commit` / `git push` / 改写历史。

## 开发原则

1. **文档优先**：改前先 `read` / `grep` 验证 API 与现有模式，不假设文件或函数存在；
2. **禁止反复猜测试错**：遇报错先查权威来源（Python 官方文档、`README*.md`、本宪章）确认根因，再最小复现验证；
3. **最小改动**：只改任务相关代码，拒绝过度抽象（YAGNI / KISS）；
4. **匹配现有风格**：命名、目录、抽象层级与周边代码一致；注释 / docstring 语言**按层就近一致**（核心模块英文、CLI 交互层中文，见宪章 §2.1），代码标识符一律英文，commit 用**中文**；
5. **同步文档**：用户可见行为变更 → 两个 README **+ `CHANGELOG.md` 的「未发布」小节**；架构 / 命令变更 → 本文档；命令或配置项增删 → 核对 §「门禁纪律」的引用点清单；
6. **零依赖**：不引入运行时第三方依赖（`dependencies` 保持为空）；
7. **版本双源**：改版本号必须同时改 `pyproject.toml` 与 `gitwebhooks/__init__.py`，提交前 `grep` 复核。

## 常见陷阱

| 问题 | 说明 |
|------|------|
| **`serve` vs `service`** | 独立 `service` 子命令已移除；systemd 管理是 `serve install` / `serve uninstall`。`cli/service.py` 是内部实现模块，不是子命令。 |
| **版本双源** | `pyproject.toml` 与 `gitwebhooks/__init__.py` 各存一份版本号，无自动同步；`main/version.py` 从包 `__version__` 读取。 |
| **两处平台注册** | 新增平台须同时改 `handlers/factory.py` 与 `auth/factory.py`，并加 `handlers/<p>.py` 与 `auth/<p>.py`；漏一处会「识别了平台但无法验证」。 |
| **测试挂起（P0）** | 历史上两处：① `sys.exit` 被 mock 成 no-op ⇒ `while True` 无限重试；② patch 了 `gitwebhooks.main.WebhookServer`，但 `cmd_serve` 用的是 `gitwebhooks.cli.serve.WebhookServer` ⇒ **真实启动服务器**。测试若卡住，先查这两类。 |
| **测试因「恰好成立」而通过** | 例：用 `main([])` 断言返回码，实际走的是「打印帮助」分支；`-m gitwebhooks.cli` 恒返回 1（模块不存在），却让「配置缺失返回 1」的断言通过。断言必须对应被测行为。 |
| **配置常量分散风险** | 路径列表、Header 名、状态码、敏感字段关键词的唯一出处是 `utils/constants.py`；别处硬编码即漂移。 |
| **命令执行信任边界** | `execute_deployment` 使用 `shell=True`。安全前提是「命令只来自本地配置文件」——**禁止**把请求体内容拼进命令。 |
| **禁止创建无人读取的管道** | `stdout=PIPE` 而不读 ⇒ 输出超过管道缓冲区（Linux 64 KiB）后命令**永久阻塞**（「推送后没反应、无报错、无日志尾」）。当前实现用守护线程合并排空 `stdout`/`stderr` 并 `wait()` 回收；改动此处**必须**保持「有消费者 + 有回收」，回归测试见 `tests/unit/test_executor.py`。 |
| **CLI 文档漂移** | README 两个语言版本与 `scripts/pre-release-check.sh` 曾残留已删除的 `service` 引用；增删子命令时按引用点清单全查。 |
| **模块入口是 `gitwebhooks.main`** | `gitwebhooks.cli` 是子命令包，**没有** `__main__.py`，`python3 -m gitwebhooks.cli` 会失败；模块方式启动一律用 `python3 -m gitwebhooks.main`。 |
| **帮助只有一个来源** | 帮助文本由 argparse 从解析器定义生成：`help.py` 不再持有手写文案。改选项后 `help <cmd>` 与 `<cmd> --help` 自动同步，不要另写一份帮助字符串。 |
| **启动服务器必须带 `serve`** | `./gitwebhooks-cli -c file.ini`（无子命令）只打印帮助并返回 0，**不会**启动服务；正确写法是 `./gitwebhooks-cli serve -c file.ini`。文档一律以此为准。 |

## 受控文档索引

| 文档 | 内容 |
|------|------|
| [`CONSTITUTION.md`](./CONSTITUTION.md) | **编码宪章（最高准则）**：适用范围、架构不变量、安全、测试、合规分级、审查矩阵 |
| [`CHANGELOG.md`](./CHANGELOG.md) | **更新日志**（Keep a Changelog）：各版本的用户可感知变更；发布时必须更新 |
| [`AGENTS.md`](./AGENTS.md)（本文档） | Agent 入口：架构、命令、门禁、陷阱 |
| [`README.md`](./README.md) | 用户手册（英文）：安装、配置、使用、发布 |
| [`README.zh.md`](./README.zh.md) | 用户手册（中文） |
| [`gitwebhooks.ini.sample`](./gitwebhooks.ini.sample) | 配置模板 |
| [`.dsh/skills/code-review/SKILL.md`](./.dsh/skills/code-review/SKILL.md) | 代码审查口径与清单 |
