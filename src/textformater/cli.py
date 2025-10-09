"""Command-line interface for text-formater."""

from __future__ import annotations

import sys
from pathlib import Path

import click

from . import __version__
from .config import load_config, validate_config as validate_config_file
from .polish import polish_text, polish_text_verbose
from .processors import process_file, find_files


@click.command()
@click.version_option(version=__version__, prog_name='textformat')
@click.argument('input', required=False)
@click.option(
    '--output', '-o',
    type=click.Path(path_type=Path),
    help='Output file path (for single file processing)',
)
@click.option(
    '--inplace', '-i',
    is_flag=True,
    help='Modify files in place',
)
@click.option(
    '--recursive', '-r',
    is_flag=True,
    help='Process directories recursively',
)
@click.option(
    '--dry-run', '-n',
    is_flag=True,
    help='Show changes without writing files',
)
@click.option(
    '--extensions', '-e',
    multiple=True,
    help='File extensions to process (e.g., -e .txt -e .md). Default: .txt, .md, .html',
)
@click.option(
    '--verbose', '-v',
    is_flag=True,
    help='Show summary of changes made',
)
@click.option(
    '--config', '-c',
    type=click.Path(path_type=Path, exists=True),
    help='Path to custom config file',
)
@click.option(
    '--validate-config',
    type=click.Path(path_type=Path, exists=True),
    help='Validate a configuration file and exit',
)
@click.option(
    '--show-config',
    is_flag=True,
    help='Show effective configuration and exit',
)
def main(
    input: str | None,
    output: Path | None,
    inplace: bool,
    recursive: bool,
    dry_run: bool,
    extensions: tuple[str, ...],
    verbose: bool,
    config: Path | None,
    validate_config: Path | None,
    show_config: bool,
):
    """Format text with Chinese typography rules.

    Automatically applies:
    • CJK-English spacing (中文English → 中文 English)
    • Em-dash formatting (-- → ——)
    • Ellipsis normalization (. . . → ...)
    • Quote spacing and punctuation fixes

    Supports: Plain text (.txt), Markdown (.md), HTML (.html, .htm)
    Code blocks and <pre>/<code> tags are preserved.

    INPUT can be:
    - Text string (if not a file/directory path)
    - File path (.txt, .md, .html)
    - Directory path
    - Omitted (reads from stdin)

    Examples:

      \b
      # Format text directly
      textformat "文本English混合"

      \b
      # Read from stdin
      echo "文本English混合" | textformat
      cat input.txt | textformat

      \b
      # Format a file
      textformat input.txt
      textformat input.md --output formatted.md

      \b
      # Format files in a directory
      textformat ./docs/
      textformat ./docs/ --recursive --inplace

      \b
      # Dry run (preview changes)
      textformat input.txt --dry-run
    """
    # Handle --validate-config command (validate and exit)
    if validate_config:
        result = validate_config_file(validate_config)
        click.echo(result.format_report())
        sys.exit(0 if result.is_valid else 1)

    # Load configuration
    rule_config = load_config(config_path=config)

    # Handle --show-config command (show config and exit)
    if show_config:
        _show_effective_config(rule_config, config)
        sys.exit(0)

    # If no input provided, read from stdin
    if input is None:
        if not sys.stdin.isatty():
            input_text = sys.stdin.read()
            if verbose:
                result, stats = polish_text_verbose(input_text, config=rule_config)
                click.echo(result)
                click.echo(stats.format_summary(), err=True)
            else:
                result = polish_text(input_text, config=rule_config)
                click.echo(result)
            return
        else:
            click.echo("Error: No input provided", err=True)
            click.echo("Try 'textformat --help' for usage information", err=True)
            sys.exit(1)

    # Check if input is a file or directory
    input_path = Path(input)

    if input_path.exists():
        # Input is a file or directory
        if input_path.is_file():
            process_single_file(input_path, output, inplace, dry_run, verbose, rule_config)
        elif input_path.is_dir():
            process_directory(input_path, inplace, recursive, dry_run, extensions, verbose, rule_config)
        else:
            click.echo(f"Error: {input_path} is not a file or directory", err=True)
            sys.exit(1)
    else:
        # Treat input as text string
        if verbose:
            result, stats = polish_text_verbose(input, config=rule_config)
            if output:
                if dry_run:
                    click.echo(f"Would write to: {output}")
                    click.echo(result)
                else:
                    output.write_text(result, encoding='utf-8')
                    click.echo(f"Formatted text written to: {output}")
                click.echo(stats.format_summary(), err=True)
            else:
                click.echo(result)
                click.echo(stats.format_summary(), err=True)
        else:
            result = polish_text(input, config=rule_config)
            if output:
                if dry_run:
                    click.echo(f"Would write to: {output}")
                    click.echo(result)
                else:
                    output.write_text(result, encoding='utf-8')
                    click.echo(f"Formatted text written to: {output}")
            else:
                click.echo(result)


