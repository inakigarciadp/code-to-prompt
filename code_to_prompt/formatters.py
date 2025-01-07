from pathlib import Path
from typing import List, Optional, Tuple

from pathspec import PathSpec

from code_to_prompt.constants import EXTENSIONS_MAP

from .filesystem import read_file_content, should_ignore


def get_path_sort_key(path: Path, base_dir: Path) -> List[Tuple[bool, str]]:
    """
    Generate a sort key for a path that will order directories and files consistently.
    
    Args:
        path: The path to generate a sort key for
        base_dir: The base directory for creating relative paths
    
    Returns:
        List of tuples containing (is_file, lowercase_name) for each path component
        
    Example:
        For path 'src/module/file.py' relative to base_dir, returns:
        [(False, 'src'), (False, 'module'), (True, 'file.py')]
    """
    # Get the relative path from base_dir to our target path
    relative_path = path.relative_to(base_dir)
    
    # Initialize our sort key list
    sort_key = []
    
    # Add each parent directory to the sort key
    # We iterate through parts from left to right (root to leaf)
    current_path = base_dir
    for part in relative_path.parts[:-1]:  # Exclude the last part (file/dir name)
        current_path = current_path / part
        sort_key.append((current_path.is_file(), part.lower()))
    
    # Add the final component (file or directory name)
    sort_key.append((path.is_file(), relative_path.name.lower()))
    
    return sort_key


def sort_files(files: List[Path], base_dir: Path) -> List[Path]:
    """
    Sort files in a consistent order matching directory tree view.
    
    Args:
        files: List of file paths to sort
        base_dir: Base directory for relative path calculation
    
    Returns:
        Sorted list of paths with directories first, then files, all alphabetically
    """
    return sorted(files, key=lambda p: get_path_sort_key(p, base_dir))


def get_file_language(file_path: Path) -> str:
    """
    Determine the programming language based on file extension for syntax highlighting.

    Args:
        file_path: Path object for the file

    Returns:
        String representing the language for markdown code block
    """

    return EXTENSIONS_MAP.get(file_path.suffix.lower(), "")


def generate_directory_tree(
    directory: Path, gitignore_spec: Optional[PathSpec] = None, prefix: str = ""
) -> str:
    """
    Generate a tree view of the directory structure, respecting gitignore rules.

    Args:
        directory: The directory to generate tree for
        gitignore_spec: Optional PathSpec object with gitignore patterns
        prefix: Current line prefix for recursion (default: "")

    Returns:
        String containing the tree view of the directory
    """
    tree = []
    contents = sorted(directory.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))

    for i, path in enumerate(contents):
        is_last = i == len(contents) - 1
        current_prefix = "└── " if is_last else "├── "
        next_prefix = "    " if is_last else "│   "

        # Skip if path should be ignored
        if should_ignore(path, directory, gitignore_spec):
            continue

        # Add current item to tree
        tree.append(f"{prefix}{current_prefix}{path.name}")

        # Recursively process directories
        if path.is_dir():
            subtree = generate_directory_tree(
                path, gitignore_spec, prefix + next_prefix
            )
            if subtree:  # Only add non-empty subtrees
                tree.append(subtree)

    return "\n".join(tree)


def generate_markdown_output(
    files: list[Path], 
    base_dir: Path, 
    gitignore_spec: Optional[PathSpec],
    is_file_mode: bool = False
) -> str:
    """
    Generate markdown formatted output for the list of files.

    Args:
        files: List of files to include in the output
        base_dir: The base directory for creating relative paths
        gitignore_spec: Optional PathSpec object with gitignore patterns
        is_file_mode: If True, skip directory tree and use file-specific header

    Returns:
        Markdown formatted string
    """
    if is_file_mode:
        markdown = "# File Summary\n\n"
    else:
        markdown = "# Codebase Contents\n\n"
        # Add directory tree
        markdown += "## Directory Structure\n\n"
        markdown += "```\n"
        markdown += base_dir.name + "\n"  # Root directory name
        markdown += generate_directory_tree(base_dir, gitignore_spec)
        markdown += "\n```\n\n"

    # Add file contents
    markdown += "## File Contents\n\n"
    # Sort files to match tree view ordering
    sorted_files = sort_files(files, base_dir)

    for file in sorted_files:
        try:
            # Convert relative path to string with forward slashes
            relative_path = str(file.relative_to(base_dir)).replace("\\", "/")
            markdown += f"### File: `{relative_path}`\n\n"

            # Read and include file contents
            content = read_file_content(file)
            if content is not None:
                if file.suffix.lower() == ".md":
                    # For markdown files, include content directly without code blocks
                    markdown += f"{content}\n\n"
                else:
                    # For all other files, use code blocks with language highlighting
                    language = get_file_language(file)
                    markdown += f"```{language}\n{content}\n```\n\n"
            else:
                markdown += "*[File content could not be read]*\n\n"

        except ValueError:
            markdown += f"### File: `{file}`\n\n"
            markdown += "*[File path error]*\n\n"

    return markdown
