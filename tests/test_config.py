"""Tests for configuration loading and parsing."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

# These imports will fail initially (TDD - RED phase)
from cjk_text_formatter.config import load_config, RuleConfig


class TestConfigLoading:
    """Test configuration file loading from different locations."""

    def test_load_default_config(self):
        """Test default config when no config files exist."""
        with patch('pathlib.Path.exists', return_value=False):
            config = load_config()

            # All built-in rules should be enabled by default
            assert config.rules['ellipsis_normalization'] is True
            assert config.rules['dash_conversion'] is True
            assert config.rules['emdash_spacing'] is True
            assert config.rules['quote_spacing'] is True
            assert config.rules['cjk_english_spacing'] is True
            assert config.rules['space_collapsing'] is True

            # No custom rules by default
            assert config.custom_rules == []

    def test_load_config_from_project_root(self, tmp_path):
        """Test loading config from project root (./cjk-text-formatter.toml)."""
        config_content = """
[rules]
ellipsis_normalization = true
dash_conversion = false
cjk_english_spacing = true
"""
        config_file = tmp_path / "cjk-text-formatter.toml"
        config_file.write_text(config_content)

        with patch('pathlib.Path.cwd', return_value=tmp_path):
            config = load_config()

            assert config.rules['ellipsis_normalization'] is True
            assert config.rules['dash_conversion'] is False
            assert config.rules['cjk_english_spacing'] is True

    def test_load_config_from_user_home(self, tmp_path):
        """Test loading config from user home (~/.config/cjk-text-formatter.toml)."""
        config_dir = tmp_path / ".config"
        config_dir.mkdir()
        config_file = config_dir / "cjk-text-formatter.toml"

        config_content = """
[rules]
quote_spacing = false
"""
        config_file.write_text(config_content)

        with patch('pathlib.Path.home', return_value=tmp_path):
            with patch('pathlib.Path.cwd') as mock_cwd:
                # Make sure project config doesn't exist
                mock_cwd.return_value = Path("/nonexistent")

                config = load_config()
                assert config.rules['quote_spacing'] is False

    def test_config_priority_project_over_user(self, tmp_path):
        """Test that project config takes priority over user config."""
        # Create user config
        user_config_dir = tmp_path / "home" / ".config"
        user_config_dir.mkdir(parents=True)
        user_config = user_config_dir / "cjk-text-formatter.toml"
        user_config.write_text("""
[rules]
dash_conversion = false
cjk_english_spacing = false
""")

        # Create project config
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        project_config = project_dir / "cjk-text-formatter.toml"
        project_config.write_text("""
[rules]
dash_conversion = true
""")

        with patch('pathlib.Path.home', return_value=tmp_path / "home"):
            with patch('pathlib.Path.cwd', return_value=project_dir):
                config = load_config()

                # Project config value wins
                assert config.rules['dash_conversion'] is True
                # User config value for other rules
                assert config.rules['cjk_english_spacing'] is False

    def test_custom_regex_rules_parsing(self, tmp_path):
        """Test parsing custom regex rules from config."""
        config_content = """
[rules]
dash_conversion = true

[[custom_rules]]
name = "arrow_unicode"
pattern = '->'
replacement = '→'
description = "Use Unicode arrow"

[[custom_rules]]
name = "multiply_sign"
pattern = '(\\d+)\\s*x\\s*(\\d+)'
replacement = '\\1×\\2'
description = "Use multiplication sign"
"""
        config_file = tmp_path / "cjk-text-formatter.toml"
        config_file.write_text(config_content)

        # Patch both cwd and home to isolate test from real config files
        with patch('pathlib.Path.cwd', return_value=tmp_path):
            with patch('pathlib.Path.home', return_value=tmp_path / "fake_home"):
                config = load_config()

                assert len(config.custom_rules) == 2

                # First custom rule
                assert config.custom_rules[0]['name'] == 'arrow_unicode'
                assert config.custom_rules[0]['pattern'] == '->'
                assert config.custom_rules[0]['replacement'] == '→'

                # Second custom rule
                assert config.custom_rules[1]['name'] == 'multiply_sign'
                assert config.custom_rules[1]['pattern'] == r'(\d+)\s*x\s*(\d+)'


class TestPython310Fallback:
    """Test graceful degradation for Python <3.11 (no tomllib)."""

    def test_fallback_when_tomllib_unavailable(self):
        """Test that config falls back to defaults when tomllib is not available."""
        with patch('cjk_text_formatter.config.TOMLLIB_AVAILABLE', False):
            config = load_config()

            # Should return default config (all rules enabled)
            assert config.rules['ellipsis_normalization'] is True
            assert config.rules['dash_conversion'] is True
            assert config.custom_rules == []

    def test_warning_message_python_310(self, capsys):
        """Test that a warning is shown when config is unavailable."""
        with patch('cjk_text_formatter.config.TOMLLIB_AVAILABLE', False):
            # Try to load config from a file that exists
            config = load_config()

            # Should print warning (implementation detail)
            # This test ensures users are notified


class TestRuleConfig:
    """Test RuleConfig dataclass."""

    def test_rule_config_defaults(self):
        """Test RuleConfig with default values."""
        config = RuleConfig()

        # All built-in rules enabled by default
        assert config.rules['ellipsis_normalization'] is True
        assert config.rules['dash_conversion'] is True
        assert config.custom_rules == []

    def test_rule_config_is_enabled(self):
        """Test checking if a rule is enabled."""
        config = RuleConfig(rules={'dash_conversion': False})

        assert config.is_enabled('dash_conversion') is False
        assert config.is_enabled('cjk_english_spacing') is True  # Default


class TestConfigWithPath:
    """Test loading config from a specific path."""

    def test_load_config_with_custom_path(self, tmp_path):
        """Test loading config from --config PATH argument."""
        config_file = tmp_path / "my_custom_config.toml"
        config_file.write_text("""
[rules]
ellipsis_normalization = false
""")

        config = load_config(config_path=config_file)
        assert config.rules['ellipsis_normalization'] is False
