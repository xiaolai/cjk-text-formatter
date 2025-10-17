"""Tests for text polishing functions."""

import pytest
from cjk_text_formatter.polish import (
    polish_text,
    contains_cjk,
    _replace_dash,
    _fix_emdash_spacing,
    _fix_quotes,
    _fix_single_quotes,
    _space_between,
    _normalize_ellipsis,
)


class TestContainsCJK:
    """Test CJK text detection (Han characters and Korean Hangul)."""

    def test_contains_cjk_with_han(self):
        assert contains_cjk("这是中文") is True
        assert contains_cjk("mixed 中文 text") is True
        assert contains_cjk("日本語です") is True  # Japanese with Kanji
        assert contains_cjk("한자韓字") is True  # Korean with Hanja

    def test_contains_cjk_with_hangul(self):
        assert contains_cjk("한글") is True  # Pure Hangul (Korean alphabet)
        assert contains_cjk("안녕하세요") is True  # Korean greeting

    def test_contains_cjk_without_han_or_hangul(self):
        assert contains_cjk("English only") is False
        assert contains_cjk("123 abc") is False
        assert contains_cjk("") is False
        assert contains_cjk("ひらがな") is False  # Pure Hiragana (no Kanji)
        assert contains_cjk("カタカナ") is False  # Pure Katakana (no Kanji)


class TestNormalizeEllipsis:
    """Test ellipsis normalization (universal rule)."""

    def test_spaced_ellipsis_three_dots(self):
        assert _normalize_ellipsis(". . .") == "..."
        assert _normalize_ellipsis("text . . . more") == "text... more"

    def test_spaced_ellipsis_four_dots(self):
        assert _normalize_ellipsis(". . . .") == "..."
        assert _normalize_ellipsis("end . . . .") == "end..."

    def test_ellipsis_spacing_after(self):
        assert _normalize_ellipsis("wait...next") == "wait... next"
        assert _normalize_ellipsis("wait...  next") == "wait... next"

    def test_already_normalized(self):
        assert _normalize_ellipsis("text... more") == "text... more"


class TestReplaceDash:
    """Test -- to —— conversion with proper spacing (CJK context only)."""

    def test_double_dash_between_chinese(self):
        """Double dash between Chinese characters should convert."""
        assert _replace_dash("文本--内容") == "文本 —— 内容"
        assert _replace_dash("中文--更多") == "中文 —— 更多"

    def test_triple_dash_between_chinese(self):
        """Triple dash (and more) between Chinese characters should convert."""
        assert _replace_dash("中文---更多") == "中文 —— 更多"
        assert _replace_dash("中文----更多") == "中文 —— 更多"
        assert _replace_dash("文本-----内容") == "文本 —— 内容"

    def test_dash_with_spaces_between_chinese(self):
        """Dashes with spaces around them between Chinese should convert."""
        assert _replace_dash("中文 -- 更多") == "中文 —— 更多"
        assert _replace_dash("中文  --  更多") == "中文 —— 更多"
        assert _replace_dash("文本 --- 内容") == "文本 —— 内容"

    def test_closing_angle_quote_no_left_space(self):
        """Closing angle quote 》 should have no space before ——."""
        assert _replace_dash("《书名》--作者") == "《书名》—— 作者"
        assert _replace_dash("《书名》---作者") == "《书名》—— 作者"

    def test_opening_angle_quote_no_right_space(self):
        """Opening angle quote 《 should have no space after ——."""
        assert _replace_dash("作者--《书名》") == "作者 ——《书名》"
        assert _replace_dash("作者---《书名》") == "作者 ——《书名》"

    def test_closing_paren_no_left_space(self):
        """Closing paren ） should have no space before ——."""
        assert _replace_dash("（注释）--内容") == "（注释）—— 内容"
        assert _replace_dash("（注释）---内容") == "（注释）—— 内容"

    def test_opening_paren_no_right_space(self):
        """Opening paren （ should have no space after ——."""
        assert _replace_dash("内容--（注释）") == "内容 ——（注释）"
        assert _replace_dash("内容---（注释）") == "内容 ——（注释）"

    def test_both_quotes(self):
        """Both sides with quotes should have no spaces."""
        assert _replace_dash("《书名》--《续集》") == "《书名》——《续集》"
        assert _replace_dash("《书名》---《续集》") == "《书名》——《续集》"

    def test_dash_between_english_not_converted(self):
        """Dashes between English text should NOT convert."""
        assert _replace_dash("text--more") == "text--more"
        assert _replace_dash("hello---world") == "hello---world"
        assert _replace_dash("foo----bar") == "foo----bar"

    def test_markdown_horizontal_rule_not_converted(self):
        """Markdown horizontal rules (---) should NOT convert."""
        assert _replace_dash("---") == "---"
        assert _replace_dash("----") == "----"
        assert _replace_dash("-----") == "-----"

    def test_mixed_english_chinese_not_converted(self):
        """Dashes between English and Chinese should NOT convert."""
        assert _replace_dash("text--中文") == "text--中文"
        assert _replace_dash("中文--text") == "中文--text"


