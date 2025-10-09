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
