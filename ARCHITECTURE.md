# Architecture

## Overview

CJK Text Formatter is a Python CLI tool that applies typography rules to text containing Chinese, Japanese, and Korean (CJK) characters. The architecture follows a clear pipeline pattern:

```
Input → Polishing → Processing → Output
```

## Core Components

### 1. Polish Module (`polish.py`)

**Purpose**: Core text transformation logic

**Design Principles**:
- **Stateless Functions**: All polishing functions are pure (no side effects)
- **Regex-Based**: Fast, deterministic text transformations using pre-compiled regex patterns
- **Modular Rules**: Each typography rule is a separate function for easy testing and maintenance
- **Performance Optimized**: Regex patterns compiled at module level for reuse

**Key Functions**:
- `polish_text()`: Main entry point, applies all enabled rules
- `polish_text_verbose()`: Same as above but returns statistics
- `_fix_quote_spacing()`: Generic quote spacing handler (DRY principle)
- Individual rule functions: `_normalize_ellipsis()`, `_replace_dash()`, etc.

**Constants**:
- `CJK_TERMINAL_PUNCTUATION`, `CJK_CLOSING_BRACKETS`, etc.: Centralized CJK character definitions
- Pre-compiled regex patterns: `ELLIPSIS_PATTERN`, `DASH_PATTERN`, etc.

### 2. Processors Module (`processors.py`)

**Purpose**: File type-specific handling

**Design Principles**:
- **Strategy Pattern**: Different processor classes for different file types
- **Content Preservation**: Code blocks and special markup preserved during processing
- **Security**: Path validation to prevent traversal attacks

**Processors**:
- `TextProcessor`: Simple text processing
- `MarkdownProcessor`: Preserves fenced code blocks, indented code, and inline code
- `HTMLProcessor`: Preserves HTML tags and `<code>`/`<pre>` elements (uses BeautifulSoup when available)

**Key Functions**:
- `process_file()`: Dispatches to appropriate processor based on file extension
- `find_files()`: Recursively finds files with specific extensions
- `validate_safe_path()`: Security validation for file paths

### 3. Configuration Module (`config.py`)

**Purpose**: TOML-based configuration loading and validation

**Design Principles**:
- **Priority System**: Explicit > Project > User > Defaults
- **Validation**: Comprehensive config file validation before use
- **Python 3.11+ Only**: Uses built-in `tomllib` (graceful fallback for older versions)

**Configuration Flow**:
```
1. Load defaults (DEFAULT_RULES)
2. Merge user config (~/.config/cjk-text-formatter.toml)
3. Merge project config (./cjk-text-formatter.toml)
4. Merge explicit config (--config flag)
```

**Key Classes**:
- `RuleConfig`: Dataclass holding enabled rules and custom rules
- `ValidationResult`: Validation report with errors and warnings

### 4. CLI Module (`cli.py`)

**Purpose**: Command-line interface using Click framework

**Design Principles**:
- **User-Friendly**: Clear error messages and help text
- **Flexible Input**: Accepts text strings, files, directories, or stdin
- **Safe Defaults**: Dry-run mode available, confirmation required for batch operations

**Key Functions**:
- `main()`: CLI entry point with argument parsing
- `process_single_file()`: Handles single file processing
- `process_directory()`: Handles batch directory processing
- `_show_effective_config()`: Displays current configuration

## Data Flow

### Single File Processing
```
User Input (file path)
    ↓
validate_safe_path() [security check]
    ↓
process_file() [determine processor]
    ↓
TextProcessor/MarkdownProcessor/HTMLProcessor
    ↓
polish_text() [apply rules]
    ↓
Output (stdout/file)
```

### Directory Processing
```
User Input (directory path + options)
    ↓
find_files() [discover files]
    ↓
For each file:
    process_file() → polish_text() → write
    ↓
Summary report
```

### Configuration Loading
```
--config flag OR auto-discovery
    ↓
_load_toml_file() [parse TOML]
    ↓
_merge_config_data() [merge with defaults]
    ↓
RuleConfig [used by polish_text()]
```

## Design Decisions

### Why Stateless Processing?

**Decision**: All text processing functions are pure (no side effects)

**Rationale**:
- Easier to test (no setup/teardown needed)
- Thread-safe by default
- Composable and reusable
- Predictable behavior

**Trade-off**: Can't maintain state across calls, but this isn't needed for text processing

### Why Regex Over Parser?

**Decision**: Use regex-based transformations instead of parsing