class TestFixEmdashSpacing:
    """Test spacing around existing —— characters."""

    def test_regular_text_adds_spaces(self):
        assert _fix_emdash_spacing("text——more") == "text —— more"
        assert _fix_emdash_spacing("文本——内容") == "文本 —— 内容"

    def test_closing_angle_quote_no_left_space(self):
        assert _fix_emdash_spacing("《书名》——作者") == "《书名》—— 作者"
        assert _fix_emdash_spacing("《书名》 —— 作者") == "《书名》—— 作者"  # Fix existing wrong spacing

    def test_opening_angle_quote_no_right_space(self):
        assert _fix_emdash_spacing("作者——《书名》") == "作者 ——《书名》"
        assert _fix_emdash_spacing("作者 —— 《书名》") == "作者 ——《书名》"  # Fix existing wrong spacing

    def test_closing_paren_no_left_space(self):
        assert _fix_emdash_spacing("（注释）——内容") == "（注释）—— 内容"

    def test_opening_paren_no_right_space(self):
        assert _fix_emdash_spacing("内容——（注释）") == "内容 ——（注释）"

    def test_both_quotes(self):
        assert _fix_emdash_spacing("《书名》——《续集》") == "《书名》——《续集》"
        assert _fix_emdash_spacing("《书名》 —— 《续集》") == "《书名》——《续集》"


