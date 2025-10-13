"""Tests for file processors."""

import pytest
from pathlib import Path
from cjk_text_formatter.processors import (
    TextProcessor,
    MarkdownProcessor,
    HTMLProcessor,
    process_file,
    find_files,
)


class TestTextProcessor:
    """Test plain text file processing."""

    def test_process_simple_text(self):
        processor = TextProcessor()
        text = "文本English混合，数字123也包含。"
        result = processor.process(text)
        assert "文本 English" in result
        assert "数字 123" in result

    def test_process_with_ellipsis(self):
        processor = TextProcessor()
        text = "wait . . . more text"
        result = processor.process(text)
        assert result == "wait... more text"

    def test_process_with_em_dash(self):
        processor = TextProcessor()
        text = "《书名》--作者"
        result = processor.process(text)
        assert result == "《书名》—— 作者"


class TestMarkdownProcessor:
    """Test markdown file processing."""

    def test_preserve_code_blocks_fenced(self):
        processor = MarkdownProcessor()
        text = """文本内容

```python
def hello():
    print("world")
```

更多文本"""
        result = processor.process(text)
        # Code blocks should be preserved exactly
        assert '```python' in result
        assert 'def hello():' in result
        assert '    print("world")' in result

    def test_preserve_code_blocks_indented(self):
        processor = MarkdownProcessor()
        text = """文本内容

    code line 1
    code line 2

更多文本"""
        result = processor.process(text)
        # Indented code blocks should be preserved
        assert '    code line 1' in result
        assert '    code line 2' in result

    def test_preserve_inline_code(self):
        processor = MarkdownProcessor()
        text = "文本`code here`更多文本"
        result = processor.process(text)
        assert "`code here`" in result

    def test_format_text_outside_code(self):
        processor = MarkdownProcessor()
        text = """# 标题Title

文本English混合

```python
# This should not be formatted
text--more
```

数字123也包含"""
        result = processor.process(text)
        # Text outside code should be formatted
        assert "文本 English" in result
        assert "数字 123" in result
        # Code inside should NOT be formatted
        assert "text--more" in result  # Should remain unchanged

    def test_preserve_indented_list_items(self):
        """Test that indented list items preserve their indentation."""
        processor = MarkdownProcessor()
        # Use 2-space indents (list items), not 4+ spaces (code blocks)
        text = """- 第一级English项目
  - 第二级nested项目
  - 另一个second项目
- 回到first级别"""
        result = processor.process(text)
        # List items should be formatted
        assert "第一级 English" in result
        assert "第二级 nested" in result
        assert "另一个 second" in result
        assert "回到 first" in result
        # But indentation should be preserved
        assert "  - 第二级 nested" in result
        assert "  - 另一个 second" in result

    def test_preserve_list_item_indentation_two_space(self):
        """Test that 2-space indented list items are processed (not treated as code)."""
        processor = MarkdownProcessor()
        text = """普通text行
  缩进的content行
回到normal级别"""
        result = processor.process(text)
        # Text should be formatted
        assert "普通 text" in result
        assert "缩进的 content" in result
        assert "回到 normal" in result
        # Indentation should be preserved
        lines = result.split('\n')
        assert lines[0] == "普通 text 行"
        assert lines[1].startswith("  ")  # 2 spaces preserved
        assert "缩进的 content 行" in lines[1]
        assert not lines[2].startswith(" ")  # No leading spaces


