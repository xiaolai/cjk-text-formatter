"""Configuration loading and management for text-formater."""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Try to import tomllib (Python 3.11+)
try:
    import tomllib
    TOMLLIB_AVAILABLE = True
except ImportError:
    TOMLLIB_AVAILABLE = False


# Default rule settings
DEFAULT_RULES = {
    # Original rules
    'ellipsis_normalization': True,
    'dash_conversion': True,
    'emdash_spacing': True,
    'quote_spacing': True,
    'single_quote_spacing': True,
    'cjk_english_spacing': True,
    'cjk_parenthesis_spacing': True,
    'space_collapsing': True,
    # New normalization rules
    'fullwidth_punctuation': True,
    'fullwidth_parentheses': True,
    'fullwidth_brackets': False,  # Optional, off by default
    'fullwidth_alphanumeric': True,
    # Cleanup rules
    'consecutive_punctuation_limit': 0,  # 0=unlimited, 1=single, 2=double
    'currency_spacing': True,
    'slash_spacing': True,
}


# Rule descriptions for documentation and --list-rules
RULE_DESCRIPTIONS = {
    'ellipsis_normalization': 'Convert spaced ellipsis to standard form (. . . → ...)',
    'dash_conversion': 'Convert dashes to Chinese em-dash between CJK text (2+ dashes → ——)',
    'emdash_spacing': 'Fix spacing around em-dash (text——more → text —— more)',
    'quote_spacing': 'Smart spacing around double quotes "" (avoids CJK punctuation)',
    'single_quote_spacing': 'Smart spacing around single quotes \'\' (avoids CJK punctuation)',
    'cjk_english_spacing': 'Add spaces between CJK and English/numbers (中文English → 中文 English)',
    'cjk_parenthesis_spacing': 'Add spaces between CJK and half-width parentheses (中文(test) → 中文 (test))',
    'space_collapsing': 'Collapse multiple spaces to single space (preserves indentation)',
    'fullwidth_punctuation': 'Normalize punctuation width based on context (,. → ，。 in CJK)',
    'fullwidth_parentheses': 'Convert () to （） in CJK context',
    'fullwidth_brackets': 'Convert [] to 【】 in CJK context',
    'fullwidth_alphanumeric': 'Convert full-width numbers/letters to half-width (１２３ → 123)',
    'consecutive_punctuation_limit': 'Limit consecutive punctuation (0=unlimited, 1=single, 2=double)',
    'currency_spacing': 'Remove space between currency symbols and amounts ($ 100 → $100)',
    'slash_spacing': 'Remove spaces around slashes (A / B → A/B, preserves URLs)',
}


@dataclass
class RuleConfig:
    """Configuration for formatting rules."""

    rules: dict[str, bool] = field(default_factory=lambda: DEFAULT_RULES.copy())
    custom_rules: list[dict[str, Any]] = field(default_factory=list)

    def is_enabled(self, rule_name: str) -> bool:
        """Check if a rule is enabled.

        Args:
            rule_name: Name of the rule to check

        Returns:
            True if rule is enabled, False otherwise
        """
        return self.rules.get(rule_name, True)

    def get_value(self, rule_name: str, default: Any = None) -> Any:
        """Get the value of a rule (for non-boolean rules).

        Args:
            rule_name: Name of the rule
            default: Default value if rule not found

        Returns:
            Rule value or default
        """
        return self.rules.get(rule_name, default)


def load_config(config_path: Path | None = None) -> RuleConfig:
    """Load configuration from file.

    Configuration priority (highest to lowest):
    1. config_path (if provided via --config flag)
    2. ./cjk-text-formatter.toml (project root)
    3. ~/.config/cjk-text-formatter.toml (user config)
    4. Default config (all rules enabled)

    Configs are merged: user config applied first, then project config overrides.

    Args:
        config_path: Optional explicit config file path

    Returns:
        RuleConfig instance with loaded configuration
    """
    if not TOMLLIB_AVAILABLE:
        # Fallback for Python <3.11
        # TODO: Could print warning to stderr
        return RuleConfig()

    # Start with defaults
    rules = DEFAULT_RULES.copy()
    custom_rules = []

    # Load user config first (if exists)
    user_config_path = Path.home() / ".config" / "cjk-text-formatter.toml"
    if user_config_path.exists():
        user_config = _load_toml_file(user_config_path)
        if user_config:
            _merge_config_data(rules, custom_rules, user_config)

    # Load project config (overrides user config)
    project_config_path = Path.cwd() / "cjk-text-formatter.toml"
    if project_config_path.exists():
        project_config = _load_toml_file(project_config_path)
        if project_config:
            _merge_config_data(rules, custom_rules, project_config)

    # Load explicit config path (highest priority)
    if config_path and config_path.exists():
        explicit_config = _load_toml_file(config_path)
        if explicit_config:
            _merge_config_data(rules, custom_rules, explicit_config)

    return RuleConfig(rules=rules, custom_rules=custom_rules)


def _load_toml_file(file_path: Path) -> dict[str, Any] | None:
    """Load and parse a TOML file.

    Args:
        file_path: Path to TOML file

    Returns:
        Parsed TOML data or None if loading fails
    """
    try:
        with open(file_path, 'rb') as f:
            return tomllib.load(f)
    except (FileNotFoundError, PermissionError, tomllib.TOMLDecodeError):
        # Expected errors - file doesn't exist, can't read, or invalid TOML
        return None
    except Exception as e:
        # Unexpected error - log for debugging but don't crash
        import sys
        print(f"Warning: Unexpected error loading config {file_path}: {e}", file=sys.stderr)
        return None