class TestFixQuotes:
    """Test spacing around Chinese quotation marks ""."""

    def test_opening_quote_adds_space_before(self):
        # Using unicode escapes for Chinese quotes to avoid syntax errors
        assert _fix_quotes('text\u201cword\u201d') == 'text \u201cword\u201d'
        assert _fix_quotes('文本\u201c内容\u201d') == '文本 \u201c内容\u201d'
        assert _fix_quotes('123\u201ctest\u201d') == '123 \u201ctest\u201d'

    def test_closing_quote_adds_space_after(self):
        # Using unicode escapes for Chinese quotes to avoid syntax errors
        assert _fix_quotes('\u201cword\u201dtext') == '\u201cword\u201d text'
        assert _fix_quotes('\u201c内容\u201d文本') == '\u201c内容\u201d 文本'
        assert _fix_quotes('\u201ctest\u201d123') == '\u201ctest\u201d 123'

    def test_quote_spacing_with_terminal_punctuation(self):
        """No space between quotes and CJK terminal punctuation (，。！？；：、)."""
        # Comma before opening quote, period after closing quote
        assert _fix_quotes('文本，\u201c引用\u201d。') == '文本，\u201c引用\u201d。'
        # Period before opening quote, Chinese after closing quote
        assert _fix_quotes('开始。\u201c内容\u201d结束') == '开始。\u201c内容\u201d 结束'
        # Exclamation before opening quote, Chinese after closing quote
        assert _fix_quotes('问题！\u201c回答\u201d文本') == '问题！\u201c回答\u201d 文本'
        # Chinese before opening quote, question mark after closing quote
        assert _fix_quotes('文本\u201c问题\u201d？结束') == '文本 \u201c问题\u201d？结束'
        # Semicolon before opening quote, Chinese after closing quote
        assert _fix_quotes('列表；\u201c项目\u201d内容') == '列表；\u201c项目\u201d 内容'
        # Colon before opening quote, Chinese after closing quote
        assert _fix_quotes('标题：\u201c内容\u201d文本') == '标题：\u201c内容\u201d 文本'
        # Enumeration comma before opening quote, Chinese after closing quote
        assert _fix_quotes('一、\u201c项目\u201d二') == '一、\u201c项目\u201d 二'

    def test_quote_spacing_with_book_title_marks(self):
        """No space between quotes and book title marks 《》."""
        assert _fix_quotes('《书名》\u201c引用\u201d文本') == '《书名》\u201c引用\u201d 文本'
        assert _fix_quotes('文本\u201c引用\u201d《书名》') == '文本 \u201c引用\u201d《书名》'
        assert _fix_quotes('《A》\u201cB\u201d《C》') == '《A》\u201cB\u201d《C》'

    def test_quote_spacing_with_corner_brackets(self):
        """No space between quotes and corner brackets 「」『』."""
        # Single corner brackets
        assert _fix_quotes('「日文」\u201c引用\u201d文本') == '「日文」\u201c引用\u201d 文本'
        assert _fix_quotes('文本\u201c引用\u201d「日文」') == '文本 \u201c引用\u201d「日文」'
        # Double corner brackets
        assert _fix_quotes('『重点』\u201c引用\u201d文本') == '『重点』\u201c引用\u201d 文本'
        assert _fix_quotes('文本\u201c引用\u201d『重点』') == '文本 \u201c引用\u201d『重点』'

    def test_quote_spacing_with_lenticular_brackets(self):
        """No space between quotes and lenticular brackets 【】."""
        assert _fix_quotes('【注】\u201c引用\u201d文本') == '【注】\u201c引用\u201d 文本'
        assert _fix_quotes('文本\u201c引用\u201d【注】') == '文本 \u201c引用\u201d【注】'

    def test_quote_spacing_with_parentheses(self):
        """No space between quotes and full-width parentheses （）."""
        assert _fix_quotes('（备注）\u201c引用\u201d文本') == '（备注）\u201c引用\u201d 文本'
        assert _fix_quotes('文本\u201c引用\u201d（备注）') == '文本 \u201c引用\u201d（备注）'

    def test_quote_spacing_with_angle_brackets(self):
        """No space between quotes and angle brackets 〈〉."""
        assert _fix_quotes('〈标记〉\u201c引用\u201d文本') == '〈标记〉\u201c引用\u201d 文本'
        assert _fix_quotes('文本\u201c引用\u201d〈标记〉') == '文本 \u201c引用\u201d〈标记〉'

    def test_quote_spacing_with_emdash(self):
        """Spaces ARE needed between quotes and em-dash (curly quotes lack visual spacing)."""
        assert _fix_quotes('前文——\u201c引用\u201d后文') == '前文—— \u201c引用\u201d 后文'
        assert _fix_quotes('前文\u201c引用\u201d——后文') == '前文 \u201c引用\u201d ——后文'
        # Both sides with em-dash
        assert _fix_quotes('前——\u201c引用\u201d——后') == '前—— \u201c引用\u201d ——后'


class TestFixSingleQuotes:
    """Test spacing around Chinese single quotation marks ''."""

    def test_single_quote_spacing_with_emdash(self):
        """Spaces ARE needed between single quotes and em-dash (curly quotes lack visual spacing)."""
        assert _fix_single_quotes('前文——\u2018引用\u2019后文') == '前文—— \u2018引用\u2019 后文'
        assert _fix_single_quotes('前文\u2018引用\u2019——后文') == '前文 \u2018引用\u2019 ——后文'
        # Both sides with em-dash
        assert _fix_single_quotes('前——\u2018引用\u2019——后') == '前—— \u2018引用\u2019 ——后'


