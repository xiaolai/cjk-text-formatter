# Text Formater

A Python CLI tool for polishing text with Chinese typography rules. Automatically formats mixed Chinese-English text, fixes em-dash spacing, normalizes ellipsis, and more.

## Features

### Universal Rules (All Languages)
- **Ellipsis normalization**: Converts `. . .` or `. . . .` to `...` with proper spacing

### Chinese-Specific Rules
- **Em-dash spacing**: Converts `--` to `——` with smart spacing around Chinese quotes `《》` and parentheses `（）`
- **Quote spacing**: Adds spaces around Chinese quotation marks `""`
- **CJK-English spacing**: Automatically adds spaces between Chinese characters and English letters/numbers
- **Multiple space collapsing**: Reduces consecutive spaces to single space

### File Type Support
- **Plain Text** (`.txt`): Direct formatting
- **Markdown** (`.md`): Preserves code blocks (fenced, indented, inline)
- **HTML** (`.html`, `.htm`): Formats text content while preserving tags and `<code>`/`<pre>` elements

## Installation

### Requirements

- Python 3.8 or higher

### Install from PyPI

```bash
# Basic installation
pip install text-formater

# With HTML support (optional)
pip install text-formater[html]
```

### Install from Source

```bash
git clone https://github.com/xiaolai/text-formater.git
cd text-formater
pip install -e .

# Or with HTML support
pip install -e ".[html]"
```

### Verify Installation

```bash
# Check version
textformat --version

# Show help
textformat --help

# Quick test
textformat "文本English混合"
# Expected output: 文本 English 混合
```

## Usage

### Command Line

```bash
# Format text directly
textformat "文本English混合"
# Output: 文本 English 混合

# Format with em-dash
textformat "《书名》--作者"
# Output: 《书名》—— 作者

# Read from stdin
echo "文本English混合" | textformat

# Format a single file
textformat input.txt
textformat input.md --output formatted.md

# Format in-place
textformat document.txt --inplace

# Preview changes without writing (dry-run)
textformat document.txt --dry-run

# Format all files in a directory
textformat ./docs/ --inplace
textformat ./docs/ --recursive --inplace

# Format specific file types only
textformat ./docs/ --inplace -e .md -e .txt
```

### Python API

```python
from textformater.polish import polish_text

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
from textformater.processors import process_file, find_files

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

1. **Custom path**: `textformat --config /path/to/config.toml`
2. **Project root**: `./textformat.toml`
3. **User config**: `~/.config/textformat.toml`
4. **Defaults**: All rules enabled

### Quick Start

```bash
# Copy example config to your project
cp textformat.toml.example textformat.toml

# Or to user config
cp textformat.toml.example ~/.config/textformat.toml

# Edit and customize rules
```

### Configuration Format

```toml
# textformat.toml

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
| `ellipsis_normalization` | ✅ | Convert `. . .` to `...` |
| `dash_conversion` | ✅ | Convert `--` to `——` |
| `emdash_spacing` | ✅ | Fix spacing around `——` |
| `quote_spacing` | ✅ | Add spaces around `""` |
| `cjk_english_spacing` | ✅ | Space between Chinese & English |
| `space_collapsing` | ✅ | Collapse multiple spaces |

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
textformat input.txt

# Use specific config file
textformat input.txt --config my-rules.toml

# Show what changed (verbose mode)
textformat input.txt --verbose

# Disable a rule temporarily (edit config file)
# Set: dash_conversion = false
```

### Validating Config Files

```bash
# Validate a config file
textformat --validate-config textformat.toml

# Example output for valid config:
# Validating: textformat.toml
# ✓ Configuration is valid

# Example output for invalid config:
# Validating: textformat.toml
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
textformat --show-config

# With custom config
textformat --show-config --config my-rules.toml

# Example output:
# Effective Configuration:
#
# Config Source:
#   Project: ./textformat.toml
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
pytest --cov=textformater

# Run specific test file
pytest tests/test_polish.py -v
```

### Project Structure

```
text-formater/
├── src/
│   └── textformater/
│       ├── __init__.py
│       ├── polish.py        # Core polishing logic
│       ├── processors.py    # File type processors
│       └── cli.py           # Command-line interface
├── tests/
│   ├── test_polish.py       # Polish function tests
│   └── test_processors.py  # File processor tests
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

2. **Implement the rule** in `src/textformater/polish.py`:
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
$ textformat "Python是一门编程语言，有3.11版本。"
Python 是一门编程语言，有 3.11 版本。
```

### Format Book Titles with Em-Dash

```bash
$ textformat "《人生》--路遥著"
《人生》—— 路遥著
```

### Batch Process Markdown Files

```bash
# Format all markdown files in docs/ and subdirectories
textformat ./docs/ --recursive --inplace -e .md

# Preview changes first
textformat ./docs/ --recursive --dry-run -e .md
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

$ textformat document.md --inplace
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
