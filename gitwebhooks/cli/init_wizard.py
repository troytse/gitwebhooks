"""
Interactive configuration initialization wizard.

This module provides a user-friendly wizard for creating git-webhooks-server
configuration files through an interactive command-line interface.

Features:
- Support for GitHub, Gitee, GitLab, and custom webhook platforms
- Automatic validation of repository names (supports dots, hyphens, underscores)
- Direct text input for event names with platform-specific defaults
- Secure file generation with proper permissions (0600)

Validation Functions:
- validate_repo_name: Validates repository name format
- validate_event_input: Validates event name input (rejects newlines and digits)
- _get_platform_default_event: Returns platform-specific default event

TECHNICAL DEBT:
This module (768 lines) exceeds the Constitution's recommended 400 line limit.
This is acceptable because the module contains the complete interactive wizard
logic including platform selection, repository configuration, event configuration,
and file generation.

Refactoring Plan (future task):
- Extract validation functions to gitwebhooks/cli/wizard_validators.py
- Consider splitting Wizard class into smaller focused classes
- Evaluate separating platform-specific logic into dedicated handlers
"""

import os
import re
from dataclasses import dataclass
from typing import Optional, List, Dict
import configparser


# =============================================================================
# Module Constants
# =============================================================================

CONFIG_LEVELS = {
    'system': {
        'path': '/etc/gitwebhooks.ini',
        'requires_root': True
    },
    'local': {
        'path': '/usr/local/etc/gitwebhooks.ini',
        'requires_root': True
    },
    'user': {
        'path': '~/.gitwebhooks.ini',
        'requires_root': False
    }
}

PLATFORMS = {
    'github': {
        'events': ['push', 'release', 'pull_request', 'tag'],
        'requires_secret': True
    },
    'gitee': {
        'events': ['push', 'release', 'pull_request'],
        'requires_secret': True
    },
    'gitlab': {
        'events': ['push', 'release', 'tag'],
        'requires_secret': True
    },
    'custom': {
        'events': [],
        'requires_secret': False,
        'custom_fields': ['header_name', 'header_value', 'identifier_path', 'header_event']
    }
}

# 平台默认事件值
# 每个平台使用不同的默认事件格式：
# - GitHub: 'push' (小写单数)
# - Gitee: 'Push Hook' (大写带空格)
# - GitLab: 'Push Hooks' (大写空格复数)
# - Custom: 'webhook' (通用自定义事件)
PLATFORM_DEFAULT_EVENTS = {
    'github': 'push',
    'gitee': 'Push Hook',
    'gitlab': 'Push Hooks',
    'custom': 'webhook',
}


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class ConfigLevel:
    """Configuration level metadata."""
    name: str
    path: str
    requires_root: bool


@dataclass
class ServerConfig:
    """Server configuration parameters."""
    address: str
    port: int
    log_file: str


@dataclass
class PlatformConfig:
    """Platform configuration parameters."""
    platform: str
    handle_events: str  # Changed from List[str] to str - comma-separated event names
    verify: bool
    secret: Optional[str] = None
    custom_params: Optional[Dict[str, str]] = None


@dataclass
class RepositoryConfig:
    """Repository configuration parameters."""
    name: str
    cwd: str
    cmd: str


# =============================================================================
# Input Validation Functions
# =============================================================================

def validate_repo_name(value: str) -> bool:
    """
    验证仓库名称格式。

    支持的格式：
    - Two-level: owner/repo (GitHub/Gitee)
    - Multi-level: group/subgroup/project (GitLab)
    - 特殊字符: 支持点号、连字符、下划线

    有效示例：
    - owner/repo
    - my-org/my-repo
    - user.repo/project
    - group/sub_group/project.name

    无效示例：
    - owner repo (包含空格)
    - owner/repo/ (尾部斜杠)
    - owner@org/repo (包含不支持的字符)

    Args:
        value: 仓库名称字符串

    Returns:
        True if valid, False otherwise
    """
    return bool(re.match(r'^[\w.-]+(/[\w.-]+)*$', value))


