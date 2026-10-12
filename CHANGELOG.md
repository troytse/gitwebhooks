# 更新日志 (Changelog)

本文件记录本项目所有值得注意的变更。

格式参考 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，
版本号遵循 [语义化版本 (Semantic Versioning)](https://semver.org/lang/zh-CN/)。

变更类型：`Added / 新增`、`Changed / 变更`、`Deprecated / 弃用`、`Removed / 移除`、
`Fixed / 修复`、`Security / 安全`。

> **关于历史条目**：本文件自 v2.4.1 起正式维护。v2.4.1 之前没有 git tag，
> 早期条目由提交历史整理而成，日期取该版本最后一次提交的日期；
> 版本切分以历史上的 `chore: 发布版本 X` 提交为准，可能与当时 PyPI 上的上传时点存在偏差。

---

## [未发布 / Unreleased]

<!-- 发布新版本时：把本节的条目移动到新的版本号小节，并更新下方链接。 -->

### Fixed / 修复

- **测试套件会永久挂起**（全量 `pytest` 跑不完——是「卡死」不是「慢」）。两处根因：
  ① `test_ask_config_level_keyboard_interrupt_confirms` 把 `sys.exit` mock 成 no-op，
  导致 `while True` 无限重试；② `test_main_*` 把 `gitwebhooks.main.WebhookServer` 打桩，
  但 `cmd_serve` 实际使用 `gitwebhooks.cli.serve.WebhookServer`，于是**真的启动了服务器**。
- **测试套件运行时间**约 55 秒降到约 10 秒。主因是每个集成测试都要等
  `serve_forever()` 默认 0.5 秒的 `poll_interval` 才完成 teardown；另有 17 处固定
  `time.sleep()`（合计约 12 秒）与每次服务器启动固定 0.25 秒等待。现改为条件轮询
  （`WebhookTestCase.wait_until` / `wait_for_file` / `wait_for_log_contains`）。
- 修复若干**从未真正运行过**的测试（此前因缺少 pytest 而整体无法导入）：
  - `tests/unit/test_main.py` 3 个用例断言的是重构前的 CLI（无子命令即启动服务器）；
  - `tests/unit/test_install_service_logic.py` 导入了已被删除的 `cmd_install`；
  - `tests/integration/test_config_discovery.py` 在 `cwd=tmp_path` 下未传 `PYTHONPATH`，
    且自身推算仓库根路径多了一层。
- `tests/unit/test_config_loading.py` 用 `python -m gitwebhooks.cli`（该模块不可执行）
  断言返回码 1，属于**因错误原因通过**；改用 `python -m gitwebhooks.main serve`，
  现在真正验证配置缺失 / 非法 INI 的处理。
- `tests/integration/test_edge_cases.py::test_large_command_output_handled` 名为「大输出」，
  实际把输出**重定向进文件**，从未经过管道——正是它让管道阻塞缺陷长期未被发现。
- `.gitignore` 现在覆盖 `*.env`（此前 `secret.env` 等不会被忽略）。
- `scripts/pre-release-check.sh` 不再吞掉全部输出（原先连构建与安装都 `>/dev/null 2>&1`，
  失败时没有任何线索）；现为成功静默、失败打印完整输出。
- **部署命令输出超过管道缓冲区后会永久卡死**（表现为「推送后没反应、无报错、无日志尾」）。
  `execute_deployment` 原先用 `stdout=PIPE, stderr=PIPE` 启动命令却**从不读取**这两个管道，
  且 `Popen` 对象被直接丢弃 ⇒ 进程一直留在 `subprocess._active`、**管道读端永不释放**，
  命令输出超过管道缓冲区（Linux 默认 64 KiB）后写端阻塞在 `write()`。
  `composer install`、`git reset --hard`、`npm ci`、`docker build` 等输出量足以触发。
  现由守护线程持续排空 stdout/stderr（合并读取）并在结束后 `wait()` 回收子进程。
- 部署失败（非 0 退出码）现在会记录退出码与输出尾部，此前完全无迹可查。
- 声明的最低 Python 版本修正为 **3.7**（原为 `>=3.6` 并带 3.6 分类器）。
  包在 import 阶段即依赖 `dataclasses`（Python 3.7+ 才有），此前 3.6 用户会安装成功、
  但 `import gitwebhooks` 必然失败。
- **安全：空 secret 会放行未认证请求**。`gitlab` / `gitee` / `custom` 三个验证器直接比较
  `signature == secret`，当配置里 `secret` 为空且请求未带 token 时 `'' == ''` 成立，
  于是 `verify=True` 形同虚设——而未认证的 webhook 会触发部署命令（任意 shell）。
  `github` 验证器本就有 `if not secret` 保护，现三者也补上同样的保护。
- **声明支持的 Python 3.7 / 3.8 实际无法启动 CLI**：`cli/init_wizard.py` 用了
  PEP 585 的 `tuple[bool, str]` 注解（3.9+ 才有），且没有 `from __future__ import annotations`；
  该模块在 `main → cli → cli.config → init_wizard` 链上被无条件导入，故 3.7/3.8 上
  `gitwebhooks-cli` 直接 `TypeError: 'type' object is not subscriptable`。改用 `typing.Tuple`。
- **`custom` 在 `header_token` 显式留空时静默跳过验证**：`verify_enabled` 由「Header 名是否非空」
  推导，因此 `verify=true` + `header_token=` 会让验证器无条件返回成功（违反宪章 §5.3）。
  现改为由 `config.verify` 决定：`verify=false` 才放行，`verify=true` 必须真正校验。
- `[ssl] enable` 写错（如 `maybe`）原先被静默当作「未启用 SSL」；现抛 `ConfigurationError`。
- pipx 自动探测用了过时的 venv 名 `gitwebhooks-server`（包名是 `gitwebhooks`），该分支实际不可达。
- `serve uninstall --purge` 删错文件：`cli/service.py` 写的是 `~/.gitwebhook.ini`（少一个 s），
  与真实路径 `~/.gitwebhooks.ini` 不符，导致配置文件从未被清理。
- 配置错误不再抛原生异常：`[ssl] enable=true` 但缺 `key_file`/`cert_file` 时原先冒泡
  `configparser.NoOptionError`，`[server] port` 非整数时冒泡 `ValueError`；现均转为
  带明确说明的 `ConfigurationError`。
- `gitwebhooks.ini.sample` 现在可直接运行：原先 `[ssl] enable=true` 配占位证书路径、
  且 `log_file=/var/log/...` 非 root 不可写，导致文档推荐的「从源码运行」命令必定失败。
- README 中的 `~/.gitwebhook.ini` / `~/.gitwebhook.log` 拼写错误（共 12 处，中英各 6），
  以及交互向导的默认日志路径同款拼写错误。

### Changed / 变更

- **完整测试套件改用 `python3 -m pytest tests/`**（`pytest` 本就是 `pyproject.toml` 的
  dev extra），共 228 个测试；`python3 -m tests` 明确为**零依赖子集运行器**（128 个），
  不再被当作「测试全通过」的依据。宪章 §6.1 / §7.1 同步更新。
- 去除 `gitwebhooks/cli/serve.py` 中与 `gitwebhooks/main/__init__.py` 重复的
  `find_config_file` 与 `format_config_error`（两份实现已漂移），改为复用后者。
- `execute_deployment` 现在返回排空输出的工作线程（`Optional[threading.Thread]`），
  便于调用方按需 join；原有调用方忽略返回值即可，行为不变。
- 部署输出逐行记入日志（DEBUG 级），失败时把尾部重新以 WARNING 级输出。
- **常量集中（宪章 §1.2/§1.3）**：各 handler 改为使用 `utils/constants.py` 的 Header 常量
  （原先硬编码 `'X-Hub-Signature'` 等字面量）；`config/loader.py` 的保留节名改用
  `RESERVED_SECTIONS`；`cli/service.py` 与 `cli/init_wizard.py` 的配置路径改用
  `CONFIG_PATH_USER/LOCAL/SYSTEM`，不再各自硬编码路径列表。
- 交互向导的配置级别菜单文案改用 `CONFIG_PATH_*` 常量（原先硬编码三个路径，已与常量漂移）。
- README 的测试命令改为 `python3 -m pytest tests/`（完整套件）；原先写 `python3 -m unittest discover tests/`，
  在未装 pytest 的环境下会报 5 个导入错误并退出非 0，且它并不是完整套件。
- 测试辅助类 `TestServer` / `TestConfigBuilder` / `TestWebhookClient` 加 `__test__ = False`，
  消除 pytest 的 26 条 `PytestCollectionWarning`。
- `execute_deployment` 的 `shell=True` 处补上信任边界注释（宪章 §5.2 要求）。

### Removed / 移除

- 死代码清理（宪章 §3.2「零死代码」）：
  - 10 个未使用的 import；
  - 8 个无任何引用的函数：`check_systemd`、`get_cli_path`、`confirm_overwrite`、
    `ask_question`、`validate_address`、`validate_path`、`validate_bool`、`validate_text`；
  - `tests/utils/server_manager.py` 的 `TestServerProcess` 死类（同时含未使用的
    `cli_script` 变量、指向不可执行模块的 `-m gitwebhooks.cli`，以及同款「创建未读管道」缺陷）；
  - 无引用的测试工具 `tests/utils/certificate_generator.py` 与 `tests/utils/coverage_runner.py`。
  - 6 个无引用的类方法：`VerifierFactory.get_verifier`、`HandlerFactory.from_headers`、
    `ConfigurationRegistry.get_provider_config` / `get_repository_config` / `has_repository`、
    `WebhookRequest.repo_identifier`；
  - 4 个无引用常量：`prompts.QUESTIONS`、`prompts.PLATFORM_QUESTIONS`、
    `service.E_SYSTEMD`、`service.E_EXISTS`；
  - 生产与测试中共 20 处未使用的 import（上一轮只清理了生产侧 10 处）。
  - 第二轮（独立复查发现）：`WebhookHandler.get_provider` 及 4 个平台覆写、
    `tests/conftest.py` 的 5 个未被调用的辅助函数、`_read_log_file`、
    9 个 `PayloadBuilder` 方法与 `generate_invalid_signature`、
    14 个无引用的 fixture 常量，以及由此产生的 5 处 `Provider` 孤儿 import。

## [2.4.1] - 2026-10-12

### Fixed / 修复

- **`-h` / `--help` 现在遵循标准 Unix 约定**：在主命令与每个子命令层级都可用，
  输出到 stdout，退出码为 `0`。此前它会打印 `Error: -h/--help parameters are not supported.`
  并以退出码 `1` 结束。
- 帮助文本改为**由 argparse 从解析器定义生成**，`help <命令>` 与 `<命令> --help`
  输出完全一致；删除 `cli/help.py` 中重复维护的手写帮助文案。
- 修正文档中已失效的命令引用：
  - 启动服务器必须带 `serve` 子命令（`./gitwebhooks-cli serve -c file.ini`）；
    原文档写作 `./gitwebhooks-cli -c file.ini`，实际只会打印帮助。
  - 模块入口是 `python3 -m gitwebhooks.main`（`gitwebhooks.cli` 无 `__main__.py`）。
  - README 结构树删除不存在的 `cli.py` 与 `install.sh`。
  - `cli/init_wizard.py` 的完成提示、`scripts/pre-release-check.sh` 的 CLI 检查
    此前仍指向已移除的 `service` 子命令（导致发布前检查实际失效）。

### Changed / 变更

- `-v` / `--version` 注册为 argparse 参数，因此会出现在 `--help` 中；
  不再由 `main()` 的预检查拦截（该预检查还会让 `serve -v` 意外打印版本号）。
- 新增 `tests/unit/cli/test_help.py`（基于 `unittest`）覆盖各层级 `help`/`version`
  的退出码、输出流与 `help <cmd>` ≡ `<cmd> --help` 的一致性。

### 工程与治理 / Tooling & Governance

- 迁移到 DSH 管理：新增 `CONSTITUTION.md`（项目编码宪章）与
  `.dsh/skills/code-review`（代码审查技能）；`CLAUDE.md` 由 `AGENTS.md` 取代。
- 清理其他 agent 工具残留：`.claude/`、`.specify/`、`.gitignore` 中的 SpecKit 段落、
  4 个空的 `tests/test_*` 目录。
- 修正 `.gitignore` 中拼错的配置文件名（`.gitwebhook.ini` → `.gitwebhooks.ini`），
  避免用户本地配置与密钥被误提交。

## [2.4.0] - 2026-01-16

### Removed / 移除

- 彻底移除 `service` 子命令及其向后兼容代码；systemd 服务管理改由
  `serve install` / `serve uninstall` 承担（`gitwebhooks/cli/service.py` 保留为内部实现模块）。

## [2.3.1] - 2026-01-16

### Fixed / 修复

- 修复 `serve` 命令显示弃用警告的问题。
- 恢复被误删的 `gitwebhooks-cli` 脚本。

## [2.3.0] - 2026-01-16

### Added / 新增

- 服务安装时的配置级别选择：`serve install --config-level user|local|system`。

### Changed / 变更

- 重构 CLI 命令结构，使其符合标准 Unix 工具规范。

> 注：本次发布提交（`chore: 发布版本 2.3.0`）中 `pyproject.toml` 的版本号仍为 `2.2.0`，
> 版本号是在紧随其后的 `chore: 更新 pyproject.toml 版本号到 2.3.0` 中才更新的。

## [2.2.0] - 2026-01-15

### Added / 新增

- 配置文件优先级自动查找：未指定 `-c` 时依次查找
  `~/.gitwebhooks.ini` → `/usr/local/etc/gitwebhooks.ini` → `/etc/gitwebhooks.ini`。

## [2.1.4] - 2026-01-15

### Changed / 变更

- 统一项目命名为 `gitwebhooks`。

### Fixed / 修复

- 修复多个测试与实现问题。

## [2.1.3] - 2026-01-14

### Fixed / 修复

- 修复配置初始化向导的多个问题。
- 恢复被误删的 `constitution.md`。

## [2.1.2] - 2026-01-14

### Added / 新增

- 发布前验证流程：`scripts/pre-release-check.sh`（构建 + 隔离环境安装 + CLI 冒烟）。

### Fixed / 修复

- 修复 CLI 入口点配置：`gitwebhooks.cli:main` → `gitwebhooks.main:main`。

## [2.1.1] - 2026-01-14

### Fixed / 修复

- 修正 README 中的包名（`git-webhooks-server` → `gitwebhooks`）。

## [2.1.0] - 2026-01-14

### Added / 新增

- 安装方法指导与服务文件自适应功能。

## [2.0.0] - 2026-01-14

首个发布到 PyPI 的版本，将原单文件实现重构为模块化包。

### Added / 新增

- 模块化包结构 `gitwebhooks/`：`models/`、`config/`、`auth/`、`handlers/`、`utils/`、`logging/`。
- 完整测试套件（单元测试 + 集成测试）。
- CLI 子命令取代 `install.sh`：`config init`（交互式配置向导）、`config view`（查看配置，敏感字段高亮）。

### Changed / 变更

- 安装方式简化为原地运行模式。
- 源码按模块拆分，所有源码注释统一为英文。

### Fixed / 修复

- 修复 Gitee webhook 签名验证算法。
- 修复 `install.sh --uninstall` 参数不生效的问题。
- 修复服务模板与安装脚本缺少 `WorkingDirectory` 的问题。
- 修复服务文件创建问题，并增加详细模式。

### Removed / 移除

- 移除旧的单文件实现与 `install.sh`。

---

## 2.0.0 之前（未发布到 PyPI）

2020–2022 年间为单文件实现（`git-webhooks-server.py`），已具备以下能力：

- 支持 GitHub、Gitee、GitLab 与自定义 webhook 源。
- 按 Header 识别平台；支持签名 / token / 密码验证。
- 支持指定需要处理的事件类型（`handle_events`）。
- 自定义 webhook 通过 `identifier_path` 提取仓库标识。
- 支持 SSL。
- 修复重启后服务无法启动的问题。

[未发布 / Unreleased]: https://gitee.com/holyhi/git-webhooks-server/compare/v2.4.1...HEAD
[2.4.1]: https://pypi.org/project/gitwebhooks/2.4.1/
[2.4.0]: https://pypi.org/project/gitwebhooks/2.4.0/
[2.3.1]: https://pypi.org/project/gitwebhooks/2.3.1/
[2.3.0]: https://pypi.org/project/gitwebhooks/2.3.0/
[2.2.0]: https://pypi.org/project/gitwebhooks/2.2.0/
[2.1.4]: https://pypi.org/project/gitwebhooks/2.1.4/
[2.1.3]: https://pypi.org/project/gitwebhooks/2.1.3/
[2.1.2]: https://pypi.org/project/gitwebhooks/2.1.2/
[2.1.1]: https://pypi.org/project/gitwebhooks/2.1.1/
[2.1.0]: https://pypi.org/project/gitwebhooks/2.1.0/
[2.0.0]: https://pypi.org/project/gitwebhooks/2.0.0/
