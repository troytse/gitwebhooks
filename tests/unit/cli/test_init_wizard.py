"""
Unit tests for init_wizard module.

Tests the configuration initialization wizard functionality including:
- Configuration level mapping and validation
- Input validation functions
- INI file generation logic
"""

import pytest
from unittest.mock import patch, MagicMock
import os
import re
import configparser
from pathlib import Path


class TestConfigLevels:
    """Test configuration level mapping and validation."""

    def test_config_levels_constant(self):
        """Test CONFIG_LEVELS contains all required levels."""
        from gitwebhooks.cli.init_wizard import CONFIG_LEVELS

        assert 'system' in CONFIG_LEVELS
        assert 'local' in CONFIG_LEVELS
        assert 'user' in CONFIG_LEVELS

    def test_system_level_config(self):
        """Test system level has correct path and requires root."""
        from gitwebhooks.cli.init_wizard import CONFIG_LEVELS

        system = CONFIG_LEVELS['system']
        assert system['path'] == '/etc/gitwebhooks.ini'
        assert system['requires_root'] is True

    def test_local_level_config(self):
        """Test local level has correct path and requires root."""
        from gitwebhooks.cli.init_wizard import CONFIG_LEVELS

        local = CONFIG_LEVELS['local']
        assert local['path'] == '/usr/local/etc/gitwebhooks.ini'
        assert local['requires_root'] is True

    def test_user_level_config(self):
        """Test user level has correct path and does not require root."""
        from gitwebhooks.cli.init_wizard import CONFIG_LEVELS

        user = CONFIG_LEVELS['user']
        assert user['path'] == '~/.gitwebhooks.ini'
        assert user['requires_root'] is False

    def test_config_level_validation(self):
        """Test ConfigLevel data class validation."""
        from gitwebhooks.cli.init_wizard import ConfigLevel

        level = ConfigLevel(name='user', path='~/.gitwebhooks.ini', requires_root=False)
        assert level.name == 'user'
        assert level.path == '~/.gitwebhooks.ini'
        assert level.requires_root is False


class TestInputValidation:
    """Test input validation functions."""

    def test_validate_repo_name_valid(self):
        """Test validate_repo_name accepts valid formats."""
        from gitwebhooks.cli.init_wizard import validate_repo_name

        # Two-level format (GitHub/Gitee)
        assert validate_repo_name('owner/repo') is True
        assert validate_repo_name('username/project-name') is True
        assert validate_repo_name('owner/repo.git') is True

        # Multi-level format (GitLab)
        assert validate_repo_name('org/team/sub-project') is True
        assert validate_repo_name('group/subgroup/project') is True

        # Single-level format (now supported per spec)
        assert validate_repo_name('owner') is True
        assert validate_repo_name('myrepo') is True

    def test_validate_repo_name_invalid(self):
        """Test validate_repo_name rejects invalid formats."""
        from gitwebhooks.cli.init_wizard import validate_repo_name

        assert validate_repo_name('owner/') is False
        assert validate_repo_name('/repo') is False
        assert validate_repo_name('') is False
        assert validate_repo_name('https://github.com/owner/repo') is False
        assert validate_repo_name('owner//repo') is False
        assert validate_repo_name('owner repo') is False  # spaces not allowed

    def test_validate_existing_path_valid(self):
        """Test validate_existing_path accepts existing directories."""
        from gitwebhooks.cli.init_wizard import validate_existing_path

        # Test with /tmp which should always exist
        assert validate_existing_path('/tmp') is True

    def test_validate_existing_path_invalid(self):
        """Test validate_existing_path rejects non-existent paths."""
        from gitwebhooks.cli.init_wizard import validate_existing_path

        assert validate_existing_path('/nonexistent/path/that/does/not/exist') is False

    def test_validate_non_empty_valid(self):
        """Test validate_non_empty accepts non-empty strings."""
        from gitwebhooks.cli.init_wizard import validate_non_empty

        assert validate_non_empty('test') is True
        assert validate_non_empty('  test  ') is True

    def test_validate_non_empty_invalid(self):
        """Test validate_non_empty rejects empty strings."""
        from gitwebhooks.cli.init_wizard import validate_non_empty

        assert validate_non_empty('') is False
        assert validate_non_empty('   ') is False
        assert validate_non_empty('\n\t') is False

    def test_validate_port_valid(self):
        """Test validate_port accepts valid port numbers."""
        from gitwebhooks.cli.init_wizard import validate_port

        assert validate_port('1') is True
        assert validate_port('6789') is True
        assert validate_port('65535') is True

    def test_validate_port_invalid(self):
        """Test validate_port rejects invalid port numbers."""
        from gitwebhooks.cli.init_wizard import validate_port

        assert validate_port('0') is False
        assert validate_port('65536') is False
        assert validate_port('-1') is False
        assert validate_port('abc') is False
        assert validate_port('') is False


