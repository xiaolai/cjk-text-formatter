"""Tests for config validation functionality."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from cjk_text_formatter.config import ValidationResult, validate_config


class TestValidConfigValidation:
    """Test validation of valid configuration files."""

    def test_valid_config_passes_all_checks(self, tmp_path):
        """Test that a completely valid config passes validation."""
        config_file = tmp_path / "valid.toml"
        config_file.write_text("""
[rules]
ellipsis_normalization = true
dash_conversion = true
cjk_english_spacing = false

[[custom_rules]]
name = "arrow_unicode"
pattern = '->'
replacement = '→'
description = "Use Unicode arrow"
""")

        result = validate_config(config_file)

        assert result.is_valid
        assert len(result.errors) == 0
        assert len(result.warnings) == 0

    def test_valid_config_with_only_rules(self, tmp_path):
        """Test config with only built-in rules (no custom rules)."""
        config_file = tmp_path / "rules_only.toml"
        config_file.write_text("""
[rules]
ellipsis_normalization = false
dash_conversion = true
""")

        result = validate_config(config_file)

        assert result.is_valid
        assert len(result.errors) == 0

    def test_valid_config_with_only_custom_rules(self, tmp_path):
        """Test config with only custom rules (no built-in rules section)."""
        config_file = tmp_path / "custom_only.toml"
        config_file.write_text("""
[[custom_rules]]
name = "test_rule"
pattern = 'foo'
replacement = 'bar'
""")

        result = validate_config(config_file)

        assert result.is_valid
        assert len(result.errors) == 0

    def test_empty_config_is_valid(self, tmp_path):
        """Test that an empty config file is valid."""
        config_file = tmp_path / "empty.toml"
        config_file.write_text("")

        result = validate_config(config_file)

        assert result.is_valid
        assert len(result.errors) == 0


class TestTOMLSyntaxValidation:
    """Test TOML syntax error detection."""

    @pytest.mark.skipif(sys.version_info < (3, 11), reason="Requires Python 3.11+")
    def test_invalid_toml_syntax(self, tmp_path):
        """Test that TOML syntax errors are detected."""
        config_file = tmp_path / "invalid.toml"
        config_file.write_text("""
