"""Command-line interface for cjk-text-formatter."""

from __future__ import annotations

import sys
from pathlib import Path

import click

from . import __version__
from .config import load_config, validate_config as validate_config_file, DEFAULT_RULES, RULE_DESCRIPTIONS
from .polish import polish_text, polish_text_verbose
from .processors import process_file, find_files

# Import for accessing package data files
try:
    from importlib.resources import files
except ImportError:
    # Python 3.8 fallback
    from importlib_resources import files


@click.command()
@click.version_option(version=__version__, prog_name='ctf')
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
@click.option(
    '--init-config',
    is_flag=True,
    help='Create example config file and exit',
)
@click.option(
    '--global',
    'config_global',
    is_flag=True,
    help='Use with --init-config to create global config (~/.config/)',
)
@click.option(
    '--force',
    is_flag=True,
    help='Use with --init-config to overwrite existing config',
)
@click.option(
    '--list-rules',
    is_flag=True,
    help='List all available formatting rules and exit',
)
@click.option(
    '--show-config-example',
    is_flag=True,
    help='Print example config to stdout and exit',
)
@click.option(
    '--where',
    'where_config',
    is_flag=True,
    help='Show config file locations and exit',
)
@click.option(
    '--disable',
    'disable_rules',
    multiple=True,
    help='Disable specific rule(s) (can be used multiple times)',
)
@click.option(
    '--enable',
    'enable_rules',
    multiple=True,
    help='Enable specific rule(s) (can be used multiple times)',
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
    init_config: bool,
    config_global: bool,
    force: bool,
    list_rules: bool,
    show_config_example: bool,
    where_config: bool,
    disable_rules: tuple[str, ...],
    enable_rules: tuple[str, ...],
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
      ctf "文本English混合"

      \b
      # Read from stdin
      echo "文本English混合" | ctf
      cat input.txt | ctf

      \b
      # Format a file
      ctf input.txt
      ctf input.md --output formatted.md

      \b
      # Format files in a directory
      ctf ./docs/
      ctf ./docs/ --recursive --inplace

      \b
      # Dry run (preview changes)
      ctf input.txt --dry-run
    """
    # Handle --validate-config command (validate and exit)
    if validate_config:
        result = validate_config_file(validate_config)
        click.echo(result.format_report())
        sys.exit(0 if result.is_valid else 1)

    # Handle --init-config command (create config file and exit)
    if init_config:
        _init_config_file(config_global, force)
        sys.exit(0)

    # Handle --list-rules command (list rules and exit)
    if list_rules:
        _list_available_rules()
        sys.exit(0)

    # Handle --show-config-example command (print example and exit)
    if show_config_example:
        _show_config_example()
        sys.exit(0)

    # Handle --where command (show config locations and exit)
    if where_config:
        _show_config_locations(config)
        sys.exit(0)

    # Load configuration
    rule_config = load_config(config_path=config)

    # Apply CLI rule overrides (--disable/--enable)
    if disable_rules or enable_rules:
        _apply_rule_overrides(rule_config, disable_rules, enable_rules)

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
            click.echo("Try 'ctf --help' for usage information", err=True)
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
            result = process_file(file_path, config=config)
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
                result = process_file(file_path, config=config)
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
        project_config = Path.cwd() / "cjk-text-formatter.toml"
        user_config = Path.home() / ".config" / "cjk-text-formatter.toml"

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


def _init_config_file(config_global: bool, force: bool) -> None:
    """Create a config file from the example template.

    Args:
        config_global: If True, create global config in ~/.config/
        force: If True, overwrite existing config file
    """
    # Determine target path
    if config_global:
        target = Path.home() / ".config" / "cjk-text-formatter.toml"
        location_name = "global config"
    else:
        target = Path.cwd() / "cjk-text-formatter.toml"
        location_name = "project config"

    # Check if file exists
    if target.exists() and not force:
        click.secho(f"Error: {location_name} already exists at {target}", fg='red', err=True)
        click.echo("Use --force to overwrite", err=True)
        sys.exit(1)

    # Get example config content from package data
    try:
        package_files = files('cjk_text_formatter')
        example_content = (package_files / 'cjk-text-formatter.toml.example').read_text(encoding='utf-8')
    except Exception as e:
        click.secho(f"Error reading example config from package: {e}", fg='red', err=True)
        sys.exit(1)

    # Create parent directory if it doesn't exist (for global config)
    target.parent.mkdir(parents=True, exist_ok=True)

    # Write example content to target
    try:
        target.write_text(example_content, encoding='utf-8')
        click.secho(f"✓ Created {location_name}: {target}", fg='green')
        click.echo()
        click.echo("Next steps:")
        click.echo(f"  1. Edit the config: {target}")
        click.echo("  2. Validate it: ctf --validate-config " + str(target))
        click.echo("  3. Test it: ctf --show-config")
    except Exception as e:
        click.secho(f"Error creating config file: {e}", fg='red', err=True)
        sys.exit(1)


def _list_available_rules() -> None:
    """List all available formatting rules with descriptions."""
    click.secho("Available Formatting Rules:", bold=True)
    click.echo()

    # Group rules by category
    categories = {
        'Universal': ['ellipsis_normalization'],
        'Normalization': [
            'fullwidth_alphanumeric',
            'fullwidth_punctuation',
            'fullwidth_parentheses',
            'fullwidth_brackets',
        ],
        'Em-Dash': ['dash_conversion', 'emdash_spacing'],
        'Quotes': ['quote_spacing', 'single_quote_spacing'],
        'Spacing': ['cjk_english_spacing', 'currency_spacing', 'slash_spacing', 'space_collapsing'],
        'Cleanup': ['consecutive_punctuation_limit'],
    }

    for category, rule_names in categories.items():
        click.secho(f"{category}:", bold=True, fg='cyan')
        for rule_name in rule_names:
            if rule_name in DEFAULT_RULES:
                default_value = DEFAULT_RULES[rule_name]
                description = RULE_DESCRIPTIONS.get(rule_name, 'No description available')

                # Format status
                if isinstance(default_value, bool):
                    status = "✓ ON " if default_value else "✗ OFF"
                    color = "green" if default_value else "red"
                else:
                    status = f"  {default_value}"
                    color = "yellow"

                click.echo(f"  {click.style(status, fg=color)} {click.style(rule_name, bold=True)}")
                click.echo(f"      {description}")
        click.echo()

    click.echo("Usage:")
    click.echo("  • Enable/disable in config file: [rules] section")
    click.echo("  • Temporarily disable: ctf --disable rule_name")
    click.echo("  • Temporarily enable: ctf --enable rule_name")
    click.echo("  • View current config: ctf --show-config")


def _show_config_example() -> None:
    """Print the example config file to stdout."""
    # Get example config content from package data
    try:
        package_files = files('cjk_text_formatter')
        content = (package_files / 'cjk-text-formatter.toml.example').read_text(encoding='utf-8')
        click.echo(content, nl=False)
    except Exception as e:
        click.secho(f"Error reading example config from package: {e}", fg='red', err=True)
        sys.exit(1)


def _show_config_locations(config_path: Path | None) -> None:
    """Show config file search paths and which ones exist.

    Args:
        config_path: Custom config path (if provided via --config)
    """
    click.secho("Config File Locations (priority order):", bold=True)
    click.echo()

    # Check each location
    locations = []

    # 1. Custom path (--config)
    if config_path:
        exists = config_path.exists()
        status = click.style("[EXISTS] ✓", fg='green') if exists else click.style("[NOT FOUND]", fg='red')
        locations.append((1, f"Custom (--config): {config_path}", status, exists))
    else:
        locations.append((1, "Custom (--config): Not specified", click.style("[NOT USED]", fg='yellow'), False))

    # 2. Project config
    project_config = Path.cwd() / "cjk-text-formatter.toml"
    exists = project_config.exists()
    status = click.style("[EXISTS] ✓", fg='green') if exists else click.style("[NOT FOUND]", fg='yellow')
    locations.append((2, f"Project: {project_config}", status, exists))

    # 3. User config
    user_config = Path.home() / ".config" / "cjk-text-formatter.toml"
    exists = user_config.exists()
    status = click.style("[EXISTS] ✓", fg='green') if exists else click.style("[NOT FOUND]", fg='yellow')
    locations.append((3, f"User: {user_config}", status, exists))

    # 4. Defaults
    locations.append((4, "Defaults: Built-in rules", click.style("[ALWAYS AVAILABLE]", fg='green'), True))

    # Print locations
    for priority, location, status, _ in locations:
        click.echo(f"  {priority}. {location}")
        click.echo(f"     {status}")
        click.echo()

    # Determine which config is active
    active_config = None
    if config_path and config_path.exists():
        active_config = f"Custom: {config_path}"
    elif project_config.exists():
        active_config = f"Project: {project_config}"
    elif user_config.exists():
        active_config = f"User: {user_config}"
    else:
        active_config = "Defaults (no config file)"

    click.secho("Active Configuration:", bold=True)
    click.echo(f"  {active_config}")
    click.echo()
    click.echo("Tip: Use 'ctf --show-config' to see effective settings")


def _apply_rule_overrides(
    rule_config,
    disable_rules: tuple[str, ...],
    enable_rules: tuple[str, ...],
) -> None:
    """Apply CLI rule overrides to the loaded configuration.

    Args:
        rule_config: Loaded RuleConfig instance
        disable_rules: Tuple of rule names to disable
        enable_rules: Tuple of rule names to enable
    """
    # Validate rule names
    all_rules = set(DEFAULT_RULES.keys())

    for rule in disable_rules:
        if rule not in all_rules:
            click.secho(f"Error: Unknown rule '{rule}'", fg='red', err=True)
            click.echo(f"Available rules: {', '.join(sorted(all_rules))}", err=True)
            sys.exit(1)
        rule_config.rules[rule] = False

    for rule in enable_rules:
        if rule not in all_rules:
            click.secho(f"Error: Unknown rule '{rule}'", fg='red', err=True)
            click.echo(f"Available rules: {', '.join(sorted(all_rules))}", err=True)
            sys.exit(1)
        rule_config.rules[rule] = True


if __name__ == '__main__':
    main()