def process_single_file(
    file_path: Path,
    output: Path | None,
    inplace: bool,
    dry_run: bool,
    verbose: bool,
    config,
):
    """Process a single file.

    Args:
        file_path: Input file path
        output: Output file path (optional)
        inplace: Modify file in place
        dry_run: Preview changes without writing
        verbose: Show statistics about changes
        config: Rule configuration
    """
    try:
        # For now, verbose stats only work with plain text files
        # For other file types, use regular processing
        if verbose and file_path.suffix.lower() == '.txt':
            content = file_path.read_text(encoding='utf-8')
            result, stats = polish_text_verbose(content, config=config)
        else:
            result = process_file(file_path)
            stats = None

        if dry_run:
            click.echo(f"=== {file_path} ===")
            click.echo(result)
            click.echo()
            if stats:
                click.echo(stats.format_summary(), err=True)
        elif inplace:
            file_path.write_text(result, encoding='utf-8')
            click.secho(f"✓ Formatted: {file_path}", fg='green')
            if stats:
                click.echo(stats.format_summary(), err=True)
        elif output:
            output.write_text(result, encoding='utf-8')
            click.secho(f"✓ Written to: {output}", fg='green')
            if stats:
                click.echo(stats.format_summary(), err=True)
        else:
            # Print to stdout
            click.echo(result)
            if stats:
                click.echo(stats.format_summary(), err=True)

    except ValueError as e:
        click.echo(f"Error processing {file_path}: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Unexpected error processing {file_path}: {e}", err=True)
        sys.exit(1)


def process_directory(
    dir_path: Path,
    inplace: bool,
    recursive: bool,
    dry_run: bool,
    extensions: tuple[str, ...],
    verbose: bool,
    config,
):
    """Process all files in a directory.

    Args:
        dir_path: Directory path
        inplace: Modify files in place
        recursive: Process subdirectories
        dry_run: Preview changes without writing
        extensions: File extensions to process
        verbose: Show statistics about changes
        config: Rule configuration
    """
    if not inplace and not dry_run:
        click.echo("Error: Directory processing requires --inplace or --dry-run", err=True)
        sys.exit(1)

    # Convert extensions tuple to list, or use defaults
    ext_list = list(extensions) if extensions else None

    try:
        files = find_files(dir_path, recursive=recursive, extensions=ext_list)
    except FileNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    if not files:
        click.echo(f"No files found in {dir_path}", err=True)
        sys.exit(0)

    click.echo(f"Found {len(files)} file(s) to process")

    success_count = 0
    error_count = 0

    for file_path in files:
        try:
            # For verbose mode with plain text files, show stats
            if verbose and file_path.suffix.lower() == '.txt':
                content = file_path.read_text(encoding='utf-8')
                result, stats = polish_text_verbose(content, config=config)
            else:
                result = process_file(file_path)
                stats = None

            if dry_run:
                click.echo(f"\n=== {file_path} ===")
                click.echo(result)
                if stats:
                    click.echo(stats.format_summary(), err=True)
            else:
                file_path.write_text(result, encoding='utf-8')
                if verbose and stats:
                    click.secho(f"✓ {file_path}", fg='green')
                    click.echo(f"  {stats.format_summary()}", err=True)
                else:
                    click.secho(f"✓ {file_path}", fg='green')
                success_count += 1

        except ValueError as e:
            click.secho(f"✗ {file_path}: {e}", fg='red', err=True)
            error_count += 1
        except Exception as e:
            click.secho(f"✗ {file_path}: Unexpected error: {e}", fg='red', err=True)
            error_count += 1

    if not dry_run:
        click.echo(f"\nProcessed {success_count} file(s), {error_count} error(s)")


def _show_effective_config(rule_config, config_path: Path | None) -> None:
    """Display the effective configuration being used.

    Args:
        rule_config: The loaded rule configuration
        config_path: Path to custom config (if provided via --config)
    """
    click.secho("Effective Configuration:", bold=True)
    click.echo()

    # Show config source
    click.echo("Config Source:")
    if config_path:
        click.echo(f"  Custom: {config_path}")
    else:
        # Check which default config is being used
        project_config = Path.cwd() / "textformat.toml"
        user_config = Path.home() / ".config" / "textformat.toml"

        if project_config.exists():
            click.echo(f"  Project: {project_config}")
        if user_config.exists():
            click.echo(f"  User: {user_config}")
        if not project_config.exists() and not user_config.exists():
            click.echo("  Defaults (no config file)")
    click.echo()

    # Show built-in rules
    click.secho("Built-in Rules:", bold=True)
    for rule_name, enabled in sorted(rule_config.rules.items()):
        status = "✓" if enabled else "✗"
        color = "green" if enabled else "red"
        click.secho(f"  {status} {rule_name}: {enabled}", fg=color)
    click.echo()

    # Show custom rules
    if rule_config.custom_rules:
        click.secho("Custom Rules:", bold=True)
        for i, rule in enumerate(rule_config.custom_rules):
            name = rule.get('name', f'rule_{i}')
            pattern = rule.get('pattern', '')
            replacement = rule.get('replacement', '')
            description = rule.get('description', '')

            click.echo(f"  [{i+1}] {name}")
            click.echo(f"      pattern: {pattern}")
            click.echo(f"      replacement: {replacement}")
            if description:
                click.echo(f"      description: {description}")
        click.echo()
    else:
        click.echo("Custom Rules: None")
        click.echo()


if __name__ == '__main__':
    main()
