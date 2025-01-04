from pathlib import Path
from typing import Optional

from pathspec import PathSpec
from pathspec.patterns import GitWildMatchPattern
from rich import print


def load_gitignore(directory: Path, additional_patterns: list[str]) -> PathSpec:
    """
    Load and parse .gitignore file if it exists and combine with additional patterns.

    Args:
        directory: The directory containing the potential .gitignore file
        additional_patterns: List of additional patterns to include in the PathSpec

    Returns:
        PathSpec object combining .gitignore patterns (if they exist) and additional patterns
    """
    patterns = additional_patterns.copy()  # Start with our additional patterns

    # Try to read .gitignore patterns if the file exists
    gitignore_path = directory / ".gitignore"
    if gitignore_path.is_file():
        try:
            with gitignore_path.open("r", encoding="utf-8") as f:
                # Filter out empty lines and comments
                gitignore_patterns = [
                    line.strip()
                    for line in f
                    if line.strip() and not line.startswith("#")
                ]
                patterns.extend(gitignore_patterns)
        except Exception as e:
            print(f"[yellow]Warning: Error reading .gitignore file: {e}[/yellow]")

    # Create PathSpec from all patterns
    return PathSpec.from_lines(GitWildMatchPattern, patterns)


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