class TestSpaceBetween:
    """Test spacing between Chinese and English/numbers."""

    def test_chinese_then_english(self):
        assert _space_between("中文English") == "中文 English"
        assert _space_between("测试test文本") == "测试 test 文本"

    def test_english_then_chinese(self):
        assert _space_between("English中文") == "English 中文"
        assert _space_between("test测试text") == "test 测试 text"

    def test_chinese_then_number(self):
        assert _space_between("数字123") == "数字 123"
        assert _space_between("共100个") == "共 100 个"

    def test_number_then_chinese(self):
        assert _space_between("123数字") == "123 数字"
        assert _space_between("100个item") == "100 个 item"

    def test_already_spaced(self):
        assert _space_between("中文 English") == "中文 English"
        assert _space_between("test 测试") == "test 测试"

    def test_percentage_spacing(self):
        """Test spacing with percentage symbols."""
        assert _space_between("占人口比例的5%甚至更多") == "占人口比例的 5% 甚至更多"
        assert _space_between("增长20%左右") == "增长 20% 左右"
        assert _space_between("的15%是") == "的 15% 是"

    def test_temperature_spacing(self):
        """Test spacing with temperature units."""
        # Unicode temperature symbols
        assert _space_between("温度25℃很热") == "温度 25℃ 很热"
        assert _space_between("约25℉左右") == "约 25℉ 左右"
        # Degree + letter combinations
        assert _space_between("是25°C今天") == "是 25°C 今天"
        assert _space_between("约25°c左右") == "约 25°c 左右"
        assert _space_between("温度25°F较低") == "温度 25°F 较低"
        assert _space_between("大约25°f吧") == "大约 25°f 吧"

    def test_degree_spacing(self):
        """Test spacing with degree symbols."""
        assert _space_between("角度45°比较") == "角度 45° 比较"
        assert _space_between("转90°然后") == "转 90° 然后"

    def test_permille_spacing(self):
        """Test spacing with per mille symbols."""
        assert _space_between("浓度3‰的溶液") == "浓度 3‰ 的溶液"


class TestJapaneseSupport:
    """Test Japanese language support (Hiragana, Katakana, Kanji).

    Note: CJK-specific rules only apply when Han characters (Kanji) are present.
    Pure kana text is treated as non-CJK and doesn't get spacing rules applied.
    This is by design - most real Japanese text contains Kanji.
    """

    def test_japanese_mixed_kanji_kana_english_spacing(self):
        """Japanese with Kanji should get spaces around English (the reported bug fix)."""
        # This was the original bug - を (Hiragana) after "raycast" didn't get space
        assert polish_text("私は毎日Raycastを使って仕事の効率化を助けてくれます") == \
               "私は毎日 Raycast を使って仕事の効率化を助けてくれます"
        assert polish_text("日本語testテキスト") == "日本語 test テキスト"
        assert polish_text("東京でappleを買う") == "東京で apple を買う"

    def test_japanese_numbers_with_units(self):
        """Japanese numbers with units should get spacing."""
        assert polish_text("気温は25°Cです") == "気温は 25°C です"
        assert polish_text("価格は100円です") == "価格は 100 円です"
        assert polish_text("約5%程度") == "約 5% 程度"

    def test_japanese_quote_spacing_with_kanji(self):
        """Japanese quotes with Kanji should get proper spacing."""
        # Using curly quotes (U+201C/D) not straight quotes
        assert polish_text('私は\u201chello\u201dと言いました') == '私は \u201chello\u201d と言いました'
        assert polish_text('東京は\u201cTokyo\u201dです') == '東京は \u201cTokyo\u201d です'

    def test_japanese_pure_kana_no_spacing(self):
        """Pure kana text without Kanji doesn't trigger CJK rules (by design)."""
        # Pure Hiragana - no Han characters, so CJK rules don't apply
        assert polish_text("これはtestですね") == "これはtestですね"
        # Pure Katakana - no Han characters, so CJK rules don't apply
        assert polish_text("テストtestケース") == "テストtestケース"

    def test_japanese_fullwidth_punctuation_preserved(self):
        """Japanese fullwidth punctuation should be preserved/normalized."""
        # Japanese uses fullwidth punctuation like Chinese
        assert polish_text("日本はアジアです。") == "日本はアジアです。"
        assert polish_text("質問は何ですか？") == "質問は何ですか？"


