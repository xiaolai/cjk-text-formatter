"""Tests for polish functions with configuration."""

from __future__ import annotations

import pytest

from cjk_text_formatter.config import RuleConfig
from cjk_text_formatter.polish import polish_text, polish_text_verbose


class TestPolishWithDisabledRules:
    """Test that disabled rules are not applied."""

    def test_polish_with_dash_conversion_disabled(self):
        """Test that dash conversion doesn't run when disabled."""
        config = RuleConfig(rules={'dash_conversion': False})

        text = "文本--测试"
        result = polish_text(text, config=config)

        # Dash should NOT be converted
        assert result == "文本--测试"

    def test_polish_with_cjk_spacing_disabled(self):
        """Test that CJK-English spacing doesn't run when disabled."""
        config = RuleConfig(rules={'cjk_english_spacing': False})

        text = "文本English"
        result = polish_text(text, config=config)

        # No space should be added
        assert result == "文本English"

    def test_polish_with_ellipsis_disabled(self):
        """Test that ellipsis normalization doesn't run when disabled."""
        config = RuleConfig(rules={'ellipsis_normalization': False})

        text = "wait . . . more"
        result = polish_text(text, config=config)

        # Ellipsis should NOT be normalized
        assert result == "wait . . . more"

    def test_polish_with_quote_spacing_disabled(self):
        """Test that quote spacing doesn't run when disabled."""
        config = RuleConfig(rules={'quote_spacing': False})

        text = '文本"quoted"内容'
        result = polish_text(text, config=config)

        # No spaces around quotes
        assert result == '文本"quoted"内容'

    def test_polish_with_multiple_rules_disabled(self):
        """Test disabling multiple rules at once."""
        config = RuleConfig(rules={
            'dash_conversion': False,
            'cjk_english_spacing': False,
        })

        text = "文本--English混合"
        result = polish_text(text, config=config)

        # Neither dash conversion nor spacing should happen
        assert result == "文本--English混合"


class TestPolishWithCustomRules:
    """Test custom regex rules execution."""

    def test_single_custom_rule(self):
        """Test applying a single custom regex rule."""
        config = RuleConfig(custom_rules=[
            {
                'name': 'arrow_unicode',
                'pattern': '->',
                'replacement': '→',
                'description': 'Use Unicode arrow'
            }
        ])

        text = "A -> B"
        result = polish_text(text, config=config)

        assert result == "A → B"

    def test_multiple_custom_rules(self):
        """Test applying multiple custom regex rules."""
        config = RuleConfig(custom_rules=[
            {
                'name': 'arrow_unicode',
                'pattern': '->',
                'replacement': '→',
            },
            {
                'name': 'multiply_sign',
                'pattern': r'(\d+)\s*x\s*(\d+)',
                'replacement': r'\1×\2',
            }
        ])

        text = "A -> B and 3 x 4"
        result = polish_text(text, config=config)

        assert result == "A → B and 3×4"

    def test_custom_rule_with_builtin_disabled(self):
        """Test custom rules still work when built-in rules are disabled."""
        config = RuleConfig(
            rules={'cjk_english_spacing': False},
            custom_rules=[
                {
                    'name': 'arrow_fix',
                    'pattern': '->',
                    'replacement': '→',
                }
            ]
        )

        text = "文本English -> test"
        result = polish_text(text, config=config)

        # CJK spacing disabled, but custom rule applies
        assert result == "文本English → test"

    def test_custom_rule_order_after_builtins(self):
        """Test that custom rules run after built-in rules."""
        config = RuleConfig(
            rules={'cjk_english_spacing': True},
            custom_rules=[
                {
                    'name': 'space_to_underscore',
                    'pattern': r' ',
                    'replacement': '_',
                }
            ]
        )

        text = "文本English"
        result = polish_text(text, config=config)

        # First CJK spacing adds space: "文本 English"
        # Then custom rule replaces space with underscore
        assert result == "文本_English"


class TestPolishVerboseWithConfig:
    """Test verbose mode with configuration."""

    def test_verbose_tracks_disabled_rules(self):
        """Test that verbose mode correctly reports when rules are disabled."""
        config = RuleConfig(rules={'dash_conversion': False})

        text = "文本English测试"
        result, stats = polish_text_verbose(text, config=config)

        # Dash conversion disabled (no dashes in text anyway)
        assert stats.dash_converted == 0
        # CJK spacing still enabled - should add space between 文本 and English
        assert stats.cjk_english_spacing_added > 0

    def test_verbose_tracks_custom_rules(self):
        """Test that verbose mode tracks custom rule applications."""
        config = RuleConfig(custom_rules=[
            {
                'name': 'arrow_fix',
                'pattern': '->',
                'replacement': '→',
            }
        ])

        text = "A -> B -> C"
        result, stats = polish_text_verbose(text, config=config)

        # Should track custom rule applications
        assert hasattr(stats, 'custom_rules_applied')
        assert stats.custom_rules_applied['arrow_fix'] == 2

    def test_verbose_summary_includes_custom_rules(self):
        """Test that verbose summary includes custom rule stats."""
        config = RuleConfig(custom_rules=[
            {
                'name': 'arrow_fix',
                'pattern': '->',
                'replacement': '→',
            }
        ])

        text = "A -> B"
        result, stats = polish_text_verbose(text, config=config)

        summary = stats.format_summary()
        assert 'arrow_fix' in summary or 'custom' in summary.lower()


class TestConfigNoneDefault:
    """Test that config=None uses default behavior (all rules enabled)."""

    def test_polish_without_config_uses_defaults(self):
        """Test that passing config=None enables all rules (backward compat)."""
        text = "文本English混合"
        result = polish_text(text, config=None)

        # All default rules should apply
        assert "文本 English 混合" == result

    def test_polish_without_config_parameter(self):
        """Test calling polish_text() without config parameter works."""
        text = "文本--内容 and English"
        result = polish_text(text)  # No config parameter

        # Should use defaults (all rules enabled)
        assert "——" in result  # Dash converts between CJK
        assert "文本 —— 内容" in result  # Check dash conversion
        assert " English" in result  # CJK spacing with English


class TestInvalidCustomRules:
    """Test error handling for invalid custom rules."""

    def test_invalid_regex_pattern(self):
        """Test that invalid regex patterns are handled gracefully (skipped)."""
        config = RuleConfig(custom_rules=[
            {
                'name': 'bad_rule',
                'pattern': '(?P<invalid',  # Invalid regex
                'replacement': 'x',
            }
        ])

        text = "test"

        # Should not crash - just skip the invalid rule
        result = polish_text(text, config=config)
        assert result == "test"  # Text unchanged since rule was skipped

    def test_missing_required_fields(self):
        """Test that custom rules with missing fields are handled gracefully (skipped)."""
        config = RuleConfig(custom_rules=[
            {
                'name': 'incomplete',
                # Missing 'pattern' and 'replacement'
            }
        ])

        text = "test"

        # Should not crash - just skip the invalid rule
        result = polish_text(text, config=config)
        assert result == "test"  # Text unchanged since rule was skipped