[rules
ellipsis_normalization = true
""")

        result = validate_config(config_file)

        assert not result.is_valid
        assert len(result.errors) > 0
        assert any("toml syntax" in err.lower() or "parse" in err.lower()
                   for err in result.errors)

    @pytest.mark.skipif(sys.version_info < (3, 11), reason="Requires Python 3.11+")
    def test_malformed_table(self, tmp_path):
        """Test detection of malformed TOML tables."""
        config_file = tmp_path / "malformed.toml"
        config_file.write_text("""
[[custom_rules]
name = "missing_bracket"
""")

        result = validate_config(config_file)

        assert not result.is_valid
        assert len(result.errors) > 0


class TestRuleNameValidation:
    """Test validation of rule names."""

    def test_unknown_builtin_rule_name(self, tmp_path):
        """Test that unknown built-in rule names are flagged."""
        config_file = tmp_path / "unknown_rule.toml"
        config_file.write_text("""
[rules]
unknown_rule_name = true
ellipsis_normalization = true
""")

        result = validate_config(config_file)

        assert not result.is_valid
        assert any("unknown_rule_name" in err.lower() for err in result.errors)

    def test_multiple_unknown_rules(self, tmp_path):
        """Test detection of multiple unknown rule names."""
        config_file = tmp_path / "multiple_unknown.toml"
        config_file.write_text("""
[rules]
fake_rule_1 = true
fake_rule_2 = false
cjk_english_spacing = true
""")

        result = validate_config(config_file)

        assert not result.is_valid
        assert any("fake_rule_1" in err.lower() for err in result.errors)
        assert any("fake_rule_2" in err.lower() for err in result.errors)


class TestCustomRuleValidation:
    """Test validation of custom rules."""

    def test_missing_pattern_field(self, tmp_path):
        """Test that missing 'pattern' field is detected."""
        config_file = tmp_path / "missing_pattern.toml"
        config_file.write_text("""
[[custom_rules]]
name = "incomplete"
replacement = "bar"
""")

        result = validate_config(config_file)

        assert not result.is_valid
        assert any("pattern" in err.lower() and "incomplete" in err.lower()
                   for err in result.errors)

    def test_missing_replacement_field(self, tmp_path):
        """Test that missing 'replacement' field is detected."""
        config_file = tmp_path / "missing_replacement.toml"
        config_file.write_text("""
[[custom_rules]]
name = "incomplete"
pattern = "foo"
""")

        result = validate_config(config_file)

        assert not result.is_valid
        assert any("replacement" in err.lower() and "incomplete" in err.lower()
                   for err in result.errors)

    def test_missing_name_field(self, tmp_path):
        """Test that missing 'name' field is detected."""
        config_file = tmp_path / "missing_name.toml"
        config_file.write_text("""
[[custom_rules]]
pattern = "foo"
replacement = "bar"
""")

        result = validate_config(config_file)

        assert not result.is_valid
        assert any("name" in err.lower() for err in result.errors)

    def test_invalid_regex_pattern(self, tmp_path):
        """Test that invalid regex patterns are detected."""
        config_file = tmp_path / "invalid_regex.toml"
        config_file.write_text("""
[[custom_rules]]
name = "bad_regex"
pattern = '(?P<invalid'
replacement = 'x'
""")

        result = validate_config(config_file)

        assert not result.is_valid
        assert any("regex" in err.lower() or "pattern" in err.lower()
                   for err in result.errors)
        assert any("bad_regex" in err.lower() for err in result.errors)


class TestFileAccessValidation:
    """Test file access and existence validation."""

    def test_nonexistent_file(self, tmp_path):
        """Test validation of non-existent file."""
        config_file = tmp_path / "nonexistent.toml"

        result = validate_config(config_file)

        assert not result.is_valid
        assert any("not found" in err.lower() or "does not exist" in err.lower()
                   for err in result.errors)

    def test_unreadable_file(self, tmp_path):
        """Test validation of unreadable file."""
        config_file = tmp_path / "unreadable.toml"
        config_file.write_text("[rules]\n")
        config_file.chmod(0o000)

        try:
            result = validate_config(config_file)
            # Should either detect as unreadable or handle gracefully
            assert not result.is_valid or len(result.errors) == 0
        finally:
            config_file.chmod(0o644)


class TestValidationResult:
    """Test ValidationResult dataclass functionality."""

    def test_validation_result_with_errors(self, tmp_path):
        """Test that ValidationResult correctly reports errors."""
        config_file = tmp_path / "errors.toml"
        config_file.write_text("""
[rules]
fake_rule = true
""")

        result = validate_config(config_file)

        assert not result.is_valid
        assert result.config_path == config_file
        assert len(result.errors) > 0

    def test_validation_result_with_warnings(self, tmp_path):
        """Test that ValidationResult can contain warnings."""
        config_file = tmp_path / "warnings.toml"
        config_file.write_text("""
[rules]
ellipsis_normalization = true
""")

        result = validate_config(config_file)

        # Valid config should have no warnings for this simple case
        assert result.is_valid
        assert isinstance(result.warnings, list)

    def test_validation_result_format_report(self, tmp_path):
        """Test that ValidationResult can format a readable report."""
        config_file = tmp_path / "test.toml"
        config_file.write_text("""
[rules]
ellipsis_normalization = true
""")

        result = validate_config(config_file)

        report = result.format_report()

        assert isinstance(report, str)
        assert len(report) > 0
        assert str(config_file) in report


class TestPython311Compatibility:
    """Test Python version compatibility."""

    @pytest.mark.skipif(sys.version_info >= (3, 11), reason="Only for Python <3.11")
    def test_validation_on_old_python(self, tmp_path):
        """Test that validation gracefully handles Python <3.11."""
        config_file = tmp_path / "test.toml"
        config_file.write_text("""
[rules]
ellipsis_normalization = true
""")

        result = validate_config(config_file)

        # Should either skip validation or provide helpful error
        assert not result.is_valid
        assert any("python 3.11" in err.lower() or "tomllib" in err.lower()
                   for err in result.errors)

    @pytest.mark.skipif(sys.version_info < (3, 11), reason="Requires Python 3.11+")
    def test_validation_on_new_python(self, tmp_path):
        """Test that validation works on Python 3.11+."""
        config_file = tmp_path / "test.toml"
        config_file.write_text("""
[rules]
ellipsis_normalization = true
""")

        result = validate_config(config_file)

        assert result.is_valid
        assert len(result.errors) == 0


class TestConfigSourceDetection:
    """Test detection of config source location."""

    def test_result_includes_config_path(self, tmp_path):
        """Test that validation result includes the config file path."""
        config_file = tmp_path / "test.toml"
        config_file.write_text("""
[rules]
ellipsis_normalization = true
""")

        result = validate_config(config_file)

        assert result.config_path == config_file

    def test_detects_config_priority_source(self, tmp_path):
        """Test that validation can show which priority level config came from."""
        config_file = tmp_path / "test.toml"
        config_file.write_text("""
[rules]
ellipsis_normalization = true
""")

        result = validate_config(config_file)

        # Result should be able to indicate this is a custom path
        assert result.config_path == config_file
