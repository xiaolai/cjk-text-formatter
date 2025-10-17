"""Text polishing functions for Chinese typography."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .config import RuleConfig

# Regular expressions
CHINESE_RE = re.compile(r"[\u4e00-\u9fff]")
HANGUL_RE = re.compile(r"[\uac00-\ud7af]")

# CJK character ranges for pattern matching
HAN = r'\u4e00-\u9fff'              # Chinese characters + Japanese Kanji
HIRAGANA = r'\u3040-\u309f'         # Japanese Hiragana
KATAKANA = r'\u30a0-\u30ff'         # Japanese Katakana
HANGUL = r'\uac00-\ud7af'           # Korean Hangul

# Combined patterns for different use cases
CJK_ALL = f'{HAN}{HIRAGANA}{KATAKANA}{HANGUL}'           # All CJK scripts
CJK_NO_KOREAN = f'{HAN}{HIRAGANA}{KATAKANA}'             # Chinese + Japanese only

# CJK punctuation constants
CJK_TERMINAL_PUNCTUATION = '，。！？；：、'
CJK_CLOSING_BRACKETS = '》」』】）〉'
CJK_OPENING_BRACKETS = '《「『【（〈'
CJK_EM_DASH = '——'

# CJK character range for dash conversion (includes Han, Hiragana, Katakana, and CJK punctuation)
CJK_CHARS_PATTERN = rf'[{HAN}{HIRAGANA}{KATAKANA}《》「」『』【】（）〈〉，。！？；：、]'

# Pre-compiled regex patterns for performance
ELLIPSIS_PATTERN = re.compile(r"\s*\.\s+\.\s+\.(?:\s+\.)*")
ELLIPSIS_SPACING_PATTERN = re.compile(r"\.\.\.\s*(?=\S)")
# Match 2+ dashes between CJK characters (with optional whitespace)
DASH_PATTERN = re.compile(rf'({CJK_CHARS_PATTERN})\s*-{{2,}}\s*({CJK_CHARS_PATTERN})')
EMDASH_SPACING_PATTERN = re.compile(r"([^\s])\s*——\s*([^\s])")
# CJK-parenthesis spacing patterns
CJK_OPENING_PAREN_PATTERN = re.compile(rf'([{CJK_ALL}])\(')
CLOSING_PAREN_CJK_PATTERN = re.compile(rf'\)([{CJK_ALL}])')
# Fullwidth normalization patterns
FULLWIDTH_PARENS_PATTERN = re.compile(rf'\(([{CJK_NO_KOREAN}][^()]*)\)')
FULLWIDTH_BRACKETS_PATTERN = re.compile(rf'\[([{CJK_NO_KOREAN}][^\[\]]*)\]')
CURRENCY_SPACING_PATTERN = re.compile(r'([$¥€£₹USD|CNY|EUR|GBP])\s+(\d)')
SLASH_SPACING_PATTERN = re.compile(r'(?<![/:])\s*/\s*(?!/)')
MULTI_SPACE_PATTERN = re.compile(r"(\S) {2,}")
TRAILING_SPACE_PATTERN = re.compile(r" +$", flags=re.MULTILINE)
EXCESSIVE_NEWLINE_PATTERN = re.compile(r"\n{3,}")


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


def contains_cjk(text: str) -> bool:
    """Check if text contains any CJK characters (Han/Kanji/Hangul).

    Note: This checks for Han characters (Chinese/Japanese Kanji) or Korean Hangul
    as a gate to determine if CJK-specific typography rules should apply.
    Text with these characters typically needs CJK typography rules
    (spacing with English/numbers, em-dash, quotes). Note that fullwidth
    punctuation rules use CJK_NO_KOREAN to exclude Korean, as Korean uses
    Western punctuation.

    Args:
        text: Text to check

    Returns:
        True if text contains Han or Hangul characters, False otherwise
    """
    return bool(CHINESE_RE.search(text) or HANGUL_RE.search(text))


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
    text = ELLIPSIS_PATTERN.sub("...", text)
    # Ensure exactly one space after ellipsis when followed by non-whitespace
    text = ELLIPSIS_SPACING_PATTERN.sub("... ", text)
    return text


def _replace_dash(text: str) -> str:
    """Convert dashes (2+) to —— when between CJK characters.

    Only converts dashes between Chinese characters or CJK punctuation.
    Supports flexible dash count (---, ----, etc.) and optional spacing.

    Rules:
    - Only converts when both sides are CJK characters/punctuation
    - No space between closing quotes/parens (》）) and ——
    - No space between —— and opening quotes/parens (《（)
    - Regular text gets spaces on both sides

    Args:
        text: Text to process

    Returns:
        Text with dashes converted to —— with proper spacing
    """
    def repl(match: re.Match[str]) -> str:
        before = match.group(1)
        after = match.group(2)
        # No space between closing quotes/parens and ——
        left_space = "" if before in ("）", "》") else " "
        # No space between —— and opening quotes/parens
        right_space = "" if after in ("（", "《") else " "
        return f"{before}{left_space}——{right_space}{after}"

    return DASH_PATTERN.sub(repl, text)


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

    return EMDASH_SPACING_PATTERN.sub(repl, text)


def _fix_quote_spacing(text: str, opening_quote: str, closing_quote: str) -> str:
    """Fix spacing around quotation marks with smart CJK punctuation handling.

    Generic implementation for any quote type (double, single, etc.).

    Rules:
    - Add space before opening quote if preceded by alphanumeric or Chinese
    - Add space after closing quote if followed by alphanumeric or Chinese
    - NO space added when adjacent to CJK punctuation with built-in visual spacing:
      * Terminal punctuation: ，。！？；：、
      * Book title marks: 《》
      * Corner brackets: 「」『』
      * Lenticular brackets: 【】
      * Parentheses: （）
      * Angle brackets: 〈〉
      * Em-dash: ——

    Args:
        text: Text to process
        opening_quote: Opening quote character (e.g., " or ')
        closing_quote: Closing quote character (e.g., " or ')

    Returns:
        Text with corrected quotation mark spacing
    """
    # All punctuation that should not have space before opening quote
    no_space_before = CJK_CLOSING_BRACKETS + CJK_TERMINAL_PUNCTUATION
    # All punctuation that should not have space after closing quote
    no_space_after = CJK_OPENING_BRACKETS + CJK_TERMINAL_PUNCTUATION

    def repl_before(match: re.Match[str]) -> str:
        """Add space before opening quote only if not preceded by CJK punct or em-dash."""
        before = match.group(1)
        # Check if we should skip adding space
        if before in no_space_before:
            return f'{before}{opening_quote}'
        return f'{before} {opening_quote}'

    def repl_after(match: re.Match[str]) -> str:
        """Add space after closing quote only if not followed by CJK punct or em-dash."""
        after = match.group(1)
        # Check if we should skip adding space
        if after in no_space_after:
            return f'{closing_quote}{after}'
        return f'{closing_quote} {after}'

    # Add space before quote if preceded by alphanumeric/CJK/em-dash (but not CJK punct)
    # Include em-dash as a special case (2-char sequence)
    text = re.sub(
        f'([A-Za-z0-9{CJK_ALL}{CJK_CLOSING_BRACKETS}{CJK_TERMINAL_PUNCTUATION}]|{CJK_EM_DASH}){opening_quote}',
        repl_before,
        text
    )

    # Add space after quote if followed by alphanumeric/CJK/em-dash (but not CJK punct)
    # Include em-dash as a special case (2-char sequence)
    text = re.sub(
        f'{closing_quote}([A-Za-z0-9{CJK_ALL}{CJK_OPENING_BRACKETS}{CJK_TERMINAL_PUNCTUATION}]|{CJK_EM_DASH})',
        repl_after,
        text
    )

    return text


def _fix_quotes(text: str) -> str:
    """Fix spacing around Chinese double quotation marks “” with smart CJK punctuation handling.

    Args:
        text: Text to process

    Returns:
        Text with corrected quotation mark spacing
    """
    # U+201C: " (LEFT DOUBLE QUOTATION MARK)
    # U+201D: " (RIGHT DOUBLE QUOTATION MARK)
    return _fix_quote_spacing(text, '\u201c', '\u201d')


def _fix_single_quotes(text: str) -> str:
    """Fix spacing around Chinese single quotation marks '' with smart CJK punctuation handling.

    Same rules as double quotes, but for single quotes.

    Args:
        text: Text to process

    Returns:
        Text with corrected quotation mark spacing
    """
    # U+2018: ' (LEFT SINGLE QUOTATION MARK)
    # U+2019: ' (RIGHT SINGLE QUOTATION MARK)
    return _fix_quote_spacing(text, '\u2018', '\u2019')


def _fix_cjk_parenthesis_spacing(text: str) -> str:
    """Add space between CJK characters and half-width parentheses.

    Only applies to half-width parentheses (), not full-width （）.
    Full-width parentheses are handled by fullwidth_parentheses rule.

    Examples:
        这是测试(test)内容 → 这是测试 (test) 内容
        中文(注释)文本 → 中文 (注释) 文本

    Args:
        text: Text to process

    Returns:
        Text with spaces added between CJK and parentheses
    """
    # Add space between CJK character and opening paren
    text = CJK_OPENING_PAREN_PATTERN.sub(r'\1 (', text)
    # Add space between closing paren and CJK character
    text = CLOSING_PAREN_CJK_PATTERN.sub(r') \1', text)
    return text


def _normalize_fullwidth_punctuation(text: str) -> str:
    """Normalize punctuation width based on context.

    Full-width in CJK context, half-width in English context.
    """
    # Half to full-width mapping
    half_to_full = {
        ',': '，',
        '.': '。',
        '!': '！',
        '?': '？',
        ';': '；',
        ':': '：',
    }

    # Convert to full-width when surrounded by CJK (Chinese + Japanese, NOT Korean)
    for half, full in half_to_full.items():
        # CJK + half + CJK → CJK + full + CJK
        text = re.sub(
            f'([{CJK_NO_KOREAN}]){re.escape(half)}([{CJK_NO_KOREAN}])',
            f'\\1{full}\\2',
            text
        )
        # CJK + half + end → CJK + full
        text = re.sub(
            f'([{CJK_NO_KOREAN}]){re.escape(half)}(?=\\s|$)',
            f'\\1{full}',
            text
        )

    return text


def _normalize_fullwidth_parentheses(text: str) -> str:
    """Normalize parentheses width in CJK context."""
    # Convert half-width to full-width when content is CJK
    text = FULLWIDTH_PARENS_PATTERN.sub(r'（\1）', text)
    return text


def _normalize_fullwidth_brackets(text: str) -> str:
    """Normalize brackets width in CJK context."""
    # Convert half-width to full-width when content is CJK
    text = FULLWIDTH_BRACKETS_PATTERN.sub(r'【\1】', text)
    return text


def _cleanup_consecutive_punctuation(text: str, limit: int = 1) -> str:
    """Reduce consecutive punctuation marks.

    Args:
        text: Text to process
        limit: Maximum allowed repetitions (0=unlimited, 1=single, 2=double)

    Returns:
        Text with reduced consecutive punctuation
    """
    if limit == 0:
        return text

    # Punctuation to limit
    marks = ['！', '？', '。']

    for mark in marks:
        if limit == 1:
            text = re.sub(f'{re.escape(mark)}{{2,}}', mark, text)
        elif limit == 2:
            text = re.sub(f'{re.escape(mark)}{{3,}}', mark * 2, text)

    return text


def _normalize_fullwidth_alphanumeric(text: str) -> str:
    """Convert full-width alphanumeric to half-width."""
    result = []
    for char in text:
        code = ord(char)
        # Full-width numbers (0-9): U+FF10-U+FF19
        if 0xFF10 <= code <= 0xFF19:
            result.append(chr(code - 0xFEE0))
        # Full-width uppercase (A-Z): U+FF21-U+FF3A
        elif 0xFF21 <= code <= 0xFF3A:
            result.append(chr(code - 0xFEE0))
        # Full-width lowercase (a-z): U+FF41-U+FF5A
        elif 0xFF41 <= code <= 0xFF5A:
            result.append(chr(code - 0xFEE0))
        else:
            result.append(char)
    return ''.join(result)


def _fix_currency_spacing(text: str) -> str:
    """Remove spaces between currency symbols and amounts."""
    # Remove space after currency symbol before number using pre-compiled pattern
    text = CURRENCY_SPACING_PATTERN.sub(r'\1\2', text)
    return text


def _fix_slash_spacing(text: str) -> str:
    """Remove spaces around slashes."""
    # Remove spaces around / but not in URLs
    # Simple approach: if not preceded/followed by / (avoid //)
    text = SLASH_SPACING_PATTERN.sub('/', text)
    return text


def _space_between(text: str) -> str:
    """Add spaces between Chinese and English/numbers.

    Rules:
    - Add space between Chinese characters and English letters
    - Add space between Chinese characters and numbers (with units like %, °C, etc.)
    - Add space between Chinese and currency symbols with amounts

    Args:
        text: Text to process

    Returns:
        Text with spaces added between Chinese and alphanumerics
    """
    # Pattern for currency + numbers: $100, ¥500, EUR200, etc.
    # Pattern for alphanumeric with optional measurement units
    # Supports: 5%, 25°C, 25°c, 45°, 3‰, 25℃, etc.
    # Also supports currency symbols: $, ¥, €, £, ₹
    alphanum_pattern = r"(?:[$¥€£₹][ ]?)?[A-Za-z0-9]+(?:[%‰℃℉]|°[CcFf]?|[ ]?(?:USD|CNY|EUR|GBP|RMB))?"

    # CJK (all scripts) followed by alphanumeric/currency (with optional unit)
    text = re.sub(f"([{CJK_ALL}])({alphanum_pattern})", r"\1 \2", text)
    # Alphanumeric/currency (with optional unit) followed by CJK (all scripts)
    text = re.sub(f"({alphanum_pattern})([{CJK_ALL}])", r"\1 \2", text)
    return text


def polish_text(text: str, config: RuleConfig | None = None) -> str:
    """Polish text with typography rules.

    Universal rules (all languages):
    - Normalize ellipsis patterns (. . . → ...)
    - Collapse excessive newlines (3+ → 2, one blank line max)

    Chinese-specific rules:
    - Convert -- to —— with proper spacing
    - Fix spacing around existing ——
    - Fix spacing around Chinese quotes ""
    - Add spaces between Chinese and English/numbers
    - Collapse multiple consecutive spaces
    - Remove trailing spaces at line endings

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

    # CJK-specific polishing (triggered by presence of Han characters)
    if contains_cjk(text):
        # Normalization rules (run first)
        if config.is_enabled('fullwidth_alphanumeric'):
            text = _normalize_fullwidth_alphanumeric(text)
        if config.is_enabled('fullwidth_punctuation'):
            text = _normalize_fullwidth_punctuation(text)
        # Note: fullwidth_parentheses must run AFTER cjk_parenthesis_spacing
        if config.is_enabled('fullwidth_brackets'):
            text = _normalize_fullwidth_brackets(text)

        # Em-dash and quote rules
        if config.is_enabled('dash_conversion'):
            text = _replace_dash(text)
        if config.is_enabled('emdash_spacing'):
            text = _fix_emdash_spacing(text)
        if config.is_enabled('quote_spacing'):
            text = _fix_quotes(text)
        if config.is_enabled('single_quote_spacing'):
            text = _fix_single_quotes(text)

        # Spacing rules
        if config.is_enabled('cjk_english_spacing'):
            text = _space_between(text)
        # Note: cjk_parenthesis_spacing must run BEFORE fullwidth_parentheses
        if config.is_enabled('cjk_parenthesis_spacing'):
            text = _fix_cjk_parenthesis_spacing(text)
        # Now convert remaining () to （） in CJK context
        if config.is_enabled('fullwidth_parentheses'):
            text = _normalize_fullwidth_parentheses(text)
        if config.is_enabled('currency_spacing'):
            text = _fix_currency_spacing(text)
        if config.is_enabled('slash_spacing'):
            text = _fix_slash_spacing(text)

        # Cleanup rules
        punct_limit = config.get_value('consecutive_punctuation_limit', 0)
        if punct_limit > 0:
            text = _cleanup_consecutive_punctuation(text, punct_limit)

        # Collapse multiple spaces to single space (preserve newlines and indentation)
        if config.is_enabled('space_collapsing'):
            # Match non-space + 2+ spaces to preserve leading indentation after newlines
            text = MULTI_SPACE_PATTERN.sub(r"\1 ", text)

        # Remove trailing spaces at end of lines
        text = TRAILING_SPACE_PATTERN.sub("", text)

    # Collapse excessive newlines (3+) to max 2 (one blank line)
    # UNIVERSAL RULE - applies to all files, not just CJK
    text = EXCESSIVE_NEWLINE_PATTERN.sub("\n\n", text)

    # Apply custom regex rules
    text = _apply_custom_rules(text, config.custom_rules)

    return text.rstrip()  # Preserve leading whitespace (for markdown indentation)


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
        stats.ellipsis_normalized = len(ELLIPSIS_PATTERN.findall(text))
        text = _normalize_ellipsis(text)

    # CJK-specific polishing (triggered by presence of Han characters)
    if contains_cjk(text):
        # Count dash conversions (-- to ——)
        if config.is_enabled('dash_conversion'):
            stats.dash_converted = len(DASH_PATTERN.findall(text))
            text = _replace_dash(text)

        # Count em-dash spacing fixes
        if config.is_enabled('emdash_spacing'):
            matches = EMDASH_SPACING_PATTERN.findall(text)
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
            quote_before = len(re.findall(f'([A-Za-z0-9{CJK_ALL}]){opening_quote}', text))
            quote_after = len(re.findall(f'{closing_quote}([A-Za-z0-9{CJK_ALL}])', text))
            stats.quote_spacing_fixed = quote_before + quote_after
            text = _fix_quotes(text)

        # Count CJK-English spacing additions
        if config.is_enabled('cjk_english_spacing'):
            num_pattern = r"[A-Za-z0-9]+(?:[%‰℃℉]|°[CcFf]?)?"
            cjk_before_eng = len(re.findall(f"([{CJK_ALL}])({num_pattern})", text))
            eng_before_cjk = len(re.findall(f"({num_pattern})([{CJK_ALL}])", text))
            stats.cjk_english_spacing_added = cjk_before_eng + eng_before_cjk
            text = _space_between(text)

        # Count multiple spaces (preserve newlines and indentation)
        if config.is_enabled('space_collapsing'):
            # Match non-space + 2+ spaces to preserve leading indentation
            stats.spaces_collapsed = len(MULTI_SPACE_PATTERN.findall(text))
            text = MULTI_SPACE_PATTERN.sub(r"\1 ", text)

        # Remove trailing spaces at end of lines
        text = TRAILING_SPACE_PATTERN.sub("", text)

    # Collapse excessive newlines (3+) to max 2 (one blank line)
    # UNIVERSAL RULE - applies to all files, not just CJK
    text = EXCESSIVE_NEWLINE_PATTERN.sub("\n\n", text)

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

    return text.rstrip(), stats  # Preserve leading whitespace (for markdown indentation)
