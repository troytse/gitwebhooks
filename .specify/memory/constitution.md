<!--
Sync Impact Report:
Version change: 2.0.0 → 2.1.0
Modified principles: N/A
Added sections: Environment Management (Development Workflow)
Removed sections: N/A
Templates updated:
  - .specify/templates/plan-template.md: ✅ reviewed (no changes needed)
  - .specify/templates/spec-template.md: ✅ reviewed (no changes needed)
  - .specify/templates/tasks-template.md: ✅ reviewed (no changes needed)
  - .specify/templates/checklist-template.md: ✅ reviewed (no changes needed)
  - .specify/templates/agent-file-template.md: ✅ reviewed (no changes needed)
Follow-up TODOs: N/A
-->

# Git Webhooks Server Constitution

## Core Principles

### I. Simplicity & Minimalism

The project MUST maintain a simple, modular Python architecture using a package structure (`gitwebhooks/`). Features MUST be justified against the cost of complexity. External dependencies beyond Python 3.7+ standard library are PROHIBITED unless absolutely essential. Configuration MUST remain INI-based and human-readable. Each module SHOULD be focused on a single responsibility and not exceed 400 lines of code.

**Rationale**: This project's value proposition is simplicity and ease of deployment. A well-organized modular structure enables code maintainability, testability, and extensibility while preserving simplicity. Users can read, understand, and modify individual modules efficiently. Adding unnecessary complexity or external dependencies undermines this core advantage.

### II. Platform Neutrality

The server MUST treat all Git platforms (Github, Gitee, Gitlab, custom) equally. No platform-specific hardcoded paths, assumptions, or special cases beyond documented header/event differences. Platform identification MUST be header-based only.

**Rationale**: Users may use any Git hosting service. Favoritism toward one platform creates maintenance burden and alienates users of other platforms.

### III. Configuration-Driven Behavior

All repository-specific logic MUST be defined in the INI configuration file, not in Python code. The `cwd` and `cmd` parameters for each repository section provide complete flexibility for deployment automation. No repository-specific code SHALL be added to the server.

**Rationale**: Configuration changes don't require code modification or redeployment. Users can customize deployment behavior without touching Python code.

### IV. Security by Verification

Webhook signature verification MUST be supported for all platforms. Token-based authentication is acceptable for platforms without HMAC signatures. Secret tokens MUST be stored in configuration files only, never hardcoded. SSL/TLS support MUST be available via configuration.

**Rationale**: Webhooks expose public endpoints that can be targeted by malicious actors. Verification ensures only authorized Git platforms trigger deployments.

### V. Service Integration

The project MUST support installation as a systemd service on Linux. The install script MUST be non-interactive when flags are provided. Logs MUST be written to a configurable file path with standard output forwarding.

**Rationale**: Production deployment requires daemonization, log management, and automatic restart capabilities. systemd is the Linux standard for service management.

### VI. Professional Commit Standards

All git/svn commits MUST NOT contain AI-generated attribution signatures such as "🤖 Generated with [Claude Code](https://claude.com/claude-code)" or similar promotional content. Commit messages MUST follow the format: `类型: 简短描述` (Chinese description) using standard types (feat, fix, docs, refactor, test, chore).

**Rationale**: Professional version control records should describe technical changes without promotional content. AI attribution signatures clutter commit history, reduce signal-to-noise ratio, and are unnecessary noise in production repositories. The commit authorship is already tracked by git's author metadata.

## Security Requirements

- All configuration files containing secrets MUST have restrictive file permissions (user-readable only, e.g., 0600)
- Webhook endpoints MUST reject unsupported HTTP methods (e.g., GET requests return 403)
- Command execution MUST use the repository's configured `cwd` to prevent directory traversal
- The service SHOULD run as an unprivileged user when possible
- SSL certificate paths MUST be validated before server start

## Development Workflow

### Environment Management

**ALL Python development and testing MUST be performed within a virtual environment.** The project provides a `venv/` directory for this purpose. Before any development work:

1. Activate the virtual environment: `source venv/bin/activate`
2. Install dependencies: `pip install -e .`
3. Install dev dependencies: `pip install -e ".[dev]"` (for testing)

**Rationale**: Virtual environments isolate project dependencies from system Python, prevent version conflicts, and ensure reproducible builds. This is especially critical for a package targeting PyPI distribution.

### Code Style

- Follow the `.editorconfig` settings for all source files
- Python code MUST use standard library patterns (no external frameworks)
- Private methods use double-underscore prefix convention
- Logging MUST use the `logging` module with appropriate levels

### Testing Approach

- Manual testing with actual Git platforms is acceptable given the project's simplicity
- Changes MUST be tested against all supported platforms when platform logic is modified
- Configuration file changes SHOULD be validated with `configparser` before deployment

### Release Process

1. Update version in any version variable if added
2. Test installation script on a clean system
3. Verify all platform webhook formats still work
4. Update README.md and README.zh.md if behavior changes
5. Tag release with semantic version

### Commit Message Standards

All commits MUST follow the format: `类型: 简短描述` (Chinese description)

Valid commit types:
- `feat`: 新功能 (new feature)
- `fix`: 修复 (bug fix)
- `docs`: 文档 (documentation)
- `refactor`: 重构 (code refactoring)
- `test`: 测试 (adding or updating tests)
- `chore`: 构建/工具 (build process or tooling changes)

**PROHIBITED**: AI-generated attribution signatures, promotional content, or emojis in commit messages.

## Governance

### Amendment Procedure

This constitution governs all development decisions. Amendments require:

1. Documentation of the proposed change with rationale
2. Update to this constitution file with version bump
3. Synchronization with dependent template files (plan, spec, tasks)
4. Review of existing code for compliance violations

### Versioning

Constitution versions follow semantic versioning (MAJOR.MINOR.PATCH):

- **MAJOR**: Principle removal or backward-incompatible governance changes
- **MINOR**: New principle added or materially expanded guidance
- **PATCH**: Clarifications, wording improvements, non-semantic refinements

### Compliance Review

All code changes MUST be evaluated against these principles. Violations require:

1. Explicit justification in the commit message or pull request
2. Documented rationale in this constitution's Complexity Tracking section (if added)
3. Consideration of simpler alternatives

### Runtime Development Guidance

For day-to-day development activities, refer to `CLAUDE.md` for:
- Architecture overview and component descriptions
- Build, test, and deployment commands
- Code style and formatting guidelines
- Project structure and file organization

**Version**: 2.1.0 | **Ratified**: 2026-01-12 | **Last Amended**: 2026-01-14
