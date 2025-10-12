"""File processors for different file types."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import List

from .config import RuleConfig
from .polish import polish_text, EXCESSIVE_NEWLINE_PATTERN


def validate_safe_path(file_path: Path, base_dir: Path | None = None) -> Path:
    """Validate that a file path doesn't attempt path traversal.

    Args:
        file_path: Path to validate
        base_dir: Optional base directory to restrict paths within

    Returns:
        Resolved absolute path

    Raises:
        ValueError: If path attempts to escape base directory or contains suspicious patterns
    """
    # Resolve to absolute path
    resolved = file_path.resolve()

    # Check for suspicious patterns that might indicate path traversal attempts
    path_str = str(file_path)
    if '..' in path_str or path_str.startswith('/'):
        # Only allow these if the resolved path is safe
        pass

    # If base_dir specified, ensure path doesn't escape it
    if base_dir:
        base_resolved = base_dir.resolve()
        try:
            # Check if resolved path is within base directory
            resolved.relative_to(base_resolved)
        except ValueError:
            raise ValueError(
                f"Path '{file_path}' attempts to access files outside allowed directory '{base_dir}'"
            )

    return resolved


class TextProcessor:
    """Processor for plain text files."""

    def process(self, text: str, config: RuleConfig | None = None) -> str:
        """Process plain text content.

        Args:
            text: Text content to process
            config: Optional rule configuration

        Returns:
            Polished text
        """
        return polish_text(text, config)


class MarkdownProcessor:
    """Processor for Markdown files that preserves code blocks."""

    def process(self, text: str, config: RuleConfig | None = None) -> str:
        """Process Markdown content, preserving code blocks.

        Preserves:
        - Fenced code blocks (```...```)
        - Indented code blocks (4-space indent)
        - Inline code (`...`)

        Args:
            text: Markdown content to process
            config: Optional rule configuration

        Returns:
            Polished markdown with code blocks preserved
        """
        # Strategy: Replace code blocks with placeholders, process, then restore

        # Store code blocks
        code_blocks = []

        def save_code(match):
            code_blocks.append(match.group(0))
            return f"___CODE_BLOCK_{len(code_blocks)-1}___"

        # Save fenced code blocks (```...```)
        text = re.sub(r'```[\s\S]*?```', save_code, text)

        # Save inline code (`...`)
        text = re.sub(r'`[^`\n]+?`', save_code, text)

        # Process lines, preserving indented code blocks
        lines = text.split('\n')
        processed_lines = []
        in_indented_code = False

        for line in lines:
            # Check if line is indented code block (4+ spaces or tab at start)
            is_code_line = line.startswith('    ') or line.startswith('\t')

            # Detect start/end of indented code blocks
            if is_code_line and not in_indented_code:
                in_indented_code = True
            elif not is_code_line and not line.strip() == '' and in_indented_code:
                in_indented_code = False

            # Only process non-code lines
            if not in_indented_code and not is_code_line:
                line = polish_text(line, config)

            processed_lines.append(line)

        text = '\n'.join(processed_lines)

        # Apply universal newline collapsing (3+ → 2, one blank line max)
        # This must be done after joining lines, as line-by-line processing
        # prevents the pattern from matching consecutive newlines
        text = EXCESSIVE_NEWLINE_PATTERN.sub("\n\n", text)

        # Restore code blocks
        for i, code_block in enumerate(code_blocks):
            text = text.replace(f"___CODE_BLOCK_{i}___", code_block)

        return text


class HTMLProcessor:
    """Processor for HTML files that preserves structure."""

    def __init__(self):
        """Initialize HTML processor."""
        try:
            from bs4 import BeautifulSoup
            self._bs4_available = True
        except ImportError:
            self._bs4_available = False

    def process(self, html: str, config: RuleConfig | None = None) -> str:
        """Process HTML content, formatting text while preserving structure.

        Preserves:
        - All HTML tags and attributes
        - Content in <code> and <pre> tags

        Args:
            html: HTML content to process
            config: Optional rule configuration

        Returns:
            HTML with polished text content
        """
        if self._bs4_available:
            return self._process_with_bs4(html, config)
        else:
            return self._process_simple(html, config)

    def _process_with_bs4(self, html: str, config: RuleConfig | None = None) -> str:
        """Process HTML using BeautifulSoup."""
        from bs4 import BeautifulSoup, NavigableString

        soup = BeautifulSoup(html, 'html.parser')

        # Tags whose content should NOT be formatted
        skip_tags = {'code', 'pre', 'script', 'style'}

        def process_element(element):
            """Recursively process element tree."""
            if element.name in skip_tags:
                return  # Don't process content in these tags

            for child in element.children:
                if isinstance(child, NavigableString):
                    # Process text nodes
                    if child.string and child.string.strip():
                        polished = polish_text(str(child.string), config)
                        child.replace_with(polished)
                elif hasattr(child, 'children'):
                    # Recursively process child elements
                    process_element(child)

        # Process the document
        if soup.body:
            process_element(soup.body)
        else:
            # No body tag, process entire soup
            for element in soup.children:
                if hasattr(element, 'children'):
                    process_element(element)

        return str(soup)

    def _process_simple(self, html: str, config: RuleConfig | None = None) -> str:
        """Process HTML with simple regex-based approach (no BeautifulSoup).

        This is a fallback for when BeautifulSoup is not available.
        It's less robust but handles simple cases.
        """
        # Save code/pre blocks
        code_blocks = []

        def save_code(match):
            code_blocks.append(match.group(0))
            return f"___HTML_CODE_{len(code_blocks)-1}___"

        # Save <code>...</code> and <pre>...</pre> blocks
        html = re.sub(r'<code[^>]*>[\s\S]*?</code>', save_code, html, flags=re.IGNORECASE)
        html = re.sub(r'<pre[^>]*>[\s\S]*?</pre>', save_code, html, flags=re.IGNORECASE)

        # Extract and process text between tags
        def process_text(match):
            text = match.group(0)
            # Don't process if it's inside a tag
            if text.strip():
                return polish_text(text, config)
            return text

        # Process text between tags (simple approach)
        html = re.sub(r'>([^<]+)<', lambda m: f'>{polish_text(m.group(1), config)}<', html)

        # Restore code blocks
        for i, code_block in enumerate(code_blocks):
            html = html.replace(f"___HTML_CODE_{i}___", code_block)

        return html


def process_file(file_path: Path, config: RuleConfig | None = None) -> str:
    """Process a file based on its extension.

    Args:
        file_path: Path to file to process
        config: Optional rule configuration

    Returns:
        Processed content

    Raises:
        ValueError: If file type is not supported or path is invalid
    """
    # Validate path (resolves to absolute path, checks for safety)
    validated_path = validate_safe_path(file_path)

    suffix = validated_path.suffix.lower()

    if suffix == '.txt':
        processor = TextProcessor()
    elif suffix == '.md':
        processor = MarkdownProcessor()
    elif suffix in ['.html', '.htm']:
        processor = HTMLProcessor()
    else:
        raise ValueError(f"Unsupported file type: {suffix}")

    content = validated_path.read_text(encoding='utf-8')
    return processor.process(content, config)


def find_files(
    path: Path,
    recursive: bool = False,
    extensions: List[str] | None = None,
) -> List[Path]:
    """Find files to process.

    Args:
        path: File or directory path
        recursive: Whether to search recursively in subdirectories
        extensions: List of file extensions to include (e.g., ['.txt', '.md'])
                   If None, defaults to ['.txt', '.md', '.html', '.htm']

    Returns:
        List of file paths to process

    Raises:
        FileNotFoundError: If path does not exist
    """
    if not path.exists():
        raise FileNotFoundError(f"Path does not exist: {path}")

    if extensions is None:
        extensions = ['.txt', '.md', '.html', '.htm']

    # Normalize extensions to lowercase
    extensions = [ext.lower() if ext.startswith('.') else f'.{ext.lower()}'
                  for ext in extensions]

    if path.is_file():
        return [path]

    # Path is a directory
    files = []
    pattern = '**/*' if recursive else '*'

    for file_path in path.glob(pattern):
        if file_path.is_file() and file_path.suffix.lower() in extensions:
            files.append(file_path)

    return sorted(files)