**Rationale**:
- Fast performance for typical document sizes
- Deterministic behavior
- Easy to understand and modify
- No complex parser dependencies

**Trade-off**: Complex nested structures harder to handle, but not required for typography rules

### Why File Type Preservation?

**Decision**: Preserve code blocks and special markup during processing

**Rationale**:
- Code should remain unchanged (formatting breaks syntax)
- Respect original author's intent for code examples
- Prevent data loss or corruption

**Implementation**: Replace code blocks with placeholders → process → restore

### Why Pre-compiled Regex?

**Decision**: Compile regex patterns at module level (v0.3.1+)

**Rationale**:
- Performance improvement for repeated use
- Patterns compiled once, reused many times
- Especially beneficial for large files or batch processing

**Previous Approach**: Compiled patterns on each function call (slower)

### Why TOML Configuration?

**Decision**: Use TOML for configuration instead of JSON/YAML

**Rationale**:
- Human-readable and writable
- Native Python support (Python 3.11+ built-in)
- Type-safe parsing
- Good for application configuration

**Trade-off**: Requires Python 3.11+ for built-in support (graceful fallback provided)

### Why Click Framework?

**Decision**: Use Click for CLI instead of argparse

**Rationale**:
- More user-friendly API
- Better error messages
- Automatic help generation
- Supports complex command structures

## Performance Considerations

### Regex Compilation
- **Before (v0.3.0)**: Regex compiled on every function call
- **After (v0.3.1)**: Pre-compiled at module level
- **Improvement**: ~20-30% faster for batch processing

### File Processing
- **Memory**: Files loaded entirely into memory (suitable for documents)
- **Streaming**: Not implemented (current design optimized for typical use case)
- **Future**: Consider streaming for very large files (>100MB)

### Caching
- **Current**: No caching (stateless design)
- **Future**: Could cache compiled custom regex rules from config

## Testing Strategy

### Unit Tests
- Each polishing function tested independently
- Edge cases and boundary conditions covered
- Configuration validation tested thoroughly

### Integration Tests
- File processing tested end-to-end
- CLI tested with Click's test runner
- Configuration loading tested with real TOML files

### Test Coverage
- Target: >80% for critical paths
- Current: ~87% (1,370 test lines for 1,578 source lines)

## Security Architecture

### Path Validation
- All file paths validated before use
- Resolved to absolute paths
- Optional base directory restriction

### Configuration Safety
- Only known rule names accepted
- Custom regex patterns validated before use
- Invalid config causes graceful fallback

### Input Handling
- File encoding explicitly specified (UTF-8)
- Error handling for invalid input
- No dangerous functions (`eval`, `exec`) used

## Extension Points

### Adding New Rules
1. Create `_new_rule(text: str) -> str` function
2. Add regex pattern to module-level constants (if needed)
3. Add rule to `polish_text()` pipeline
4. Add to `DEFAULT_RULES` in `config.py`
5. Write tests in `test_polish.py`

### Adding New File Types
1. Create `NewFileProcessor` class
2. Implement `process(text: str) -> str` method
3. Add file extension mapping in `process_file()`
4. Write tests in `test_processors.py`

### Adding New CLI Commands
1. Add Click command/option in `cli.py`
2. Implement handler function
3. Update help text and documentation
4. Write tests using Click's test runner

## Future Improvements

### Planned
- Streaming support for large files
- Plugin system for custom processors
- Language-specific rule sets (Japanese, Korean)
- Performance metrics and profiling

### Under Consideration
- Web API/service version
- IDE integrations
- GitHub Action for automated formatting
- Language server protocol (LSP) support

## Module Dependencies

```
cli.py
  ├── config.py (tomllib)
  ├── polish.py
  └── processors.py
      └── polish.py

config.py
  └── tomllib (Python 3.11+)

processors.py
  ├── polish.py
  └── beautifulsoup4 (optional, for HTML)

polish.py
  └── re (standard library)
```

## Versioning Strategy

- **Semantic Versioning**: MAJOR.MINOR.PATCH
- **Breaking Changes**: Increment MAJOR (e.g., 0.3.0 → 1.0.0)
- **New Features**: Increment MINOR (e.g., 0.3.0 → 0.4.0)
- **Bug Fixes**: Increment PATCH (e.g., 0.3.0 → 0.3.1)

## Contact

For architecture questions or proposals:
**xiaolaidev@gmail.com**

Originally developed as part of [TEPUB](https://github.com/xiaolai/tepub).
