from dataclasses import dataclass
from typing import Callable, Optional

# Type aliases
OutputHandler = Callable[[str], None]


@dataclass
class OutputConfig:
    """Configuration for an output handler."""

    type: str
    path: Optional[str] = None


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