def _merge_config_data(rules: dict[str, bool], custom_rules: list, config_data: dict) -> None:
    """Merge config data into existing rules and custom_rules.

    Args:
        rules: Existing rules dict (modified in place)
        custom_rules: Existing custom rules list (modified in place)
        config_data: Config data to merge
    """
    # Merge rules
    if 'rules' in config_data:
        for key, value in config_data['rules'].items():
            if key in DEFAULT_RULES:  # Only accept known rules
                rules[key] = value

    # Merge custom rules
    if 'custom_rules' in config_data:
        custom_rules.extend(config_data['custom_rules'])


def merge_configs(base: RuleConfig, override: RuleConfig) -> RuleConfig:
    """Merge two configs with override taking precedence.

    Args:
        base: Base configuration
        override: Override configuration

    Returns:
        New RuleConfig with merged settings
    """
    merged_rules = base.rules.copy()
    merged_rules.update(override.rules)

    merged_custom_rules = base.custom_rules + override.custom_rules

    return RuleConfig(rules=merged_rules, custom_rules=merged_custom_rules)


@dataclass
class ValidationResult:
    """Result of config file validation."""

    config_path: Path
    is_valid: bool = True
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def format_report(self) -> str:
        """Format a human-readable validation report.

        Returns:
            Formatted validation report string
        """
        lines = [f"Validating: {self.config_path}"]
        lines.append("")

        if self.is_valid and not self.warnings:
            lines.append("✓ Configuration is valid")
        else:
            if self.errors:
                lines.append("Errors:")
                for error in self.errors:
                    lines.append(f"  ✗ {error}")
                lines.append("")

            if self.warnings:
                lines.append("Warnings:")
                for warning in self.warnings:
                    lines.append(f"  ⚠ {warning}")
                lines.append("")

            if not self.errors:
                lines.append("✓ Configuration is valid (with warnings)")

        return "\n".join(lines)


def validate_config(config_path: Path) -> ValidationResult:
    """Validate a configuration file.

    Checks:
    - File exists and is readable
    - Valid TOML syntax
    - Valid structure ([rules], [[custom_rules]])
    - Rule names match known built-in rules
    - Custom rules have required fields (name, pattern, replacement)
    - Regex patterns compile successfully

    Args:
        config_path: Path to config file to validate

    Returns:
        ValidationResult with validation details
    """
    result = ValidationResult(config_path=config_path)

    # Check Python version
    if not TOMLLIB_AVAILABLE:
        result.is_valid = False
        result.errors.append(
            "Config validation requires Python 3.11+ (tomllib not available)"
        )
        return result

    # Check if file exists
    if not config_path.exists():
        result.is_valid = False
        result.errors.append(f"Config file not found: {config_path}")
        return result

    # Check if file is readable
    if not config_path.is_file():
        result.is_valid = False
        result.errors.append(f"Path is not a file: {config_path}")
        return result

    # Try to load and parse TOML
    try:
        with open(config_path, 'rb') as f:
            config_data = tomllib.load(f)
    except PermissionError:
        result.is_valid = False
        result.errors.append(f"Cannot read file (permission denied): {config_path}")
        return result
    except tomllib.TOMLDecodeError as e:
        result.is_valid = False
        result.errors.append(f"TOML syntax error: {e}")
        return result
    except Exception as e:
        result.is_valid = False
        result.errors.append(f"Failed to load config: {e}")
        return result

    # Validate built-in rules section
    if 'rules' in config_data:
        if not isinstance(config_data['rules'], dict):
            result.is_valid = False
            result.errors.append("'rules' section must be a table/dict")
        else:
            # Check for unknown rule names
            for rule_name in config_data['rules']:
                if rule_name not in DEFAULT_RULES:
                    result.is_valid = False
                    result.errors.append(
                        f"Unknown rule name: '{rule_name}'. "
                        f"Valid rules: {', '.join(sorted(DEFAULT_RULES.keys()))}"
                    )

    # Validate custom rules section
    if 'custom_rules' in config_data:
        if not isinstance(config_data['custom_rules'], list):
            result.is_valid = False
            result.errors.append("'custom_rules' must be an array of tables")
        else:
            for i, rule in enumerate(config_data['custom_rules']):
                rule_id = f"custom_rules[{i}]"

                # Check required fields
                if 'name' not in rule:
                    result.is_valid = False
                    result.errors.append(f"{rule_id}: Missing required field 'name'")
                    continue  # Can't check other fields without name

                rule_name = rule.get('name', f'rule_{i}')

                if 'pattern' not in rule:
                    result.is_valid = False
                    result.errors.append(f"{rule_id} ({rule_name}): Missing required field 'pattern'")

                if 'replacement' not in rule:
                    result.is_valid = False
                    result.errors.append(f"{rule_id} ({rule_name}): Missing required field 'replacement'")

                # Validate regex pattern if present
                if 'pattern' in rule:
                    try:
                        re.compile(rule['pattern'])
                    except re.error as e:
                        result.is_valid = False
                        result.errors.append(
                            f"{rule_id} ({rule_name}): Invalid regex pattern: {e}"
                        )

    return result