class TestKoreanSupport:
    """Test Korean language support (Hangul).

    Korean Hangul characters now trigger CJK spacing rules, so spaces will be
    added between Hangul and English/numbers, just like with Chinese and Japanese.
    Korean punctuation rules still exclude fullwidth punctuation conversion
    since Korean uses Western punctuation.
    """

    def test_korean_with_hanja_english_spacing(self):
        """Korean with Hanja (Han characters) should get spaces around English."""
        # Korean with Hanja (mixed script)
        assert polish_text("韓國에서test를합니다") == "韓國에서 test 를합니다"
        assert polish_text("漢字apple사용") == "漢字 apple 사용"

    def test_korean_pure_hangul_with_spacing(self):
        """Pure Hangul text now gets CJK spacing rules applied."""
        # Pure Hangul - now triggers CJK rules for spacing
        assert polish_text("나는매일raycast를사용합니다") == "나는매일 raycast 를사용합니다"
        assert polish_text("이것은test입니다") == "이것은 test 입니다"
        assert polish_text("한글apple텍스트") == "한글 apple 텍스트"

    def test_korean_western_punctuation_preserved(self):
        """Korean halfwidth (Western) punctuation should be preserved."""
        # Korean uses Western punctuation . , not fullwidth 。，
        text = "이것은 테스트입니다."
        assert polish_text(text) == text  # Period stays halfwidth

        text = "첫째, 둘째, 셋째입니다."
        assert polish_text(text) == text  # Commas stay halfwidth


class TestCJKParenthesisSpacing:
    """Test spacing between CJK characters and half-width parentheses."""

    def test_cjk_with_paren_enclosed_text(self):
        """Add spaces around parentheses, then () may convert to （） in CJK context."""
        # English content inside parens: spaces added, parens stay half-width
        assert polish_text('这是测试(test)内容') == '这是测试 (test) 内容'
        # CJK content: spaces added, then fullwidth_parentheses converts () to （）
        assert polish_text('文本(注释)继续') == '文本 （注释） 继续'
        # Korean + English: spaces added, parens stay half-width
        assert polish_text('한글(Korean)텍스트') == '한글 (Korean) 텍스트'

    def test_cjk_before_opening_paren(self):
        """Add space between CJK and opening parenthesis."""
        assert polish_text('中文(English') == '中文 (English'
        assert polish_text('日本語(test') == '日本語 (test'

    def test_closing_paren_before_cjk(self):
        """Add space between closing parenthesis and CJK."""
        assert polish_text('English)中文') == 'English) 中文'
        assert polish_text('test)日本語') == 'test) 日本語'

    def test_already_spaced_parentheses(self):
        """Already spaced parentheses will add extra spaces, then space_collapsing cleans them up."""
        # The rule adds spaces, creating double spaces, then space_collapsing fixes it
        assert polish_text('中文 (test) 文本') == '中文 (test) 文本'  # Double spaces collapsed to single


