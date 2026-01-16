"""Unit tests for config level prompt functionality

Tests the ask_config_level() function in prompts.py.
"""

import pytest
from unittest.mock import patch
from io import StringIO

from gitwebhooks.cli.prompts import ask_config_level
from gitwebhooks.utils.constants import ConfigLevel


class TestAskConfigLevel:
    """Test ask_config_level function"""

    @patch('gitwebhooks.cli.prompts.input')
    def test_ask_config_level_user_choice(self, mock_input):
        """Test ask_config_level with user choice (1)"""
        mock_input.return_value = '1'

        result = ask_config_level()

        assert result == ConfigLevel.USER
        mock_input.assert_called_once()

    @patch('gitwebhooks.cli.prompts.input')
    def test_ask_config_level_local_choice(self, mock_input):
        """Test ask_config_level with local choice (2)"""
        mock_input.return_value = '2'

        result = ask_config_level()

        assert result == ConfigLevel.LOCAL

    @patch('gitwebhooks.cli.prompts.input')
    def test_ask_config_level_system_choice(self, mock_input):
        """Test ask_config_level with system choice (3)"""
        mock_input.return_value = '3'

        result = ask_config_level()

        assert result == ConfigLevel.SYSTEM

    @patch('gitwebhooks.cli.prompts.input')
    @patch('gitwebhooks.cli.prompts.print')
    def test_ask_config_level_default_choice(self, mock_print, mock_input):
        """Test ask_config_level with empty input (default to USER)"""
        mock_input.return_value = ''

        result = ask_config_level()

        assert result == ConfigLevel.USER

    @patch('gitwebhooks.cli.prompts.input')
    @patch('gitwebhooks.cli.prompts.print')
    def test_ask_config_level_invalid_then_valid(self, mock_print, mock_input):
        """Test ask_config_level with invalid input then valid"""
        mock_input.side_effect = ['invalid', '2']

        result = ask_config_level()

        assert result == ConfigLevel.LOCAL
        assert mock_input.call_count == 2

    @patch('gitwebhooks.cli.prompts.input')
    @patch('gitwebhooks.cli.prompts.ask_yes_no')
    @patch('gitwebhooks.cli.prompts.sys.exit')
    def test_ask_config_level_keyboard_interrupt_confirms(
        self, mock_exit, mock_yes_no, mock_input
    ):
        """Test ask_config_level with KeyboardInterrupt confirming exit"""
        mock_input.side_effect = KeyboardInterrupt()
        mock_yes_no.return_value = True

        ask_config_level()

        mock_exit.assert_called_once_with(0)

    @patch('gitwebhooks.cli.prompts.input')
    @patch('gitwebhooks.cli.prompts.ask_yes_no')
    def test_ask_config_level_keyboard_interrupt_cancels(
        self, mock_yes_no, mock_input
    ):
        """Test ask_config_level with KeyboardInterrupt canceling exit"""
        mock_input.side_effect = [KeyboardInterrupt(), '1']
        mock_yes_no.return_value = False

        result = ask_config_level()

        assert result == ConfigLevel.USER
        assert mock_input.call_count == 2


class TestAskConfigLevelOutput:
    """Test ask_config_level output messages"""

    @patch('gitwebhooks.cli.prompts.input')
    @patch('gitwebhooks.cli.prompts.print')
    def test_ask_config_level_shows_menu(self, mock_print, mock_input):
        """Test ask_config_level shows correct menu"""
        mock_input.return_value = '1'

        ask_config_level()

        # Get all print calls
        print_calls = [str(call) for call in mock_print.call_args_list]
        output = '\n'.join(print_calls)

        # Verify menu items
        assert 'Select configuration file level' in output
        assert 'User level' in output
        assert 'Local level' in output
        assert 'System level' in output
        assert '~/.gitwebhooks.ini' in output
        assert '/usr/local/etc/gitwebhooks.ini' in output
        assert '/etc/gitwebhooks.ini' in output

    @patch('gitwebhooks.cli.prompts.input')
    @patch('gitwebhooks.cli.prompts.print')
    def test_ask_config_level_shows_priority_info(self, mock_print, mock_input):
        """Test ask_config_level shows priority information"""
        mock_input.return_value = '1'

        ask_config_level()

        print_calls = [str(call) for call in mock_print.call_args_list]
        output = '\n'.join(print_calls)

        assert 'highest priority' in output
        assert 'medium priority' in output
        assert 'lowest priority' in output


class TestAskConfigLevelEdgeCases:
    """Test ask_config_level edge cases"""

    @patch('gitwebhooks.cli.prompts.input')
    @patch('gitwebhooks.cli.prompts.print')
    def test_ask_config_level_whitespace_input(self, mock_print, mock_input):
        """Test ask_config_level with whitespace input (should default)"""
        mock_input.return_value = '   '

        result = ask_config_level()

        assert result == ConfigLevel.USER

    @patch('gitwebhooks.cli.prompts.input')
    @patch('gitwebhooks.cli.prompts.print')
    def test_ask_config_level_multiple_invalid_then_valid(self, mock_print, mock_input):
        """Test ask_config_level with multiple invalid inputs"""
        mock_input.side_effect = ['abc', '999', 'x', '3']

        result = ask_config_level()

        assert result == ConfigLevel.SYSTEM
        assert mock_input.call_count == 4

    @patch('gitwebhooks.cli.prompts.input')
    @patch('gitwebhooks.cli.prompts.print')
    def test_ask_config_level_case_sensitive_numbers(self, mock_print, mock_input):
        """Test ask_config_level only accepts numeric choices"""
        mock_input.side_effect = ['one', 'two', '1']

        result = ask_config_level()

        assert result == ConfigLevel.USER
        assert mock_input.call_count == 3
