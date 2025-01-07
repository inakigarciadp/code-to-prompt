from pathlib import Path

import pytest
from pathspec import PathSpec
from pathspec.patterns import GitWildMatchPattern

from code_to_prompt.formatters import (
    generate_directory_tree,
    generate_markdown_output,
    get_file_language,
    get_path_sort_key,
    sort_files,
)


def test_get_path_sort_key(tmp_path):
    """Test that get_path_sort_key generates correct sort keys"""
    # Create test path
    file_path = tmp_path / "src" / "module" / "file.py"
    file_path.parent.mkdir(parents=True)
    file_path.touch()

    sort_key = get_path_sort_key(file_path, tmp_path)

    assert len(sort_key) == 3
    assert sort_key[0] == (False, "src")
    assert sort_key[1] == (False, "module")
    assert sort_key[2] == (True, "file.py")


def test_sort_files(tmp_path):
    """Test that files are sorted correctly"""
    # Create test files
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "module").mkdir()
    file1 = tmp_path / "src" / "module" / "file.py"
    file2 = tmp_path / "README.md"
    file3 = tmp_path / "src" / "test.py"

    for f in [file1, file2, file3]:
        f.touch()

    files = [file1, file2, file3]
    sorted_files = sort_files(files, tmp_path)

    # Convert to relative paths for easier assertion
    sorted_paths = [str(f.relative_to(tmp_path)) for f in sorted_files]

    assert sorted_paths == [
        "src/module/file.py",
        "src/test.py",
        "README.md",
    ]


# Fixtures for common test setup
@pytest.fixture
def temp_dir(tmp_path):
    """Create a temporary directory with some test files."""
    # Create test directory structure
    python_file = tmp_path / "test.py"
    python_file.write_text("def test(): pass")

    markdown_file = tmp_path / "readme.md"
    markdown_file.write_text("# Test\nThis is a test")

    subdir = tmp_path / "subdir"
    subdir.mkdir()
    subfile = subdir / "test.js"
    subfile.write_text("console.log('test');")

    return tmp_path


@pytest.fixture
def gitignore_spec():
    """Create a simple gitignore spec for testing."""
    patterns = ["*.log", "temp/"]
    return PathSpec.from_lines(GitWildMatchPattern, patterns)


def test_get_file_language():
    """Test language detection for different file extensions."""
    test_cases = [
        (Path("test.py"), "python"),
        (Path("test.js"), "javascript"),
        (Path("test.md"), "markdown"),
        (Path("test.unknown"), ""),  # Unknown extension should return empty string
    ]

    for file_path, expected in test_cases:
        assert get_file_language(file_path) == expected


def test_generate_directory_tree(temp_dir, gitignore_spec):
    """Test directory tree generation with a simple directory structure."""
    tree = generate_directory_tree(temp_dir, gitignore_spec)

    # Basic structure checks
    assert "test.py" in tree
    assert "readme.md" in tree
    assert "subdir" in tree
    assert "test.js" in tree

    # Check formatting
    assert "├── " in tree or "└── " in tree  # Should use proper tree characters
    assert "\n" in tree  # Should be multi-line


def test_generate_markdown_output_directory_mode(temp_dir, gitignore_spec):
    """Test markdown output generation in directory mode."""
    files = [
        temp_dir / "test.py",
        temp_dir / "readme.md",
        temp_dir / "subdir" / "test.js",
    ]

    output = generate_markdown_output(
        files, temp_dir, gitignore_spec, is_file_mode=False
    )

    # Check basic structure
    assert "# Codebase Contents" in output
    assert "## Directory Structure" in output
    assert "## File Contents" in output


def test_generate_markdown_output_file_mode(temp_dir, gitignore_spec):
    """Test markdown output generation in file mode."""
    files = [temp_dir / "test.py"]

    output = generate_markdown_output(
        files, temp_dir, gitignore_spec, is_file_mode=True
    )

    # Check file mode specific structure
    assert "# File Summary" in output
    assert "## Directory Structure" not in output
    assert "## File Contents" in output

    # Check file content inclusion
    assert "### File: `test.py`" in output
    assert "```python" in output
    assert "def test(): pass" in output
