# Simple Git Webhooks Server

[README](README.md) | [中文说明](README.zh.md)

## Table of Contents
- [Introduction](#introduction)
- [Architecture](#architecture)
- [Installation](#installation)
- [Uninstallation](#uninstallation)
- [Usage](#usage)
  - [Github](#github)
  - [Gitee](#gitee)
  - [Gitlab](#gitlab)
  - [Custom](#custom)
- [Configuration](#configuration)
- [Project Structure](#project-structure)

## Introduction

A lightweight Git webhook server for automated deployment.

- Implemented with Python 3.6+ (standard library only)
- Supports Github, Gitee, Gitlab, and custom repositories
- Custom working directory and command for different repositories
- Installable as a Systemd service
- Modular architecture for easy extension and testing

## Architecture

**Version 2.0** features a modular package structure:

```
gitwebhooks/
├── models/          # Data models (Provider, Request, Result)
├── config/          # Configuration management
├── auth/            # Signature verification
├── handlers/        # Webhook handlers
├── utils/           # Utilities
└── logging/         # Logging setup
```

**Key Features:**
- **Dependency Injection**: ConfigurationRegistry, VerifierFactory, HandlerFactory
- **Abstract Base Classes**: SignatureVerifier, WebhookHandler
- **No External Dependencies**: 100% Python standard library
- **In-Place Execution**: CLI runs from source directory

## Installation

### Prerequisites

- Python 3.6 or higher
- pip (Python package manager)
- sudo/root access (for systemd service installation)

### Recommended: pipx (System-wide installation)

pipx is the recommended way to install gitwebhooks system-wide.

```bash
# Install pipx (if not already installed)
sudo apt install pipx  # Ubuntu/Debian
# or: python3 -m pip install --user pipx

# Install gitwebhooks
pipx install gitwebhooks
```

**Why pipx?**
- Isolated from system Python packages
- No dependency conflicts
- Easy to upgrade and uninstall
- Automatic service file configuration

### Alternative: venv (Virtual environment)

If you prefer using Python's built-in venv module:

```bash
# Create virtual environment
python3 -m venv ~/venv/gitwebhooks

# Activate and install
source ~/venv/gitwebhooks/bin/activate
pip install gitwebhooks

# Add to PATH (optional)
echo 'export PATH="$HOME/venv/gitwebhooks/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### ⚠️ NOT Recommended: System pip

**Warning**: Installing directly with `sudo pip install` is NOT recommended:

```bash
# DO NOT DO THIS
sudo pip install gitwebhooks
```

**Risks**:
- Can conflict with system Python packages
- May break system tools that depend on Python
- Difficult to uninstall cleanly

### Initialize Configuration

```bash
# Interactive configuration setup (prompts for configuration level)
gitwebhooks-cli config init

# Or specify configuration level directly
gitwebhooks-cli config init user      # User level (~/.gitwebhooks.ini)
gitwebhooks-cli config init local      # Local level (/usr/local/etc/gitwebhooks.ini)
sudo gitwebhooks-cli config init system # System level (/etc/gitwebhooks.ini, requires root)
```

The wizard will prompt for:
1. Configuration level (system/local/user)
2. Server configuration (address, port, log file)
3. Git platform (github/gitee/gitlab/custom)
4. Platform-specific settings (webhook events, verification, secret)
5. Repository configuration (name, working directory, deploy command)

This will create a configuration file with secure permissions (0600).

### Install as systemd Service

The service installation command automatically detects your installation type (pipx, venv, or system) and generates the appropriate service file.

```bash
# Install and start as a systemd service
sudo gitwebhooks-cli service install

# Preview service file without installing (dry-run mode)
sudo gitwebhooks-cli service install --dry-run

# Install with verbose output
sudo gitwebhooks-cli service install --verbose
sudo gitwebhooks-cli service install -v      # Basic verbosity
sudo gitwebhooks-cli service install -vv     # Extra verbosity

# Force overwrite existing service
sudo gitwebhooks-cli service install --force

# Uninstall the service
sudo gitwebhooks-cli service uninstall
```

**Service file auto-detection**:
- **pipx installation**: Uses `gitwebhooks-cli` command directly
- **venv/virtualenv**: Uses `python -m gitwebhooks.cli` with environment's Python
- **System pip**: Uses system Python with `python -m gitwebhooks.cli`
- **conda**: Not supported - installation will be refused with clear error message

### Manual Installation

To install manually without pip:

```bash
# Make CLI executable
chmod +x gitwebhooks-cli

# Create hard link to system path
sudo ln "$(pwd)/gitwebhooks-cli" /usr/local/bin/gitwebhooks-cli
```

### Verify Installation

```bash
gitwebhooks-cli --help
```

## Migrating from System pip Installation

If you previously installed gitwebhooks using `sudo pip install`,
follow these steps to migrate to a recommended installation method.

### Step 1: Uninstall the old installation

```bash
sudo pip uninstall gitwebhooks
```

### Step 2: Backup your configuration (if exists)

```bash
cp ~/.gitwebhook.ini ~/.gitwebhook.ini.backup
```

### Step 3: Stop and uninstall the service (if installed)

```bash
sudo systemctl stop gitwebhooks
sudo systemctl disable gitwebhooks
sudo gitwebhooks-cli service uninstall
```

### Step 4: Install using the recommended method

Choose **pipx** (recommended):
```bash
# Install pipx if needed
sudo apt install pipx  # Ubuntu/Debian
# or: python3 -m pip install --user pipx

# Install gitwebhooks
pipx install gitwebhooks
```

Or **venv**:
```bash
# Create virtual environment
python3 -m venv ~/venv/gitwebhooks
source ~/venv/gitwebhooks/bin/activate

# Install gitwebhooks
pip install gitwebhooks
```

### Step 5: Restore configuration (if backed up)

```bash
# If you backed up your configuration
cp ~/.gitwebhook.ini.backup ~/.gitwebhook.ini
# Or create a new one
gitwebhooks-cli config init
```

### Step 6: Reinstall the service

```bash
sudo gitwebhooks-cli service install
```

### Step 7: Verify

```bash
sudo systemctl status gitwebhooks
```

## Uninstallation

```bash
# Uninstall systemd service (if installed)
sudo gitwebhooks-cli service uninstall --purge

# Remove the package
pip uninstall gitwebhooks
```

## Usage

### Configuration File Auto-Discovery

The `gitwebhooks-cli` automatically searches for configuration files in the following order (priority):

1. **User level**: `~/.gitwebhooks.ini` (highest priority)
2. **Local level**: `/usr/local/etc/gitwebhooks.ini`
3. **System level**: `/etc/gitwebhooks.ini` (lowest priority)

You can run `gitwebhooks-cli` without specifying `-c` parameter, and it will automatically use the first existing configuration file.

```bash
# Auto-discover and use configuration file
gitwebhooks-cli

# The server will display which config file is being used
# Using configuration file: /home/user/.gitwebhooks.ini
```

If you want to use a specific configuration file, use the `-c` parameter:

```bash
# Use a specific configuration file
gitwebhooks-cli -c /path/to/custom.ini
```

If no configuration file is found, a friendly error message will display all searched paths:

```
Error: Configuration file not found.
Searched paths:
  1. /home/user/.gitwebhooks.ini
  2. /usr/local/etc/gitwebhooks.ini
  3. /etc/gitwebhooks.ini

You can create a configuration file using:
  gitwebhooks-cli config init
```

### 1. Configure Repository

Edit your configuration file (e.g., `~/.gitwebhooks.ini`):

```ini
[your_name/repository]
cwd=/path/to/your/repository
cmd=git fetch --all && git reset --hard origin/master && git pull
```

### 2. Restart Service

```bash
# If running as a service
systemctl restart gitwebhooks

# Or run directly (auto-discovers config file):
gitwebhooks-cli
```

### 3. Add Webhook

#### Github

![github](doc/github.png)
![github-success](doc/github-success.png)

#### Gitee

![gitee](doc/gitee.png)
![gitee-success](doc/gitee-success.png)

#### Gitlab

![gitlab](doc/gitlab.png)
![gitlab-success](doc/gitlab-success.png)

#### Custom

For custom webhook sources, configure like this:

```ini
[custom]
# Header to identify the source
header_name=X-Custom-Header
header_value=Custom-Git-Hookshot
# Header for token verification
header_token=X-Custom-Token
# Path to repository name in JSON payload
identifier_path=project.path_with_namespace
verify=True
secret=123456
```

The handler accepts POST data with `application/json` or `application/x-www-form-urlencoded` content type. See [Github](https://developer.github.com/webhooks/event-payloads/#example-delivery) / [Gitee](https://gitee.com/help/articles/4186) / [Gitlab](https://gitlab.com/help/user/project/integrations/webhooks#push-events) for payload examples.

Example payload:
```json
{
  "project": {
    "path_with_namespace": "your_name/repository"
  }
}
```

![custom-header](doc/custom-header.png)
![custom-body](doc/custom-body.png)
![custom-response](doc/custom-response.png)

## Configuration

Default configuration file: `~/.gitwebhook.ini`

### Initialize Configuration

```bash
# Interactive configuration setup
gitwebhooks-cli config init

# Or specify configuration level directly
gitwebhooks-cli config init user
sudo gitwebhooks-cli config init system
```

### View Configuration

```bash
# View current configuration file (auto-detects location)
gitwebhooks-cli config view

# View specific configuration file
gitwebhooks-cli config view -c /path/to/config.ini
```

The `config view` command displays:
- Configuration file path and source (user-specified or auto-detected)
- Configuration content organized by sections
- Sensitive fields (containing: secret, password, token, key, passphrase) highlighted in yellow

To disable color highlighting:
```bash
NO_COLOR=1 gitwebhooks-cli config view
```

### Server Configuration

```ini
[server]
address=0.0.0.0          # Listen address
port=6789                # Listen port
log_file=~/.gitwebhook.log  # Log file (empty = stdout only)
```

### SSL Configuration (Optional)

```ini
[ssl]
enable=False
key_file=/path/to/key.pem
cert_file=/path/to/cert.pem
```

### Provider Configuration

```ini
[github]
verify=True              # Enable signature verification
secret=your_webhook_secret
handle_events=push,pull_request  # Events to handle (empty = all)

[gitee]
verify=True
secret=your_webhook_secret

[gitlab]
verify=True
secret=your_webhook_token

[custom]
header_name=X-Custom-Header
header_value=Your-Identifier
header_token=X-Custom-Token
identifier_path=project.path_with_namespace
verify=True
secret=your_secret
```

### Repository Configuration

```ini
[owner/repository]
cwd=/path/to/repo    # Working directory
cmd=your_command     # Command to execute
```

## Project Structure

```
gitwebhooks/
├── gitwebhooks/              # Python package (modular v2.0)
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py                # CLI entry point
│   ├── server.py             # HTTP server
│   ├── models/               # Data models
│   ├── config/               # Configuration management
│   ├── auth/                 # Signature verification
│   ├── handlers/             # Webhook handlers
│   ├── utils/                # Utilities
│   └── logging/              # Logging setup
├── gitwebhooks-cli           # CLI wrapper script
├── install.sh                # Installation script
├── gitwebhooks.ini.sample
└── tests/                    # Test suite
```

## Development

### Running from Source

```bash
# Method 1: Use CLI tool (recommended)
./gitwebhooks-cli -c gitwebhooks.ini.sample

# Method 2: Use module entry
python3 -m gitwebhooks.cli -c gitwebhooks.ini.sample
```

### Running Tests

```bash
# Using pytest
python3 -m pytest tests/

# Or using unittest
python3 -m unittest discover tests/
```

### Releasing to PyPI

**IMPORTANT**: Before releasing to PyPI, you MUST run the pre-release validation script:

```bash
./scripts/pre-release-check.sh
```

This script validates:
- Package builds successfully
- CLI entry point works (`gitwebhooks-cli`)
- All subcommands work (`service`, `config`)
- Module imports work correctly

Only after all checks pass, proceed with publishing:

```bash
# Build the package
python3 -m build

# Upload to PyPI
python3 -m twine upload dist/*
```

## License

MIT License
