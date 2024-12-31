#!/usr/bin/env python3
"""
code-to-prompt: A CLI tool to convert codebases into LLM prompts.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

import typer
from pathspec import PathSpec
from pathspec.patterns import GitWildMatchPattern
from rich import print
from rich.markdown import Markdown

# Type aliases
OutputHandler = Callable[[str], None]
OutputHandlers = dict[str, OutputHandler]


@dataclass
class OutputConfig:
    """Configuration for an output handler."""

    type: str
    path: Optional[str] = None


app = typer.Typer(
    name="code-to-prompt",
    help="Convert codebases into LLM prompts",
    add_completion=False,
)


def parse_output_config(output_str: str) -> OutputConfig:
    """
    Parse output configuration string.

    Args:
        output_str: String in format "type" or "type=path"

    Returns:
        OutputConfig object containing type and optional path

    Examples:
        >>> parse_output_config("console")
        OutputConfig(type="console", path=None)
        >>> parse_output_config("file=output.md")
        OutputConfig(type="file", path="output.md")
    """
    if "=" in output_str:
        output_type, path = output_str.split("=", 1)
        return OutputConfig(type=output_type.strip(), path=path.strip())
    return OutputConfig(type=output_str.strip())


def console_output(content: str) -> None:
    """
    Output content to console using rich formatting.

    Args:
        content: Markdown content to output
    """
    print(Markdown(content))


def file_output(content: str, path: str) -> None:
    """
    Output content to a file.

    Args:
        content: Content to write to file
        path: Path to output file
    """
    output_path = Path(path)
    try:
        output_path.write_text(content, encoding="utf-8")
        print(f"[green]Output written to {output_path}[/green]")
    except Exception as e:
        print(f"[red]Error writing to file {output_path}: {e}[/red]")


def get_output_handlers(configs: list[OutputConfig]) -> list[OutputHandler]:
    """
    Create list of output handlers from configs.

    Args:
        configs: List of output configurations

    Returns:
        List of configured output handler functions

    Raises:
        typer.BadParameter: If an invalid output type is specified
    """
    handlers: list[OutputHandler] = []

    for config in configs:
        if config.type == "console":
            handlers.append(lambda content: console_output(content))
        elif config.type == "file":
            if not config.path:
                raise typer.BadParameter(
                    "File output requires a path (e.g., file=output.md)"
                )
            # Create a closure to capture the path
            path = config.path
            handlers.append(lambda content: file_output(content, path))
        else:
            raise typer.BadParameter(f"Unknown output type: {config.type}")

    return handlers or [
        console_output
    ]  # Default to console output if no handlers specified


def load_gitignore(directory: Path) -> Optional[PathSpec]:
    """
    Load and parse .gitignore file if it exists.

    Args:
        directory: The directory containing the potential .gitignore file

    Returns:
        PathSpec object if .gitignore exists, None otherwise
    """
    gitignore_path = directory / ".gitignore"
    if not gitignore_path.is_file():
        return None

    try:
        with gitignore_path.open("r", encoding="utf-8") as f:
            # Filter out empty lines and comments
            patterns = [
                line.strip() for line in f if line.strip() and not line.startswith("#")
            ]
            return PathSpec.from_lines(GitWildMatchPattern, patterns)
    except Exception as e:
        print(f"[yellow]Warning: Error reading .gitignore file: {e}[/yellow]")
        return None


def should_ignore(
    path: Path, base_dir: Path, gitignore_spec: Optional[PathSpec]
) -> bool:
    """
    Check if a path should be ignored based on gitignore rules and default Git behavior.

    Args:
        path: The path to check
        base_dir: The base directory of the project
        gitignore_spec: The parsed gitignore patterns

    Returns:
        True if the path should be ignored, False otherwise
    """
    # Always ignore .git directory
    try:
        relative_parts = path.relative_to(base_dir).parts
        if ".git" in relative_parts:
            return True
    except ValueError:
        pass

    # Check gitignore patterns if they exist
    if gitignore_spec is None:
        return False

    # Convert to relative path for gitignore matching
    try:
        relative_path = str(path.relative_to(base_dir))
        # Use forward slashes for consistency (important for Windows)
        relative_path = relative_path.replace("\\", "/")
        return gitignore_spec.match_file(relative_path)
    except ValueError:
        return False


def get_files_recursively(
    directory: Path, gitignore_spec: Optional[PathSpec] = None
) -> list[Path]:
    """
    Recursively get all files in a directory, respecting gitignore rules.

    Args:
        directory: The directory to search in
        gitignore_spec: Optional PathSpec object with gitignore patterns

    Returns:
        List of Path objects for all non-ignored files
    """
    files = []

    for item in directory.rglob("*"):
        # Skip if it's not a file
        if not item.is_file():
            continue

        # Skip if it matches gitignore patterns
        if should_ignore(item, directory, gitignore_spec):
            continue

        files.append(item)

    return files


def get_file_language(file_path: Path) -> str:
    """
    Determine the programming language based on file extension for syntax highlighting.

    Args:
        file_path: Path object for the file

    Returns:
        String representing the language for markdown code block
    """
    extension_map = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".jsx": "jsx",
        ".tsx": "tsx",
        ".html": "html",
        ".css": "css",
        ".scss": "scss",
        ".sql": "sql",
        ".sh": "bash",
        ".bash": "bash",
        ".zsh": "bash",
        ".go": "go",
        ".rs": "rust",
        ".java": "java",
        ".cpp": "cpp",
        ".c": "c",
        ".rb": "ruby",
        ".php": "php",
        ".md": "markdown",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".json": "json",
        ".xml": "xml",
        ".toml": "toml",
    }

    return extension_map.get(file_path.suffix.lower(), "")


def read_file_content(file_path: Path) -> Optional[str]:
    """
    Safely read the content of a file with proper encoding handling.

    Args:
        file_path: Path object for the file to read

    Returns:
        File content as string if successful, None if reading fails
    """
    try:
        # Try UTF-8 first
        return file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        try:
            # Fallback to system default encoding
            return file_path.read_text()
        except Exception as e:
            print(f"[yellow]Warning: Could not read file {file_path}: {e}[/yellow]")
            return None


def generate_markdown_output(files: list[Path], base_dir: Path) -> str:
    """
    Generate markdown formatted output for the list of files, including their contents.

    Args:
        files: List of files to include in the output
        base_dir: The base directory for creating relative paths

    Returns:
        Markdown formatted string
    """
    markdown = "# Codebase Contents\n\n"

    for file in sorted(files):
        try:
            relative_path = file.relative_to(base_dir)
            markdown += f"## File: `{relative_path}`\n\n"

            # Read and include file contents
            content = read_file_content(file)
            if content is not None:
                language = get_file_language(file)
                markdown += f"```{language}\n{content}\n```\n\n"
            else:
                markdown += "*[File content could not be read]*\n\n"

        except ValueError:
            markdown += f"## File: `{file}`\n\n"
            markdown += "*[File path error]*\n\n"

    return markdown


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
        None,
        "--output",
        "-o",
        help="Output destinations (e.g., console, file=output.md). Multiple allowed.",
    ),
) -> None:
    """
    Generate an LLM prompt from a codebase.
    """
    # Use current directory if none specified
    working_dir = directory or Path.cwd()

    # Parse output configurations
    output_configs = [parse_output_config(out) for out in (output or ["console"])]
    handlers = get_output_handlers(output_configs)

    # Load gitignore if it exists
    gitignore_spec = load_gitignore(working_dir)

    # Get all files recursively, respecting gitignore
    files = get_files_recursively(working_dir, gitignore_spec)

    # Generate markdown output
    markdown_content = generate_markdown_output(files, working_dir)

    # Send to all configured outputs
    for handler in handlers:
        handler(markdown_content)


if __name__ == "__main__":
    app()
