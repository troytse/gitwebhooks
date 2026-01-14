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

### Install via pip

```bash
# Install from PyPI (when published)
pip install gitwebhooks

# Or install from source
git clone https://github.com/troytse/git-webhooks-server.git
cd git-webhooks-server
pip install .
```

### Initialize Configuration

```bash
# Create initial configuration file
gitwebhooks-cli config init
```

This will create `~/.gitwebhook.ini` with interactive prompts.

### Install as systemd Service

```bash
# Install and start as a systemd service
sudo gitwebhooks-cli service install

# Uninstall the service
sudo gitwebhooks-cli service uninstall
```

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

## Uninstallation

```bash
# Uninstall systemd service (if installed)
sudo gitwebhooks-cli service uninstall --purge

# Remove the package
pip uninstall gitwebhooks
```

## Usage

### 1. Configure Repository

Edit `~/.gitwebhook.ini`:

```ini
[your_name/repository]
cwd=/path/to/your/repository
cmd=git fetch --all && git reset --hard origin/master && git pull
```

### 2. Restart Service

```bash
# If running as a service
systemctl restart git-webhooks-server

# Or run directly:
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

# Or specify output path
gitwebhooks-cli config init --output /path/to/config.ini
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
git-webhooks-server/
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
├── git-webhooks-server.ini.sample
└── tests/                    # Test suite
```

## Development

### Running from Source

```bash
# Method 1: Use CLI tool (recommended)
./gitwebhooks-cli -c git-webhooks-server.ini.sample

# Method 2: Use module entry
python3 -m gitwebhooks.cli -c git-webhooks-server.ini.sample
```

### Running Tests

```bash
# Using pytest
python3 -m pytest tests/

# Or using unittest
python3 -m unittest discover tests/
```

## License

MIT License