class TestPlatformConstants:
    """Test platform configuration constants."""

    def test_platforms_constant(self):
        """Test PLATFORMS contains all required platforms."""
        from gitwebhooks.cli.init_wizard import PLATFORMS

        assert 'github' in PLATFORMS
        assert 'gitee' in PLATFORMS
        assert 'gitlab' in PLATFORMS
        assert 'custom' in PLATFORMS

    def test_github_platform_events(self):
        """Test GitHub platform has correct events."""
        from gitwebhooks.cli.init_wizard import PLATFORMS

        github = PLATFORMS['github']
        assert 'push' in github['events']
        assert 'release' in github['events']
        assert github['requires_secret'] is True

    def test_gitee_platform_events(self):
        """Test Gitee platform has correct events."""
        from gitwebhooks.cli.init_wizard import PLATFORMS

        gitee = PLATFORMS['gitee']
        assert 'push' in gitee['events']
        assert 'release' in gitee['events']
        assert gitee['requires_secret'] is True

    def test_gitlab_platform_events(self):
        """Test GitLab platform has correct events."""
        from gitwebhooks.cli.init_wizard import PLATFORMS

        gitlab = PLATFORMS['gitlab']
        assert 'push' in gitlab['events']
        assert 'tag' in gitlab['events']
        assert gitlab['requires_secret'] is True

    def test_custom_platform_config(self):
        """Test custom platform has custom fields."""
        from gitwebhooks.cli.init_wizard import PLATFORMS

        custom = PLATFORMS['custom']
        assert 'custom_fields' in custom
        assert 'header_name' in custom['custom_fields']
        assert 'header_value' in custom['custom_fields']
        assert 'identifier_path' in custom['custom_fields']


class TestINIGeneration:
    """Test INI file generation logic."""

    def test_generate_server_section(self):
        """Test generating [server] section."""
        from gitwebhooks.cli.init_wizard import ServerConfig, _generate_config

        server = ServerConfig(address='0.0.0.0', port=6789, log_file='/var/log/test.log')
        platform = MagicMock()
        repo = MagicMock()

        config = _generate_config(server, platform, repo)

        assert config.has_section('server')
        assert config.get('server', 'address') == '0.0.0.0'
        assert config.get('server', 'port') == '6789'
        assert config.get('server', 'log_file') == '/var/log/test.log'

    def test_generate_github_section(self):
        """Test generating [github] section."""
        from gitwebhooks.cli.init_wizard import PlatformConfig, _generate_config

        server = MagicMock()
        platform = PlatformConfig(
            platform='github',
            handle_events='push,release',  # Changed from list to string
            verify=True,
            secret='test-secret',
            custom_params=None
        )
        repo = MagicMock()

        config = _generate_config(server, platform, repo)

        assert config.has_section('github')
        assert config.get('github', 'handle_events') == 'push,release'  # No spaces
        assert config.get('github', 'verify') == 'true'
        assert config.get('github', 'secret') == 'test-secret'

    def test_generate_repository_section(self):
        """Test generating repository section."""
        from gitwebhooks.cli.init_wizard import RepositoryConfig, _generate_config

        server = MagicMock()
        platform = MagicMock()
        repo = RepositoryConfig(
            name='owner/repo',
            cwd='/path/to/repo',
            cmd='git pull && ./deploy.sh'
        )

        config = _generate_config(server, platform, repo)

        # Section name no longer has 'repo/' prefix
        assert config.has_section('owner/repo')
        assert config.get('owner/repo', 'cwd') == '/path/to/repo'
        assert config.get('owner/repo', 'cmd') == 'git pull && ./deploy.sh'

    def test_generate_custom_platform_section(self):
        """Test generating [custom] section with custom parameters."""
        from gitwebhooks.cli.init_wizard import PlatformConfig, _generate_config

        server = MagicMock()
        platform = PlatformConfig(
            platform='custom',
            handle_events='webhook',  # Changed from list to string
            verify=False,
            secret=None,
            custom_params={
                'header_name': 'X-Webhook-Token',
                'header_value': 'my-token',
                'identifier_path': 'project.path',
                'header_event': 'X-Event'
            }
        )
        repo = MagicMock()

        config = _generate_config(server, platform, repo)

        assert config.has_section('custom')
        assert config.get('custom', 'header_name') == 'X-Webhook-Token'
        assert config.get('custom', 'header_value') == 'my-token'
        assert config.get('custom', 'identifier_path') == 'project.path'
        assert config.get('custom', 'header_event') == 'X-Event'


class TestDataClasses:
    """Test data class definitions."""

    def test_server_config_dataclass(self):
        """Test ServerConfig data class."""
        from gitwebhooks.cli.init_wizard import ServerConfig

        server = ServerConfig(
            address='127.0.0.1',
            port=8080,
            log_file='/tmp/test.log'
        )
        assert server.address == '127.0.0.1'
        assert server.port == 8080
        assert server.log_file == '/tmp/test.log'

    def test_platform_config_dataclass(self):
        """Test PlatformConfig data class."""
        from gitwebhooks.cli.init_wizard import PlatformConfig

        platform = PlatformConfig(
            platform='github',
            handle_events='push,release',  # Changed from list to string
            verify=True,
            secret='my-secret'
        )
        assert platform.platform == 'github'
        assert platform.handle_events == 'push,release'
        assert platform.verify is True
        assert platform.secret == 'my-secret'

    def test_repository_config_dataclass(self):
        """Test RepositoryConfig data class."""
        from gitwebhooks.cli.init_wizard import RepositoryConfig

        repo = RepositoryConfig(
            name='test/testing',
            cwd='/home/test/project',
            cmd='make deploy'
        )
        assert repo.name == 'test/testing'
        assert repo.cwd == '/home/test/project'
        assert repo.cmd == 'make deploy'
