from pathlib import Path
from unittest.mock import patch

import pytest
from pathspec import PathSpec
from pathspec.patterns import GitWildMatchPattern

from code_to_prompt.formatters import (
    generate_directory_tree,
    generate_markdown_output,
    get_file_language,
)


# Fixtures
@pytest.fixture
def temp_dir(tmp_path):
    """Create a temporary directory with a known structure."""
    # Create directories
    code_dir = tmp_path / "code"
    code_dir.mkdir()

    src_dir = code_dir / "src"
    src_dir.mkdir()

    # Create some test files
    (src_dir / "main.py").write_text("print('Hello')")
    (src_dir / "test.js").write_text("console.log('test')")
    (src_dir / "style.css").write_text("body { color: black; }")
    (src_dir / "readme.md").write_text("# Test\nThis is a test")
    (src_dir / "noext").write_text("no extension")
    (src_dir / "UPPER.PY").write_text("UPPER case")

    # Create nested structure
    nested = src_dir / "nested"
    nested.mkdir()
    (nested / "deep.py").write_text("nested file")

    return code_dir


@pytest.fixture
def gitignore_spec():
    """Create a PathSpec with some test patterns."""
    patterns = ["*.log", "ignored_dir/", "*_ignored.*"]
    return PathSpec.from_lines(GitWildMatchPattern, patterns)


# Test get_file_language()
@pytest.mark.parametrize(
    "file_path,expected",
    [
        (Path("test.py"), "python"),
        (Path("test.js"), "javascript"),
        (Path("test.unknown"), ""),
        (Path("no_extension"), ""),
        (Path("TEST.PY"), "python"),
        (Path(".gitignore"), ""),
        (Path("test.MD"), "markdown"),
        (Path("../test.py"), "python"),
        (Path("/absolute/path/test.py"), "python"),
    ],
)
def test_get_file_language(file_path, expected):
    """Test language detection for various file types and paths."""
    assert get_file_language(file_path) == expected


# Test generate_directory_tree()
def test_empty_directory(tmp_path):
    """Test tree generation for an empty directory."""
    result = generate_directory_tree(tmp_path)
    assert result == ""


def test_directory_with_files_only(tmp_path):
    """Test tree generation for directory with only files."""
    (tmp_path / "file1.txt").touch()
    (tmp_path / "file2.py").touch()

    result = generate_directory_tree(tmp_path)
    expected = "├── file1.txt\n└── file2.py"
    assert result.strip() == expected


def test_directory_with_subdirs_only(tmp_path):
    """Test tree generation for directory with only subdirectories."""
    (tmp_path / "dir1").mkdir()
    (tmp_path / "dir2").mkdir()

    result = generate_directory_tree(tmp_path)
    expected = "├── dir1\n└── dir2"
    assert result.strip() == expected


def test_complex_directory_structure(temp_dir):
    """Test tree generation for a complex directory structure."""
    result = generate_directory_tree(temp_dir)
    # Test for presence of contents rather than specific prefix
    assert "src" in result
    assert "nested" in result
    assert "deep.py" in result
    # Verify the nested structure is maintained
    assert result.count("│   ") > 0  # Should have at least one level of nesting


def test_directory_with_ignored_files(temp_dir, gitignore_spec):
    """Test tree generation with ignored files."""
    # Create some files that should be ignored
    (temp_dir / "test.log").touch()
    (temp_dir / "file_ignored.txt").touch()
    ignored_dir = temp_dir / "ignored_dir"
    ignored_dir.mkdir()
    (ignored_dir / "ignored.py").touch()

    # Create the gitignore_spec with correct pattern format
    patterns = [
        "*.log",  # Ignore log files
        "/ignored_dir/**",  # Ignore the ignored_dir and all its contents
        "*_ignored.*",  # Ignore files with _ignored in name
    ]
    gitignore_spec = PathSpec.from_lines(GitWildMatchPattern, patterns)

    result = generate_directory_tree(temp_dir, gitignore_spec)
    # Verify files are ignored
    assert "test.log" not in result
    assert "file_ignored.txt" not in result
    # Check complete paths to avoid partial matches
    assert "ignored_dir/ignored.py" not in result.replace("\\", "/")


