# Contributing to CJK Text Formatter

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help others learn and grow

## Getting Started

### Development Setup

```bash
# Clone the repository
git clone https://github.com/xiaolai/cjk-text-formatter.git
cd cjk-text-formatter

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode with dev dependencies
pip install -e ".[dev,html]"

# Run tests
pytest
```

## How to Contribute

### Reporting Bugs

-  Use the GitHub issue tracker
- Include Python version, OS, and cjk-text-formatter version
- Provide minimal reproduction steps
- Include actual vs. expected behavior

### Suggesting Features

- Check existing issues first
- Explain the use case clearly
- Consider backward compatibility

### Pull Requests

1. **Fork and Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Changes**
   - Follow existing code style
   - Add tests for new functionality
   - Update documentation as needed

3. **Test**
   ```bash
   pytest  # All tests must pass
   pytest --cov=cjk_text_formatter  # Check coverage
   ```

4. **Commit**
   - Use clear, descriptive commit messages
   - Reference issues when applicable

5. **Push and Create PR**
   ```bash
   git push origin feature/your-feature-name
   ```

## Code Style

### Python Style
- Follow PEP 8
- Use type hints (Python 3.8+ style)
- Maximum line length: 100 characters
- Use descriptive variable names

### Naming Conventions
- Functions/variables: `snake_case`
- Classes: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`
- Private functions: `_leading_underscore`

### Documentation
- Add docstrings to all public functions
- Use Google-style docstrings
- Update README.md for user-facing changes

## Testing Guidelines

### Writing Tests
- Place tests in `tests/` directory
- Mirror source structure (e.g., `test_polish.py` for `polish.py`)
- Use descriptive test names: `test_feature_description()`

### Test Coverage
- Aim for >80% coverage on new code
- Test edge cases and error conditions
- Include integration tests for complex features

### Example Test
```python
def test_ellipsis_normalization(self):
    """Test that spaced ellipsis is normalized."""
    text = "wait . . . more"
    expected = "wait... more"
    assert polish_text(text) == expected
```

## Adding New Rules

### 1. Write Tests First
```python
# tests/test_polish.py
def test_new_rule(self):
    assert polish_text("input") == "expected"
```

### 2. Implement the Rule
```python
# src/cjk_text_formatter/polish.py

# Add regex pattern at module level
NEW_RULE_PATTERN = re.compile(r"pattern")

def _new_rule(text: str) -> str:
    """Description of what this rule does."""
    return NEW_RULE_PATTERN.sub("replacement", text)
```

### 3. Add to Pipeline
```python
# In polish_text()
if config.is_enabled('new_rule'):
    text = _new_rule(text)
```

### 4. Add to Configuration
```python
# src/cjk_text_formatter/config.py
DEFAULT_RULES = {
    # ... existing rules
    'new_rule': True,
}
```

### 5. Update Documentation
- Add rule to README.md
- Document in ARCHITECTURE.md if significant

## Project Structure

```
cjk-text-formatter/
├── src/cjk_text_formatter/
│   ├── __init__.py
│   ├── polish.py         # Core text processing
│   ├── processors.py     # File type handlers
│   ├── config.py         # Configuration
│   └── cli.py            # Command-line interface
├── tests/
│   ├── test_polish.py
│   ├── test_processors.py
│   ├── test_config.py
│   └── test_config_validation.py
├── README.md
├── ARCHITECTURE.md
├── CONTRIBUTING.md (this file)
└── pyproject.toml
```

## Release Process

(For maintainers)

1. Update version in `src/cjk_text_formatter/__init__.py`
2. Update `pyproject.toml`
3. Update CHANGELOG (if exists)
4. Create git tag
5. Build and publish to PyPI

## Questions?

- Open an issue for questions
- Email: xiaolaidev@gmail.com

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to CJK Text Formatter!