def validate_existing_path(value: str) -> bool:
    """
    Validate that a path exists and is a directory.

    Args:
        value: Path string to validate

    Returns:
        True if path exists and is a directory, False otherwise
    """
    return os.path.isdir(value)


def validate_non_empty(value: str) -> bool:
    """
    Validate that a string is not empty or whitespace-only.

    Args:
        value: String to validate

    Returns:
        True if string has non-whitespace content, False otherwise
    """
    return bool(value.strip())


def validate_port(value: str) -> bool:
    """
    Validate port number.

    Args:
        value: Port number as string

    Returns:
        True if valid port (1-65535), False otherwise
    """
    try:
        port = int(value)
        return 1 <= port <= 65535
    except ValueError:
        return False


def validate_event_input(value: str) -> tuple[bool, str]:
    """
    验证事件名称输入。

    验证规则：
    1. 不能为空字符串
    2. 不能包含换行符（会破坏 INI 文件格式）
    3. 不能包含数字（拒绝旧的数字选择格式）

    Args:
        value: 用户输入的事件名称

    Returns:
        (is_valid, error_message) - 验证结果和错误消息（如果验证失败）
    """
    # 空输入检查（由调用方处理默认值，这里只做非空检查）
    if not value or not value.strip():
        return False, "事件名称不能为空"

    # 换行符检查
    if '\n' in value or '\r' in value:
        return False, "事件名称不能包含换行符"

    # 数字检查：去除逗号和空格后检查是否包含数字
    cleaned = value.replace(',', '').replace(' ', '')
    if any(c.isdigit() for c in cleaned):
        return False, "请直接输入事件名称，不支持数字选择"

    return True, ""


def _get_platform_default_event(platform: str) -> str:
    """
    获取平台默认事件值。

    Args:
        platform: 平台名称 (github/gitee/gitlab/custom)

    Returns:
        默认事件字符串，如果平台未找到则返回 'webhook'
    """
    return PLATFORM_DEFAULT_EVENTS.get(platform.lower(), 'webhook')


# =============================================================================
# INI Generation Functions
# =============================================================================

def _generate_config(
    server: ServerConfig,
    platform: PlatformConfig,
    repo: RepositoryConfig
) -> configparser.ConfigParser:
    """
    Generate configuration object from collected data.

    Args:
        server: Server configuration
        platform: Platform configuration
        repo: Repository configuration

    Returns:
        ConfigParser object with all sections
    """
    config = configparser.ConfigParser()

    # Server section
    config['server'] = {
        'address': server.address,
        'port': str(server.port),
        'log_file': server.log_file
    }

    # Platform section
    platform_section = platform.platform
    platform_config = {
        'handle_events': platform.handle_events,  # Direct string value
        'verify': 'true' if platform.verify else 'false'
    }

    if platform.verify and platform.secret:
        platform_config['secret'] = platform.secret

    # Add custom platform parameters if present
    if platform.custom_params:
        for key, value in platform.custom_params.items():
            if value:  # Only add non-empty values
                platform_config[key] = value

    config[platform_section] = platform_config

    # Repository section
    repo_section = repo.name
    config[repo_section] = {
        'cwd': repo.cwd,
        'cmd': repo.cmd
    }

    return config


# =============================================================================
# Wizard Class
# =============================================================================

