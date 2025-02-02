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
    path: Optional[Path] = typer.Argument(
        None,
        help="File or directory to generate prompt from (defaults to current directory)",
        exists=True,
        file_okay=True,
        dir_okay=True,
        resolve_path=True,
    ),
    analyze_imports: bool = typer.Option(
        False,
        "--analyze-imports",
        "-a",
        help="Analyze and include local imports when processing a single file",
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
    working_path = path or Path.cwd()

    # Parse output configurations
    output_configs = [parse_output_config(out) for out in output]
    handlers = get_output_handlers(output_configs)

    if working_path.is_file():
        print("File mode: Processing single file")
        base_dir = working_path.parent
        files = [working_path]
        gitignore_spec = load_gitignore(base_dir, DEFAULT_IGNORE_PATTERNS.copy())
    else:
        print("Directory mode: Processing entire directory")
        base_dir = working_path
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
        gitignore_spec = load_gitignore(base_dir, patterns_to_use)

        # Get all files recursively, respecting gitignore
        files = get_files_recursively(base_dir, gitignore_spec)

    # Generate markdown output
    markdown_content = generate_markdown_output(
        files, 
        base_dir, 
        gitignore_spec,
        is_file_mode=working_path.is_file()
    )

    # Send to all configured outputs
    for handler in handlers:
        handler(markdown_content)
