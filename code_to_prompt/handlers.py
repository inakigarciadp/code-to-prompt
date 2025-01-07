from pathlib import Path

import typer
from rich import print
from rich.markdown import Markdown

from .config import OutputConfig, OutputHandler


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

    return handlers
