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
- sudo/root access (for installation)

### Install from Source

```bash
# Clone or download the repository
git clone https://github.com/troytse/git-webhooks-server.git
cd git-webhooks-server

# Run the installation script
./install.sh
```

The installer will:
1. Create a hard link for `gitwebhooks-cli` in `/usr/local/bin`
2. Copy configuration file to `/usr/local/etc/git-webhooks-server.ini`
3. Optionally install as a systemd service

![install](doc/install.png)

### Manual Installation

To install manually without the script:

```bash
# Make CLI executable
chmod +x gitwebhooks-cli

# Create hard link to system path
sudo ln "$(pwd)/gitwebhooks-cli" /usr/local/bin/gitwebhooks-cli

# Copy configuration
sudo cp git-webhooks-server.ini.sample /usr/local/etc/git-webhooks-server.ini
```

### Verify Installation

```bash
gitwebhooks-cli --help
```

## Uninstallation

```bash
cd git-webhooks-server
./install.sh --uninstall
```

![uninstall](doc/uninstall.png)

## Usage

### 1. Configure Repository

Edit `/usr/local/etc/git-webhooks-server.ini`:

```ini
[your_name/repository]
cwd=/path/to/your/repository
cmd=git fetch --all && git reset --hard origin/master && git pull
```

### 2. Restart Service

```bash
systemctl restart git-webhooks-server
# Or run directly:
gitwebhooks-cli -c /usr/local/etc/git-webhooks-server.ini
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

Default configuration file: `/usr/local/etc/git-webhooks-server.ini`

### Server Configuration

```ini
[server]
address=0.0.0.0          # Listen address
port=6789                # Listen port
log_file=/var/log/git-webhooks-server.log  # Log file (empty = stdout only)
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
# From project root
./gitwebhooks-cli -c git-webhooks-server.ini.sample
```

### Running Tests

```bash
python3 -m unittest discover tests/
```

## License

MIT License