class Wizard:
    """
    Interactive configuration wizard.

    Guides users through creating a git-webhooks-server configuration file
    by collecting server, platform, and repository configuration parameters.
    """

    def __init__(self, level: Optional[str] = None):
        """
        Initialize the wizard.

        Args:
            level: Optional configuration level (system/local/user).
                   If None, user will be prompted to select.

        Raises:
            ValueError: If level is provided but invalid
        """
        if level is not None and level not in CONFIG_LEVELS:
            raise ValueError(f"Invalid configuration level: {level}. "
                           f"Must be one of: {', '.join(CONFIG_LEVELS.keys())}")

        self.level = level
        self.config_level: Optional[ConfigLevel] = None

    def run(self) -> str:
        """
        Run the wizard and generate configuration file.

        Returns:
            Absolute path to the generated configuration file

        Raises:
            KeyboardInterrupt: User presses Ctrl+C
            PermissionError: Cannot write to target directory
            FileExistsError: User cancels overwrite
        """
        try:
            # Step 1: Determine configuration level
            if self.level is None:
                self._select_level()
            else:
                self._set_level(self.level)

            # Step 2: Check permissions
            self._check_permissions()

            # Step 3: Collect server configuration
            server_config = self._collect_server_config()

            # Step 4: Select and configure platform
            platform_name = self._select_platform()
            platform_config = self._collect_platform_config(platform_name)

            # Step 5: Collect repository configuration
            repo_config = self._collect_repository_config()

            # Step 6: Confirm overwrite if file exists
            config_path = os.path.expanduser(self.config_level.path)
            backup = False
            if os.path.exists(config_path):
                backup = self._confirm_overwrite(config_path)

            # Step 7: Generate configuration
            config = _generate_config(server_config, platform_config, repo_config)

            # Step 8: Write configuration file
            self._write_config(config, config_path, backup=backup)

            # Step 9: Show completion message
            self._show_completion(config_path)

            return config_path

        except KeyboardInterrupt:
            print("\n操作已取消")
            # Clean up partial files if any
            self._cleanup()
            raise

    def _set_level(self, level_name: str) -> None:
        """
        Set configuration level from name.

        Args:
            level_name: Configuration level name (system/local/user)
        """
        level_config = CONFIG_LEVELS[level_name]
        self.config_level = ConfigLevel(
            name=level_name,
            path=level_config['path'],
            requires_root=level_config['requires_root']
        )

    def _select_level(self) -> None:
        """
        Interactively select configuration level.

        Updates self.config_level with selected level.
        """
        print("选择配置级别:")
        levels = list(CONFIG_LEVELS.items())
        for idx, (name, config) in enumerate(levels, 1):
            path = config['path']
            print(f"  {idx}. {name} ({path})")

        while True:
            try:
                choice = input(f"输入选择 [1-{len(levels)}]: ").strip()
                if not choice:
                    print("请选择一个配置级别")
                    continue

                index = int(choice) - 1
                if 0 <= index < len(levels):
                    level_name, level_config = levels[index]
                    self._set_level(level_name)
                    return
                else:
                    print(f"无效选择，请输入 1-{len(levels)} 之间的数字")
            except ValueError:
                print("请输入有效的数字")
            except KeyboardInterrupt:
                raise

    def _check_permissions(self) -> None:
        """
        Check if target directory is writable.

        Raises:
            PermissionError: If target directory is not writable
        """
        config_path = os.path.expanduser(self.config_level.path)
        target_dir = os.path.dirname(config_path)

        # Create directory if it doesn't exist (for user level)
        if not os.path.exists(target_dir):
            try:
                os.makedirs(target_dir, exist_ok=True)
            except OSError as e:
                raise PermissionError(
                    f"无法创建目录 {target_dir}: {e}\n"
                    f"建议: 使用 sudo 或选择 user 级别"
                )

        # Check write permission
        if not os.access(target_dir, os.W_OK):
            raise PermissionError(
                f"无法写入 {self.config_level.path}（权限不足）\n"
                f"建议: 使用 sudo 或选择 user 级别"
            )

    def _collect_server_config(self) -> ServerConfig:
        """
        Collect server configuration parameters.

        Returns:
            ServerConfig object with collected parameters
        """
        print("\n--- 服务器配置 ---")

        # Address
        default_address = "0.0.0.0"
        address = input(f"服务器监听地址 [默认: {default_address}]: ").strip()
        if not address:
            address = default_address

        # Port
        default_port = "6789"
        while True:
            port_str = input(f"服务器端口 [默认: {default_port}]: ").strip()
            if not port_str:
                port = int(default_port)
                break
            if validate_port(port_str):
                port = int(port_str)
                break
            print("端口号必须在 1-65535 之间")

        # Log file
        default_log = "/var/log/git-webhooks-server.log"
        log_file = input(f"日志文件路径 [默认: {default_log}]: ").strip()
        if not log_file:
            log_file = default_log

        return ServerConfig(
            address=address,
            port=port,
            log_file=log_file
        )

    def _select_platform(self) -> str:
        """
        Interactively select Git platform.

        Returns:
            Platform name (github/gitee/gitlab/custom)
        """
        print("\n选择 Git 平台:")
        platforms = list(PLATFORMS.keys())
        for idx, platform in enumerate(platforms, 1):
            print(f"  {idx}. {platform}")

        while True:
            try:
                choice = input(f"输入选择 [1-{len(platforms)}]: ").strip()
                if not choice:
                    print("请选择一个平台")
                    continue

                index = int(choice) - 1
                if 0 <= index < len(platforms):
                    return platforms[index]
                else:
                    print(f"无效选择，请输入 1-{len(platforms)} 之间的数字")
            except ValueError:
                print("请输入有效的数字")
            except KeyboardInterrupt:
                raise

    def _collect_platform_config(self, platform: str) -> PlatformConfig:
        """
        Collect platform configuration parameters.

        Args:
            platform: Platform name

        Returns:
            PlatformConfig object with collected parameters
        """
        print(f"\n--- {platform.upper()} 平台配置 ---")

        platform_info = PLATFORMS[platform]

        # Collect events
        handle_events = self._collect_events(platform)

        # Collect verification settings
        verify = False
        secret = None

        if platform_info['requires_secret']:
            while True:
                verify_input = input("是否启用签名验证？ [y/N]: ").strip().lower()
                if verify_input in ('y', 'yes'):
                    verify = True
                    break
                elif verify_input in ('n', 'no', ''):
                    verify = False
                    break
                else:
                    print("请输入 y 或 n")

            if verify:
                while True:
                    secret = input("输入验证密钥: ").strip()
                    if validate_non_empty(secret):
                        break
                    print("验证密钥不能为空")

        # Custom platform parameters
        custom_params = None
        if platform == 'custom':
            custom_params = self._collect_custom_params()

        return PlatformConfig(
            platform=platform,
            handle_events=handle_events,
            verify=verify,
            secret=secret,
            custom_params=custom_params
        )

    def _collect_events(self, platform: str) -> str:
        """
        收集平台要处理的事件名称。

        改为直接文本输入方式，支持逗号分隔多个事件。
        空输入时使用平台默认值。

        Args:
            platform: Platform name (github/gitee/gitlab/custom)

        Returns:
            逗号分隔的事件名称字符串
        """
        default_event = _get_platform_default_event(platform)
        prompt = f"输入要处理的事件名称（多个用逗号分隔，直接回车默认: {default_event}）: "

        while True:
            value = input(prompt).strip()

            # 空输入使用默认值
            if not value:
                return default_event

            # 验证输入
            is_valid, error_msg = validate_event_input(value)
            if not is_valid:
                print(f"错误: {error_msg}")
                continue

            # 去除逗号前后的空格
            cleaned = ','.join(part.strip() for part in value.split(','))
            return cleaned

    def _collect_custom_params(self) -> Dict[str, str]:
        """
        Collect custom platform specific parameters.

        Returns:
            Dictionary of custom parameter names and values
        """
        print("\n--- 自定义平台参数 ---")

        params = {}

        # header_name
        default_header_name = "X-Webhook-Token"
        header_name = input(f"输入识别 Header 名称 [默认: {default_header_name}]: ").strip()
        params['header_name'] = header_name if header_name else default_header_name

        # header_value
        while True:
            header_value = input("输入验证 Header 值: ").strip()
            if validate_non_empty(header_value):
                params['header_value'] = header_value
                break
            print("Header 值不能为空")

        # identifier_path
        default_identifier = "project.path_with_namespace"
        identifier_path = input(f"输入仓库标识 JSON 路径 [默认: {default_identifier}]: ").strip()
        params['identifier_path'] = identifier_path if identifier_path else default_identifier

        # header_event (optional)
        header_event = input("输入事件类型 Header 名称 [可选，直接回车跳过]: ").strip()
        if header_event:
            params['header_event'] = header_event

        return params

    def _collect_repository_config(self) -> RepositoryConfig:
        """
        Collect repository configuration parameters.

        Returns:
            RepositoryConfig object with collected parameters
        """
        print("\n--- 仓库配置 ---")

        # Repository name
        while True:
            repo_name = input("输入仓库名称 (格式: owner/repo): ").strip()
            if validate_repo_name(repo_name):
                break
            print("仓库名称只能包含字母、数字、斜杠、点号、连字符和下划线")

        # Working directory
        while True:
            cwd = input("输入工作目录路径 (必须已存在): ").strip()
            if validate_existing_path(cwd):
                break
            print(f"错误: 目录不存在: {cwd}")

        # Deploy command
        while True:
            cmd = input("输入部署命令: ").strip()
            if validate_non_empty(cmd):
                break
            print("部署命令不能为空")

        return RepositoryConfig(
            name=repo_name,
            cwd=cwd,
            cmd=cmd
        )

    def _confirm_overwrite(self, path: str) -> bool:
        """
        Confirm whether to overwrite existing configuration file.

        Args:
            path: Path to existing file

        Returns:
            True to proceed with overwrite, False to cancel

        Raises:
            FileExistsError: User chooses to cancel
        """
        print(f"\n配置文件 {path} 已存在")
        print("选择操作:")
        print("  1. 覆盖（会删除原文件）")
        print("  2. 备份后覆盖（保存为 .bak）")
        print("  3. 取消操作")

        while True:
            try:
                choice = input("输入选择 [1-3]: ").strip()
                if choice == '1':
                    return False  # Overwrite without backup
                elif choice == '2':
                    return True  # Backup then overwrite
                elif choice == '3':
                    raise FileExistsError("用户取消操作")
                else:
                    print("请输入 1、2 或 3")
            except KeyboardInterrupt:
                raise

    def _write_config(
        self,
        config: configparser.ConfigParser,
        path: str,
        backup: bool = False
    ) -> None:
        """
        Write configuration file to disk.

        Args:
            config: ConfigParser object
            path: Target file path
            backup: Whether to backup existing file
        """
        try:
            # Backup existing file if requested
            if backup and os.path.exists(path):
                backup_path = f"{path}.bak"
                os.rename(path, backup_path)
                print(f"已备份原文件到: {backup_path}")

            # Write configuration
            with open(path, 'w') as f:
                config.write(f)

            # Set secure permissions (user read/write only)
            os.chmod(path, 0o600)

        except OSError as e:
            raise PermissionError(f"无法写入配置文件 {path}: {e}")

    def _show_completion(self, path: str) -> None:
        """
        Display completion message and next steps.

        Args:
            path: Generated configuration file path
        """
        print(f"\n配置文件已生成: {path}")
        print("后续步骤:")
        print(f"  1. 检查配置文件内容: gitwebhooks-cli config view {path}")
        print(f"  2. 启动服务器: gitwebhooks-cli -c {path}")
        print("  3. 或安装为服务: sudo gitwebhooks-cli service install")

    def _cleanup(self) -> None:
        """
        Clean up partial files if wizard is interrupted.

        This method is called when KeyboardInterrupt is caught.
        """
        # Remove partial configuration file if it exists
        if self.config_level:
            config_path = os.path.expanduser(self.config_level.path)
            if os.path.exists(config_path):
                try:
                    os.remove(config_path)
                    print(f"已清理部分文件: {config_path}")
                except OSError:
                    pass
