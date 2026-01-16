"""Unit tests for ConfigLevel enum and related functionality

Tests the configuration file level enumeration and utility functions.
"""

import pytest
from pathlib import Path

from gitwebhooks.utils.constants import ConfigLevel


class TestConfigLevelEnum:
    """Test ConfigLevel enumeration"""

    def test_config_level_values(self):
        """Test ConfigLevel has correct values"""
        assert ConfigLevel.USER.value == "user"
        assert ConfigLevel.LOCAL.value == "local"
        assert ConfigLevel.SYSTEM.value == "system"

    def test_config_level_get_config_path_user(self):
        """Test get_config_path() returns correct path for USER level"""
        path = ConfigLevel.USER.get_config_path()
        assert path == Path("~/.gitwebhooks.ini").expanduser()

    def test_config_level_get_config_path_local(self):
        """Test get_config_path() returns correct path for LOCAL level"""
        path = ConfigLevel.LOCAL.get_config_path()
        assert path == Path("/usr/local/etc/gitwebhooks.ini")

    def test_config_level_get_config_path_system(self):
        """Test get_config_path() returns correct path for SYSTEM level"""
        path = ConfigLevel.SYSTEM.get_config_path()
        assert path == Path("/etc/gitwebhooks.ini")

    def test_config_level_paths_are_absolute(self):
        """Test all config level paths are absolute"""
        for level in ConfigLevel:
            path = level.get_config_path()
            assert path.is_absolute()


class TestConfigLevelFromString:
    """Test ConfigLevel.from_string() class method"""

    def test_from_string_user_lowercase(self):
        """Test from_string() with lowercase 'user'"""
        level = ConfigLevel.from_string("user")
        assert level == ConfigLevel.USER

    def test_from_string_user_uppercase(self):
        """Test from_string() with uppercase 'USER'"""
        level = ConfigLevel.from_string("USER")
        assert level == ConfigLevel.USER

    def test_from_string_user_mixed_case(self):
        """Test from_string() with mixed case 'UsEr'"""
        level = ConfigLevel.from_string("UsEr")
        assert level == ConfigLevel.USER

    def test_from_string_local(self):
        """Test from_string() with 'local'"""
        level = ConfigLevel.from_string("local")
        assert level == ConfigLevel.LOCAL

    def test_from_string_system(self):
        """Test from_string() with 'system'"""
        level = ConfigLevel.from_string("system")
        assert level == ConfigLevel.SYSTEM

    def test_from_string_invalid_raises_error(self):
        """Test from_string() raises ValueError for invalid input"""
        with pytest.raises(ValueError) as exc_info:
            ConfigLevel.from_string("invalid")

        assert "Invalid config level 'invalid'" in str(exc_info.value)
        assert "user, local, system" in str(exc_info.value)

    def test_from_string_empty_raises_error(self):
        """Test from_string() raises ValueError for empty input"""
        with pytest.raises(ValueError) as exc_info:
            ConfigLevel.from_string("")

        assert "Invalid config level" in str(exc_info.value)


class TestConfigLevelPriority:
    """Test config level priority order"""

    def test_config_level_iteration_order(self):
        """Test ConfigLevel enum iteration follows priority order"""
        levels = list(ConfigLevel)
        assert levels[0] == ConfigLevel.USER
        assert levels[1] == ConfigLevel.LOCAL
        assert levels[2] == ConfigLevel.SYSTEM

    def test_user_level_has_highest_priority(self):
        """Test USER level has highest priority (appears first)"""
        levels = list(ConfigLevel)
        assert levels[0] == ConfigLevel.USER

    def test_system_level_has_lowest_priority(self):
        """Test SYSTEM level has lowest priority (appears last)"""
        levels = list(ConfigLevel)
        assert levels[-1] == ConfigLevel.SYSTEM