class TestHTMLProcessor:
    """Test HTML file processing."""

    def test_format_text_preserve_tags(self):
        processor = HTMLProcessor()
        html = "<p>文本English混合</p>"
        result = processor.process(html)
        # Text should be formatted
        assert "文本 English" in result
        # Tags should be preserved
        assert "<p>" in result
        assert "</p>" in result

    def test_preserve_code_tags(self):
        processor = HTMLProcessor()
        html = "<p>文本<code>text--more</code>内容</p>"
        result = processor.process(html)
        # Code content should NOT be formatted
        assert "text--more" in result
        assert "<code>" in result

    def test_preserve_pre_tags(self):
        processor = HTMLProcessor()
        html = "<pre>text--more\nline2--end</pre>"
        result = processor.process(html)
        # Pre content should NOT be formatted
        assert "text--more" in result
        assert "line2--end" in result

    def test_format_nested_elements(self):
        processor = HTMLProcessor()
        html = """<div>
    <h1>标题Title</h1>
    <p>文本English混合</p>
</div>"""
        result = processor.process(html)
        assert "标题 Title" in result
        assert "文本 English" in result
        assert "<div>" in result
        assert "</div>" in result

    def test_handle_attributes(self):
        processor = HTMLProcessor()
        html = '<a href="link">文本English</a>'
        result = processor.process(html)
        assert "文本 English" in result
        assert 'href="link"' in result


class TestProcessFile:
    """Test file processing dispatcher."""

    def test_process_txt_file(self, tmp_path):
        # Create test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("文本English混合")

        result = process_file(test_file)
        assert "文本 English" in result

    def test_process_md_file(self, tmp_path):
        test_file = tmp_path / "test.md"
        test_file.write_text("# 标题Title\n\n文本English混合")

        result = process_file(test_file)
        assert "标题 Title" in result
        assert "文本 English" in result

    def test_process_html_file(self, tmp_path):
        test_file = tmp_path / "test.html"
        test_file.write_text("<p>文本English混合</p>")

        result = process_file(test_file)
        assert "文本 English" in result
        assert "<p>" in result

    def test_unsupported_file_type(self, tmp_path):
        test_file = tmp_path / "test.xyz"
        test_file.write_text("content")

        with pytest.raises(ValueError, match="Unsupported file type"):
            process_file(test_file)


class TestFindFiles:
    """Test file finding functionality."""

    def test_find_single_file(self, tmp_path):
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")

        files = find_files(test_file)
        assert len(files) == 1
        assert files[0] == test_file

    def test_find_files_in_directory_non_recursive(self, tmp_path):
        # Create files
        (tmp_path / "file1.txt").write_text("1")
        (tmp_path / "file2.md").write_text("2")
        (tmp_path / "file3.html").write_text("3")
        (tmp_path / "file4.xyz").write_text("4")  # Should be ignored

        # Create subdirectory with files
        subdir = tmp_path / "sub"
        subdir.mkdir()
        (subdir / "file5.txt").write_text("5")  # Should be ignored (non-recursive)

        files = find_files(tmp_path, recursive=False)
        assert len(files) == 3  # Only .txt, .md, .html in root
        assert all(f.suffix in ['.txt', '.md', '.html'] for f in files)
        assert all(f.parent == tmp_path for f in files)

    def test_find_files_in_directory_recursive(self, tmp_path):
        # Create files in root
        (tmp_path / "file1.txt").write_text("1")

        # Create subdirectory with files
        subdir = tmp_path / "sub"
        subdir.mkdir()
        (subdir / "file2.md").write_text("2")

        # Create nested subdirectory
        subsubdir = subdir / "subsub"
        subsubdir.mkdir()
        (subsubdir / "file3.html").write_text("3")

        files = find_files(tmp_path, recursive=True)
        assert len(files) == 3
        # Check that files from all levels are found
        assert any(f.name == "file1.txt" for f in files)
        assert any(f.name == "file2.md" for f in files)
        assert any(f.name == "file3.html" for f in files)

    def test_find_specific_extensions(self, tmp_path):
        (tmp_path / "file1.txt").write_text("1")
        (tmp_path / "file2.md").write_text("2")
        (tmp_path / "file3.html").write_text("3")

        # Find only .txt files
        files = find_files(tmp_path, extensions=['.txt'])
        assert len(files) == 1
        assert files[0].suffix == '.txt'

        # Find .txt and .md files
        files = find_files(tmp_path, extensions=['.txt', '.md'])
        assert len(files) == 2
        assert all(f.suffix in ['.txt', '.md'] for f in files)

    def test_directory_not_found(self, tmp_path):
        non_existent = tmp_path / "does_not_exist"
        with pytest.raises(FileNotFoundError):
            find_files(non_existent)