class TestPolishText:
    """Test complete text polishing with all rules applied."""

    def test_universal_rules_applied_to_non_chinese(self):
        """Universal rules like ellipsis should apply to all text."""
        result = polish_text("wait . . . more")
        assert result == "wait... more"

    def test_chinese_rules_applied_together(self):
        """All Chinese rules should work together."""
        text = "《Python编程》--一本关于Python的书。中文English混合，数字123也包含。"
        result = polish_text(text)
        # Should have:
        # - —— spacing fixed
        # - Space between Chinese and English
        # - Space between Chinese and numbers
        assert "《Python编程》—— 一本" in result or "《Python 编程》—— 一本" in result
        assert "中文 English" in result
        assert "数字 123" in result

    def test_em_dash_with_quotes(self):
        """Test em-dash spacing with angle quotes."""
        assert polish_text("《书名》——作者") == "《书名》—— 作者"
        assert polish_text("作者——《书名》") == "作者 ——《书名》"

    def test_multiple_spaces_collapsed(self):
        """Multiple consecutive spaces should be collapsed to one."""
        text = "文本    太多    空格"
        result = polish_text(text)
        assert "  " not in result  # No double spaces

    def test_space_collapsing_preserves_newlines(self):
        """Space collapsing should preserve newlines (paragraph breaks)."""
        # Double newline should be preserved (paragraph break)
        text = "段落一。\n\n段落二。"
        result = polish_text(text)
        assert result == "段落一。\n\n段落二。"

        # Single newline should be preserved
        text = "第一行。\n第二行。"
        result = polish_text(text)
        assert result == "第一行。\n第二行。"

    def test_trailing_spaces_removed(self):
        """Trailing spaces at end of lines should be removed."""
        # Trailing spaces before newline
        text = "第一行有空格   \n第二行也有   \n第三行。"
        result = polish_text(text)
        assert result == "第一行有空格\n第二行也有\n第三行。"

        # Trailing spaces before paragraph break
        text = "段落一。  \n\n段落二。"
        result = polish_text(text)
        assert result == "段落一。\n\n段落二。"

        # Only trailing spaces (whole line of spaces)
        text = "文本\n    \n更多文本"
        result = polish_text(text)
        assert result == "文本\n\n更多文本"

    def test_excessive_newlines_collapsed(self):
        """Excessive newlines (3+) should be collapsed to 2 (one blank line)."""
        # Triple newline → double newline
        text = "章节一。\n\n\n章节二。"
        result = polish_text(text)
        assert result == "章节一。\n\n章节二。"

        # Quadruple newline → double newline
        text = "段落一。\n\n\n\n段落二。"
        result = polish_text(text)
        assert result == "段落一。\n\n段落二。"

        # Five newlines → double newline
        text = "部分一。\n\n\n\n\n部分二。"
        result = polish_text(text)
        assert result == "部分一。\n\n部分二。"

    def test_space_collapsing_with_mixed_whitespace(self):
        """Space collapsing should handle mixed spaces and newlines correctly."""
        # Multiple spaces between words on same line
        text = "文本    太多    空格"
        result = polish_text(text)
        assert result == "文本 太多 空格"

        # Leading spaces after newline are preserved (indentation)
        text = "一些文本\n  更多文本"
        result = polish_text(text)
        assert result == "一些文本\n  更多文本"

        # Multiple levels of indentation preserved
        text = "行一\n  行二缩进\n    行三更多缩进"
        result = polish_text(text)
        assert result == "行一\n  行二缩进\n    行三更多缩进"

    def test_strip_whitespace(self):
        """Trailing whitespace should be removed, leading whitespace preserved."""
        # Preserves leading whitespace (for markdown indentation)
        assert polish_text("  text  ") == "  text"
        assert polish_text("  中文  ") == "  中文"
        # Still removes trailing whitespace
        assert polish_text("text  ") == "text"
        assert polish_text("中文  ") == "中文"

    def test_non_chinese_text_unchanged(self):
        """English text without Chinese should only get universal rules."""
        text = "English text with no Chinese"
        result = polish_text(text)
        assert result == text  # Should be unchanged

    def test_mixed_complex_text(self):
        """Complex real-world example with new dash conversion rules."""
        text = "作者——李华（生于1980年）。他写了《人生》--一部长篇小说。该书在2018年出版。"
        result = polish_text(text)

        # Check key transformations
        assert "作者 —— 李华" in result  # Em-dash spacing with regular text
        assert "。他" in result or "。 他" in result  # Period handling
        assert "《人生》—— 一部" in result  # Dash converts between CJK (closing quote, no left space)
        assert "2018 年" in result  # Number-Chinese spacing
