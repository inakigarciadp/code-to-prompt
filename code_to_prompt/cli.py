from pathlib import Path
from typing import Optional

import typer

from .config import parse_output_config
from .constants import DEFAULT_IGNORE_PATTERNS
from .filesystem import get_files_recursively, load_gitignore
from .formatters import generate_markdown_output
from .handlers import get_output_handlers

app = typer.Typer(
    name="code-to-prompt",
    help="Convert codebases into LLM prompts",
    add_completion=False,
)


@app.command()
def main(
    directory: Optional[Path] = typer.Argument(
        None,
        help="Directory to generate prompt from (defaults to current directory)",
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
    output: Optional[list[str]] = typer.Option(
        ["console"],
        "--output",
        "-o",
        help="Output destinations (e.g., console, file=output.md). Multiple allowed.",
    ),
    ignore_patterns: Optional[list[str]] = typer.Option(
        None,
        "--ignore",
        "-i",
        help="Patterns to ignore (e.g., '*.log', 'temp/'). Replaces default patterns. Use empty list to disable all patterns.",
    ),
    extra_ignore: Optional[list[str]] = typer.Option(
        None,
        "--extra-ignore",
        "-e",
        help="Additional patterns to ignore. These are added to default patterns.",
    ),
) -> None:
    """
    Generate an LLM prompt from a codebase.
    """
    # Use current directory if none specified
    working_dir = directory or Path.cwd()

    # Parse output configurations
    output_configs = [parse_output_config(out) for out in output]
    handlers = get_output_handlers(output_configs)

    # Handle ignore patterns
    if ignore_patterns is not None:
        # Use provided patterns (empty list disables all ignoring)
        patterns_to_use = ignore_patterns
    else:
        # Start with default patterns
        patterns_to_use = DEFAULT_IGNORE_PATTERNS.copy()
        # Add extra patterns if provided
        if extra_ignore:
            patterns_to_use.extend(extra_ignore)

    # Load gitignore if it exists and combine with our patterns
    gitignore_spec = load_gitignore(working_dir, patterns_to_use)

    # Get all files recursively, respecting gitignore
    files = get_files_recursively(working_dir, gitignore_spec)

    # Generate markdown output
    markdown_content = generate_markdown_output(files, working_dir, gitignore_spec)

    # Send to all configured outputs
    for handler in handlers:
        handler(markdown_content)