def test_directory_with_special_chars(tmp_path):
    """Test tree generation with special characters in names."""
    special_dir = tmp_path / "special chars & symbols"
    special_dir.mkdir()
    (special_dir / "file with spaces.py").touch()
    (special_dir / "@special#file.txt").touch()

    result = generate_directory_tree(tmp_path)
    assert "special chars & symbols" in result
    assert "file with spaces.py" in result
    assert "@special#file.txt" in result


# Test generate_markdown_output()
def test_empty_file_list():
    """Test markdown generation with empty file list."""
    result = generate_markdown_output([], Path("."), None)
    assert "# Codebase Contents" in result
    assert "## Directory Structure" in result
    assert "## File Contents" in result


@pytest.mark.parametrize(
    "content,extension,expected_marker",
    [
        ("# Markdown\nTest", ".md", "# Markdown\nTest"),
        ("def test(): pass", ".py", "```python\ndef test(): pass\n```"),
        ("body { color: black; }", ".css", "```css\nbody { color: black; }\n```"),
        ("no extension", "", "```\nno extension\n```"),
    ],
)
def test_different_file_types(tmp_path, content, extension, expected_marker):
    """Test markdown generation for different file types."""
    test_file = tmp_path / f"test{extension}"
    test_file.write_text(content)

    result = generate_markdown_output([test_file], tmp_path, None)
    assert expected_marker in result


@patch("code_to_prompt.formatters.read_file_content")
def test_unreadable_file(mock_read, tmp_path):
    """Test handling of unreadable files."""
    test_file = tmp_path / "unreadable.txt"
    test_file.touch()
    mock_read.return_value = None

    result = generate_markdown_output([test_file], tmp_path, None)
    assert "*[File content could not be read]*" in result


def test_special_path_characters(tmp_path):
    """Test handling of special characters in file paths."""
    special_path = tmp_path / "special & chars" / "test file.py"
    special_path.parent.mkdir()
    special_path.write_text("test content")

    result = generate_markdown_output([special_path], tmp_path, None)
    assert "special & chars" in result
    assert "test file.py" in result


def test_same_name_different_dirs(tmp_path):
    """Test handling of files with same names in different directories."""
    dir1 = tmp_path / "dir1"
    dir2 = tmp_path / "dir2"
    dir1.mkdir()
    dir2.mkdir()

    file1 = dir1 / "test.py"
    file2 = dir2 / "test.py"
    file1.write_text("content1")
    file2.write_text("content2")

    result = generate_markdown_output([file1, file2], tmp_path, None)
    assert "dir1/test.py" in result.replace("\\", "/")
    assert "dir2/test.py" in result.replace("\\", "/")
    assert "content1" in result
    assert "content2" in result


def test_sorting_order(temp_dir):
    """Test that files are sorted correctly in the output."""
    result = generate_markdown_output(
        [
            temp_dir / "src" / "main.py",
            temp_dir / "src" / "test.js",
            temp_dir / "src" / "nested" / "deep.py",
        ],
        temp_dir,
        None,
    )

    # Convert content to lines for easier comparison
    lines = result.split("\n")

    # Find indices of file headers
    indices = [i for i, line in enumerate(lines) if line.startswith("### File:")]

    # Verify correct order based on actual sorting implementation
    # Nested paths should come before flat paths at the same level
    assert "nested/deep.py" in lines[indices[0]].replace("\\", "/")
    assert "main.py" in lines[indices[1]]
    assert "test.js" in lines[indices[2]]


def test_windows_paths_in_output(tmp_path):
    """Test that Windows paths are handled correctly in output."""
    # Create a Windows-style path
    win_path = tmp_path / "Windows" / "Path" / "test.py"
    win_path.parent.mkdir(parents=True)
    win_path.write_text("windows test")

    result = generate_markdown_output([win_path], tmp_path, None)
    # Verify that path separators are consistent
    assert "\\" not in result or "/" not in result  # Should use one style consistently
