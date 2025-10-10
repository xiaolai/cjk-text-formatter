# CJK Text Formatter

A Python CLI tool for polishing text with Chinese typography rules. Automatically formats mixed Chinese-English text, fixes em-dash spacing, normalizes ellipsis, and more.

## Features

### Universal Rules (All Languages)
- **Ellipsis normalization**: Converts `. . .` or `. . . .` to `...` with proper spacing

### Chinese-Specific Rules

**Quote & Punctuation:**
- **Double quote spacing (`""`)**: Smart spacing that excludes CJK punctuation with built-in visual spacing
- **Single quote spacing (`''`)**: Same smart rules as double quotes
- **Em-dash spacing**: Converts `--` to `——` with context-aware spacing
- **Full-width punctuation**: Normalizes `,`→`，` `.`→`。` in CJK context
- **Full-width parentheses/brackets**: `(text)` → `（text）` in CJK context

**Normalization:**
- **Full-width alphanumeric**: Converts `１２３ＡＢＣ` → `123ABC`
- **Consecutive punctuation cleanup**: `！！！` → `！` (configurable limit)

**Spacing:**
- **CJK-English spacing**: Auto-adds spaces between Chinese & English/numbers
- **Currency spacing**: `$ 100` → `$100`
- **Slash spacing**: `A / B` → `A/B`
- **Multiple space collapsing**: Reduces consecutive spaces (preserves indentation)
- **Trailing space removal**: Cleans up line endings
- **Excessive newline collapsing**: Limits to max one blank line

### File Type Support
- **Plain Text** (`.txt`): Direct formatting
- **Markdown** (`.md`): Preserves code blocks (fenced, indented, inline)
- **HTML** (`.html`, `.htm`): Formats text content while preserving tags and `<code>`/`<pre>` elements

## Installation

> **⚠️ BREAKING CHANGE in v0.3.0**: The package has been renamed from `textformater` to `cjk_text_formatter` to fix a spelling error. If you're upgrading from v0.2.x:
> - Update imports: `from textformater` → `from cjk_text_formatter`
> - CLI command (`ctf`) remains unchanged
> - Config file name unchanged: `cjk-text-formatter.toml`

### Requirements

- Python 3.8 or higher

### Install from PyPI

```bash
# Basic installation
pip install cjk-text-formatter

# With HTML support (optional)
pip install cjk-text-formatter[html]
```

### Install from Source

```bash
git clone https://github.com/xiaolai/cjk-text-formatter.git
cd cjk-text-formatter
pip install -e .

# Or with HTML support
pip install -e ".[html]"
```

### Verify Installation

```bash
# Check version
ctf --version

# Show help
ctf --help

# Quick test
ctf "文本English混合"
# Expected output: 文本 English 混合
```

## Usage

### Command Line

```bash
# Format text directly
ctf "文本English混合"
# Output: 文本 English 混合

# Format with em-dash
ctf "《书名》--作者"
# Output: 《书名》—— 作者

# Read from stdin
echo "文本English混合" | ctf

# Format a single file
ctf input.txt
ctf input.md --output formatted.md

# Format in-place
ctf document.txt --inplace

# Preview changes without writing (dry-run)
ctf document.txt --dry-run

# Format all files in a directory
ctf ./docs/ --inplace
ctf ./docs/ --recursive --inplace

# Format specific file types only
ctf ./docs/ --inplace -e .md -e .txt
```

### Python API

```python
from cjk_text_formatter.polish import polish_text

# Format text
text = "文本English混合，数字123也包含。"
result = polish_text(text)
print(result)
# Output: 文本 English 混合，数字 123 也包含。

# Format with em-dash
text = "《Python编程》--一本好书"
result = polish_text(text)
print(result)
# Output: 《Python 编程》—— 一本好书
```

```python
from cjk_text_formatter.processors import process_file, find_files

# Process a single file
result = process_file(Path("document.md"))

# Find and process multiple files
files = find_files(Path("./docs"), recursive=True, extensions=['.md', '.txt'])
for file in files:
    result = process_file(file)
    # Do something with result
```

## Configuration

**Requires Python 3.11+** (uses built-in `tomllib`). On Python <3.11, all rules are enabled by default.

### Config File Locations

Configuration is loaded with the following priority (highest to lowest):

1. **Custom path**: `ctf --config /path/to/config.toml`
2. **Project root**: `./cjk-text-formatter.toml`
3. **User config**: `~/.config/cjk-text-formatter.toml`
4. **Defaults**: All rules enabled

### Quick Start

```bash
# Copy example config to your project
cp cjk-text-formatter.toml.example cjk-text-formatter.toml

# Or to user config
cp cjk-text-formatter.toml.example ~/.config/cjk-text-formatter.toml

# Edit and customize rules
```

