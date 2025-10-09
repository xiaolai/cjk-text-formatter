"""Text polishing functions for Chinese typography."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .config import RuleConfig

# Regular expressions
CHINESE_RE = re.compile(r"[\u4e00-\u9fff]")


@dataclass
class PolishStats:
    """Statistics about text polishing operations."""

    ellipsis_normalized: int = 0
    dash_converted: int = 0
    emdash_spacing_fixed: int = 0
    quote_spacing_fixed: int = 0
    cjk_english_spacing_added: int = 0
    spaces_collapsed: int = 0
    custom_rules_applied: dict[str, int] = field(default_factory=dict)

    def has_changes(self) -> bool:
        """Check if any changes were made."""
        return any([
            self.ellipsis_normalized,
            self.dash_converted,
            self.emdash_spacing_fixed,
            self.quote_spacing_fixed,
            self.cjk_english_spacing_added,
            self.spaces_collapsed,
            bool(self.custom_rules_applied),
        ])

    def format_summary(self) -> str:
        """Format a human-readable summary of changes."""
        changes = []
        if self.ellipsis_normalized:
            changes.append(f"{self.ellipsis_normalized} ellipsis normalized")
        if self.dash_converted:
            changes.append(f"{self.dash_converted} em-dash converted")
        if self.emdash_spacing_fixed:
            changes.append(f"{self.emdash_spacing_fixed} em-dash spacing fixed")
        if self.quote_spacing_fixed:
            changes.append(f"{self.quote_spacing_fixed} quote spacing fixed")
        if self.cjk_english_spacing_added:
            changes.append(f"{self.cjk_english_spacing_added} CJK-English spacing added")
        if self.spaces_collapsed:
            changes.append(f"{self.spaces_collapsed} spaces collapsed")

        # Add custom rule stats
        for rule_name, count in self.custom_rules_applied.items():
            if count > 0:
                changes.append(f"{count} {rule_name} applied")

        if not changes:
            return "No changes made"

        return "Changes: " + ", ".join(changes)


def contains_chinese(text: str) -> bool:
    """Check if text contains any Chinese characters.

    Args:
        text: Text to check

    Returns:
        True if text contains Chinese characters, False otherwise
    """
    return bool(CHINESE_RE.search(text))


def _normalize_ellipsis(text: str) -> str:
    """Normalize spaced ellipsis patterns to standard ellipsis.

    Handles patterns like ". . ." or ". . . ." that might appear in AI translations.
    This is a universal rule applied to all languages.

    Args:
        text: Text to normalize

    Returns:
        Text with normalized ellipsis
    """
    # Replace spaced dots (. . . or . . . .) with standard ellipsis
    # Also remove space before if pattern starts with space
    text = re.sub(r"\s*\.\s+\.\s+\.(?:\s+\.)*", "...", text)
    # Ensure exactly one space after ellipsis when followed by non-whitespace
    text = re.sub(r"\.\.\.\s*(?=\S)", "... ", text)
    return text


def _replace_dash(text: str) -> str:
    """Convert -- to —— with proper spacing.

    Rules:
    - No space between closing quotes/parens (》）) and ——
    - No space between —— and opening quotes/parens (《（)
    - Regular text gets spaces on both sides

    Args:
        text: Text to process

    Returns:
        Text with -- converted to —— with proper spacing
    """
    def repl(match: re.Match[str]) -> str:
        before = match.group(1)
        after = match.group(2)
        # No space between closing quotes/parens and ——
        left_space = "" if before in ("）", "》") else " "
        # No space between —— and opening quotes/parens
        right_space = "" if after in ("（", "《") else " "
        return f"{before}{left_space}——{right_space}{after}"

    return re.sub(r"([^\s])--([^\s])", repl, text)


def _fix_emdash_spacing(text: str) -> str:
    """Fix spacing around existing —— (em-dash) characters.

    Rules:
    - No space between closing quotes/parens (》）) and ——
    - No space between —— and opening quotes/parens (《（)
    - Regular text gets spaces on both sides

    Args:
        text: Text to process

    Returns:
        Text with corrected em-dash spacing
    """
    def repl(match: re.Match[str]) -> str:
        before = match.group(1)
        after = match.group(2)
        # No space between closing quotes/parens and ——
        left_space = "" if before in ("）", "》") else " "
        # No space between —— and opening quotes/parens
        right_space = "" if after in ("（", "《") else " "
        return f"{before}{left_space}——{right_space}{after}"

    return re.sub(r"([^\s])\s*——\s*([^\s])", repl, text)


def _fix_quotes(text: str) -> str:
    """Fix spacing around Chinese quotation marks "".

    Rules:
    - Add space before opening quote " if preceded by alphanumeric or Chinese
    - Add space after closing quote " if followed by alphanumeric or Chinese

    Args:
        text: Text to process

    Returns:
        Text with corrected quotation mark spacing
    """
    # U+201C: " (LEFT DOUBLE QUOTATION MARK)
    # U+201D: " (RIGHT DOUBLE QUOTATION MARK)
    opening_quote = '\u201c'
    closing_quote = '\u201d'

    # Add space before opening quote "
    text = re.sub(f'([A-Za-z0-9\u4e00-\u9fff]){opening_quote}', f'\\1 {opening_quote}', text)
    # Add space after closing quote "
    text = re.sub(f'{closing_quote}([A-Za-z0-9\u4e00-\u9fff])', f'{closing_quote} \\1', text)
    return text


def _space_between(text: str) -> str:
    """Add spaces between Chinese and English/numbers.

    Rules:
    - Add space between Chinese characters and English letters
    - Add space between Chinese characters and numbers (with units like %, °C, etc.)

    Args:
        text: Text to process

    Returns:
        Text with spaces added between Chinese and alphanumerics
    """
    # Pattern for numbers with optional measurement units
    # Supports: 5%, 25°C, 25°c, 45°, 3‰, 25℃, etc.
    num_pattern = r"[A-Za-z0-9]+(?:[%‰℃℉]|°[CcFf]?)?"

    # Chinese followed by alphanumeric (with optional unit)
    text = re.sub(f"([\u4e00-\u9fff])({num_pattern})", r"\1 \2", text)
    # Alphanumeric (with optional unit) followed by Chinese
    text = re.sub(f"({num_pattern})([\u4e00-\u9fff])", r"\1 \2", text)
    return text


def polish_text(text: str, config: RuleConfig | None = None) -> str:
    """Polish text with typography rules.

    Universal rules (all languages):
    - Normalize ellipsis patterns (. . . → ...)

    Chinese-specific rules:
    - Convert -- to —— with proper spacing
    - Fix spacing around existing ——
    - Fix spacing around Chinese quotes ""
    - Add spaces between Chinese and English/numbers
    - Collapse multiple consecutive spaces

    Args:
        text: Text to polish
        config: Optional configuration for rule toggling

    Returns:
        Polished text with typography rules applied
    """
    # If no config, create default (all rules enabled)
    if config is None:
        from .config import RuleConfig
        config = RuleConfig()

    # Universal normalization (applies to all languages)
    if config.is_enabled('ellipsis_normalization'):
        text = _normalize_ellipsis(text)

    # Chinese-specific polishing
    if contains_chinese(text):
        if config.is_enabled('dash_conversion'):
            text = _replace_dash(text)
        if config.is_enabled('emdash_spacing'):
            text = _fix_emdash_spacing(text)
        if config.is_enabled('quote_spacing'):
            text = _fix_quotes(text)
        if config.is_enabled('cjk_english_spacing'):
            text = _space_between(text)

        # Collapse multiple spaces to single space
        if config.is_enabled('space_collapsing'):
            text = re.sub(r"\s{2,}", " ", text)

    # Apply custom regex rules
    text = _apply_custom_rules(text, config.custom_rules)

    return text.strip()


def _apply_custom_rules(text: str, custom_rules: list) -> str:
    """Apply custom regex rules to text.

    Args:
        text: Text to process
        custom_rules: List of custom rule dicts with 'pattern' and 'replacement'

    Returns:
        Text with custom rules applied
    """
    for rule in custom_rules:
        try:
            pattern = rule['pattern']
            replacement = rule['replacement']
            text = re.sub(pattern, replacement, text)
        except (KeyError, re.error):
            # Skip invalid rules
            continue

    return text


def polish_text_verbose(text: str, config: RuleConfig | None = None) -> tuple[str, PolishStats]:
    """Polish text with typography rules and return statistics.

    Args:
        text: Text to polish
        config: Optional configuration for rule toggling

    Returns:
        Tuple of (polished text, statistics)
    """
    # If no config, create default (all rules enabled)
    if config is None:
        from .config import RuleConfig
        config = RuleConfig()

    stats = PolishStats()
    original = text

    # Universal normalization - count ellipsis patterns
    if config.is_enabled('ellipsis_normalization'):
        ellipsis_pattern = re.compile(r"\s*\.\s+\.\s+\.(?:\s+\.)*")
        stats.ellipsis_normalized = len(ellipsis_pattern.findall(text))
        text = _normalize_ellipsis(text)

    # Chinese-specific polishing
    if contains_chinese(text):
        # Count dash conversions (-- to ——)
        if config.is_enabled('dash_conversion'):
            dash_pattern = re.compile(r"([^\s])--([^\s])")
            stats.dash_converted = len(dash_pattern.findall(text))
            text = _replace_dash(text)

        # Count em-dash spacing fixes
        if config.is_enabled('emdash_spacing'):
            emdash_spacing_pattern = re.compile(r"([^\s])\s*——\s*([^\s])")
            matches = emdash_spacing_pattern.findall(text)
            # Only count if spacing is actually wrong
            temp_text = text
            for before, after in matches:
                left_space = "" if before in ("）", "》") else " "
                right_space = "" if after in ("（", "《") else " "
                correct = f"{before}{left_space}——{right_space}{after}"
                # Check if current version doesn't match correct version
                current_pattern = re.compile(re.escape(before) + r"\s*——\s*" + re.escape(after))
                if current_pattern.search(temp_text):
                    current_match = current_pattern.search(temp_text).group()
                    if current_match != correct:
                        stats.emdash_spacing_fixed += 1
            text = _fix_emdash_spacing(text)

        # Count quote spacing fixes
        if config.is_enabled('quote_spacing'):
            opening_quote = '\u201c'
            closing_quote = '\u201d'
            quote_before = len(re.findall(f'([A-Za-z0-9\u4e00-\u9fff]){opening_quote}', text))
            quote_after = len(re.findall(f'{closing_quote}([A-Za-z0-9\u4e00-\u9fff])', text))
            stats.quote_spacing_fixed = quote_before + quote_after
            text = _fix_quotes(text)

        # Count CJK-English spacing additions
        if config.is_enabled('cjk_english_spacing'):
            num_pattern = r"[A-Za-z0-9]+(?:[%‰℃℉]|°[CcFf]?)?"
            cjk_before_eng = len(re.findall(f"([\u4e00-\u9fff])({num_pattern})", text))
            eng_before_cjk = len(re.findall(f"({num_pattern})([\u4e00-\u9fff])", text))
            stats.cjk_english_spacing_added = cjk_before_eng + eng_before_cjk
            text = _space_between(text)

        # Count multiple spaces
        if config.is_enabled('space_collapsing'):
            multi_space_pattern = re.compile(r"\s{2,}")
            stats.spaces_collapsed = len(multi_space_pattern.findall(text))
            text = re.sub(r"\s{2,}", " ", text)

    # Apply custom regex rules and track counts
    for rule in config.custom_rules:
        try:
            pattern = rule['pattern']
            replacement = rule['replacement']
            rule_name = rule.get('name', 'custom')

            # Count matches before applying
            matches = re.findall(pattern, text)
            count = len(matches)

            if count > 0:
                stats.custom_rules_applied[rule_name] = count
                text = re.sub(pattern, replacement, text)
        except (KeyError, re.error):
            # Skip invalid rules
            continue

    return text.strip(), stats