### Configuration Format

```toml
# cjk-text-formatter.toml

[rules]
# Toggle built-in rules on/off
ellipsis_normalization = true
dash_conversion = true
emdash_spacing = true
quote_spacing = true
cjk_english_spacing = true
space_collapsing = true

# Define custom regex rules
[[custom_rules]]
name = "arrow_unicode"
pattern = '->'
replacement = '→'
description = "Use Unicode arrows"

[[custom_rules]]
name = "multiply_sign"
pattern = '(\d+)\s*x\s*(\d+)'
replacement = '\1×\2'
description = "Use proper multiplication sign"
```

### Built-in Rules

| Rule | Default | Description |
|------|---------|-------------|
| **Universal Rules** | | |
| `ellipsis_normalization` | ✅ | Convert `. . .` to `...` |
| **Quote & Em-dash** | | |
| `quote_spacing` | ✅ | Add spaces around `""` with smart CJK handling |
| `single_quote_spacing` | ✅ | Add spaces around `''` with smart CJK handling |
| `dash_conversion` | ✅ | Convert `--` to `——` |
| `emdash_spacing` | ✅ | Fix spacing around `——` |
| **Normalization** | | |
| `fullwidth_punctuation` | ✅ | Normalize `,` `.` `!` `?` `;` `:` width |
| `fullwidth_parentheses` | ✅ | Normalize `()` → `（）` in CJK |
| `fullwidth_brackets` | ❌ | Normalize `[]` → `【】` in CJK (off by default) |
| `fullwidth_alphanumeric` | ✅ | Convert `１２３ＡＢＣ` → `123ABC` |
| **Spacing & Cleanup** | | |
| `cjk_english_spacing` | ✅ | Space between Chinese & English/numbers |
| `currency_spacing` | ✅ | Remove space: `$ 100` → `$100` |
| `slash_spacing` | ✅ | Remove space: `A / B` → `A/B` |
| `space_collapsing` | ✅ | Collapse multiple spaces (preserve indents) |
| `consecutive_punctuation_limit` | 0 | Limit repeats: `！！！` → `！` (0=off, 1=single, 2=double) |

### Custom Rules

Add your own regex-based transformations:

```toml
[[custom_rules]]
name = "rule_name"              # Identifier (required)
pattern = 'regex pattern'       # Regex to match (required)
replacement = 'replacement'     # Replacement text (required)
description = "What it does"    # Optional description
```

**Examples:**

```toml
# Unicode fractions
[[custom_rules]]
name = "fraction_half"
pattern = '\b1/2\b'
replacement = '½'

# Temperature symbols
[[custom_rules]]
name = "celsius"
pattern = '(\d+)\s*C\b'
replacement = '\1°C'

# Smart quotes
[[custom_rules]]
name = "double_quotes"
pattern = '"([^"]+)"'
replacement = '"\1"'
```

### Usage with Config

```bash
# Use project config (auto-detected)
ctf input.txt

# Use specific config file
ctf input.txt --config my-rules.toml

# Show what changed (verbose mode)
ctf input.txt --verbose

# Disable a rule temporarily (edit config file)
# Set: dash_conversion = false
```

### Validating Config Files

```bash
# Validate a config file
ctf --validate-config cjk-text-formatter.toml

# Example output for valid config:
# Validating: cjk-text-formatter.toml
# ✓ Configuration is valid

# Example output for invalid config:
# Validating: cjk-text-formatter.toml
# Errors:
#   ✗ Unknown rule name: 'unknown_rule'. Valid rules: ...
#   ✗ custom_rules[0] (bad_regex): Invalid regex pattern: ...
```

**What gets validated:**
- ✅ File exists and is readable
- ✅ Valid TOML syntax
- ✅ Rule names match known built-in rules
- ✅ Custom rules have required fields (`name`, `pattern`, `replacement`)
- ✅ Regex patterns compile successfully

### Showing Effective Config

```bash
# Show which config is active and what rules are enabled
ctf --show-config

# With custom config
ctf --show-config --config my-rules.toml

# Example output:
# Effective Configuration:
#
# Config Source:
#   Project: ./cjk-text-formatter.toml
#
# Built-in Rules:
#   ✓ cjk_english_spacing: True
#   ✗ dash_conversion: False
#   ...
#
# Custom Rules:
#   [1] unicode_arrows
#       pattern: ->
#       replacement: →
#       description: Use Unicode right arrow
```

## Typography Rules

### Em-Dash Spacing

| Before | After | Rule |
|--------|-------|------|
| `text--more` | `text —— more` | Regular text: spaces on both sides |
| `《书名》--作者` | `《书名》—— 作者` | After `》`: no space before `——`, space after |
| `作者--《书名》` | `作者 ——《书名》` | Before `《`: space before `——`, no space after |
| `（注释）--内容` | `（注释）—— 内容` | After `）`: no space before `——`, space after |
| `内容--（注释）` | `内容 ——（注释）` | Before `（`: space before `——`, no space after |

### CJK-English Spacing

| Before | After |
|--------|-------|
| `中文English` | `中文 English` |
| `数字123` | `数字 123` |
| `100个item` | `100 个 item` |

### Quote Spacing (Smart CJK Punctuation Handling)

The quote spacing rule intelligently avoids adding spaces when quotes are adjacent to CJK punctuation that already has visual spacing built-in:

| Before | After | Rule |
|--------|-------|------|
| `文本"引用"文本` | `文本 "引用" 文本` | Regular text: add spaces for readability |
| `文本，"引用"。` | `文本，"引用"。` | Punctuation ，。: NO space (already has visual spacing) |
| `《书名》"引用"（注）` | `《书名》"引用"（注）` | Brackets 《》（）: NO space (already has visual spacing) |
| `前文——"引用"——后文` | `前文——"引用"——后文` | Em-dash ——: NO space (already has visual spacing) |
| `English"中文"123` | `English "中文" 123` | Alphanumeric: add spaces for readability |

**CJK punctuation excluded from spacing:**
- Terminal punctuation: ，。！？；：、
- Book title marks & corner brackets: 《》「」『』
- Brackets: 【】（）〈〉
- Em-dash: ——

### Ellipsis Normalization

| Before | After |
|--------|-------|
| `. . .` | `...` |
| `wait . . . more` | `wait... more` |
| `end . . . .` | `end...` |

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=cjk_text_formatter

# Run specific test file
pytest tests/test_polish.py -v
```

### Project Structure

```
cjk-text-formatter/
├── src/
│   └── cjk_text_formatter/
│       ├── __init__.py
│       ├── polish.py        # Core polishing logic
│       ├── processors.py    # File type processors
│       ├── config.py        # Configuration management
│       └── cli.py           # Command-line interface
├── tests/
│   ├── test_polish.py       # Polish function tests
│   ├── test_processors.py  # File processor tests
│   ├── test_config.py      # Configuration tests
│   └── test_config_validation.py
├── pyproject.toml           # Package configuration
└── README.md
```

### Adding New Rules

To add a new typography rule:

1. **Add tests** in `tests/test_polish.py`:
   ```python
   def test_new_rule(self):
       assert polish_text("input") == "expected_output"
   ```

2. **Implement the rule** in `src/cjk_text_formatter/polish.py`:
   ```python
   def _new_rule(text: str) -> str:
       # Implementation
       return text
   ```

3. **Add to pipeline** in `polish_text()`:
   ```python
   def polish_text(text: str) -> str:
       text = _normalize_ellipsis(text)
       text = _new_rule(text)  # Add your rule
       # ... rest of pipeline
       return text.strip()
   ```

## Options

| Option | Short | Description |
|--------|-------|-------------|
| `--output PATH` | `-o` | Output file path |
| `--inplace` | `-i` | Modify files in place |
| `--recursive` | `-r` | Process directories recursively |
| `--dry-run` | `-n` | Preview changes without writing |
| `--extensions EXT` | `-e` | File extensions to process (e.g., `-e .txt -e .md`) |
| `--verbose` | `-v` | Show summary of changes made |
| `--config PATH` | `-c` | Path to custom config file |
| `--validate-config PATH` | | Validate config file and exit |
| `--show-config` | | Show effective configuration and exit |
| `--version` | | Show version and exit |

## Examples

### Format Chinese-English Mixed Content

```bash
$ ctf "Python是一门编程语言，有3.11版本。"
Python 是一门编程语言，有 3.11 版本。
```

### Format Book Titles with Em-Dash

```bash
$ ctf "《人生》--路遥著"
《人生》—— 路遥著
```

### Batch Process Markdown Files

```bash
# Format all markdown files in docs/ and subdirectories
ctf ./docs/ --recursive --inplace -e .md

# Preview changes first
ctf ./docs/ --recursive --dry-run -e .md
```

### Process with Preserved Code Blocks

Markdown code blocks are automatically preserved:

```bash
$ cat document.md
# 标题Title

文本English混合

\`\`\`python
# This code won't be formatted
text--more
\`\`\`

$ ctf document.md --inplace
$ cat document.md
# 标题 Title

文本 English 混合

\`\`\`python
# This code won't be formatted
text--more
\`\`\`
```

## License

MIT License

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass: `pytest`
5. Submit a pull request

## Author

Created by Xiaolai for the TEPUB project.

Originally developed as part of [TEPUB](https://github.com/xiaolai/tepub), a tool for EPUB translation and audiobook generation.
