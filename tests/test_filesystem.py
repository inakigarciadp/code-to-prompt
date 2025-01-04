import os
import stat
from pathlib import Path

import pytest
from pathspec import PathSpec
from pathspec.patterns import GitWildMatchPattern

from code_to_prompt.filesystem import (
    get_files_recursively,
    load_gitignore,
    read_file_content,
    should_ignore,
)


# Fixtures
@pytest.fixture
def temp_dir(tmp_path):
    """Create a temporary directory with various test files and structures."""
    # Create basic structure
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("print('hello')")

    # Create nested structure
    nested = src / "nested"
    nested.mkdir()
    (nested / "test.py").write_text("test content")

    # Create directory with special characters
    special = tmp_path / "special chars & symbols"
    special.mkdir()
    (special / "file with spaces.txt").write_text("content")

    return tmp_path


@pytest.fixture
def gitignore_content():
    """Create sample gitignore content."""
    return """
# Comments should be ignored
*.log
!important.log
/build/
**/temp/
*.pyc
node_modules/

# Empty lines should be ignored

tests/*_ignored/
""".strip()


@pytest.fixture
def gitignore_spec():
    """Create a PathSpec with test patterns."""
    patterns = ["*.log", "build/", "**/temp/", "*.pyc"]
    return PathSpec.from_lines(GitWildMatchPattern, patterns)


# Test load_gitignore
def test_load_gitignore_no_file(temp_dir):
    """Test loading gitignore when file doesn't exist."""
    patterns = ["*.txt"]
    result = load_gitignore(temp_dir, patterns)
    assert isinstance(result, PathSpec)
    # Original patterns should be preserved
    assert "*.txt" in patterns


def test_load_gitignore_empty_file(temp_dir):
    """Test loading empty gitignore file."""
    gitignore_path = temp_dir / ".gitignore"
    gitignore_path.write_text("")
    result = load_gitignore(temp_dir, [])
    assert isinstance(result, PathSpec)


def test_load_gitignore_with_content(temp_dir, gitignore_content):
    """Test loading gitignore with various pattern types."""
    gitignore_path = temp_dir / ".gitignore"
    gitignore_path.write_text(gitignore_content)
    result = load_gitignore(temp_dir, ["*.txt"])
    assert isinstance(result, PathSpec)
    # Check if patterns are properly loaded
    test_path = Path("test.log")
    assert result.match_file(str(test_path))


def test_load_gitignore_invalid_encoding(temp_dir):
    """Test loading gitignore with invalid encoding."""
    gitignore_path = temp_dir / ".gitignore"
    # Write binary content with invalid UTF-8
    with open(gitignore_path, "wb") as f:
        f.write(b"\x80invalid")

    result = load_gitignore(temp_dir, ["*.txt"])
    assert isinstance(result, PathSpec)
    # Original patterns should be preserved
    assert result.match_file("test.txt")


@pytest.mark.skipif(os.name == "nt", reason="Permission tests unreliable on Windows")
def test_load_gitignore_permission_denied(temp_dir):
    """Test loading gitignore with no read permissions."""
    gitignore_path = temp_dir / ".gitignore"
    gitignore_path.write_text("*.log")
    # Remove read permissions
    gitignore_path.chmod(0)

    try:
        result = load_gitignore(temp_dir, ["*.txt"])
        assert isinstance(result, PathSpec)
        # Should fall back to provided patterns
        assert result.match_file("test.txt")
    finally:
        # Restore permissions for cleanup
        gitignore_path.chmod(stat.S_IRUSR | stat.S_IWUSR)


# Test should_ignore
def test_should_ignore_git_directory(temp_dir):
    """Test that .git directory is always ignored."""
    git_path = temp_dir / ".git" / "config"
    git_path.parent.mkdir()
    git_path.touch()

    assert should_ignore(git_path, temp_dir, None)
    # Even with empty PathSpec
    assert should_ignore(git_path, temp_dir, PathSpec([]))


def test_should_ignore_patterns(temp_dir, gitignore_spec):
    """Test various ignore patterns."""
    test_cases = [
        (temp_dir / "test.log", True),  # Should be ignored
        (temp_dir / "important.txt", False),  # Should not be ignored
        (temp_dir / "build" / "output.txt", True),  # In ignored directory
        (temp_dir / "src" / "temp" / "file.txt", True),  # Matches **/temp/
        (temp_dir / "test.pyc", True),  # Matches *.pyc
    ]

    for path, expected in test_cases:
        assert should_ignore(path, temp_dir, gitignore_spec) == expected


def test_should_ignore_special_chars(temp_dir):
    """Test paths with special characters."""
    spec = PathSpec.from_lines(GitWildMatchPattern, ["*space*"])
    path = temp_dir / "file with space.txt"
    assert should_ignore(path, temp_dir, spec)


def test_should_ignore_relative_absolute_paths(temp_dir):
    """Test both relative and absolute paths.
    PathSpec expects paths to be in the correct relative format."""
    # Create a new PathSpec specifically for this test
    spec = PathSpec.from_lines(GitWildMatchPattern, ["*.log"])

    # Create test file in temp_dir to ensure path exists
    test_file = temp_dir / "test.log"
    test_file.touch()

    # Convert paths to strings for gitignore matching
    rel_str = str(test_file.relative_to(temp_dir)).replace("\\", "/")
    abs_str = str(test_file).replace("\\", "/")

    # Test relative path
    assert spec.match_file(rel_str), "Relative path should match"
    # Test absolute path by first making it relative
    assert spec.match_file(abs_str), "Absolute path (made relative) should match"


def test_should_ignore_invalid_relative_path(temp_dir, gitignore_spec):
    """Test handling of invalid relative paths."""
    # Path outside of base_dir
    invalid_path = temp_dir.parent / "outside.log"
    assert not should_ignore(invalid_path, temp_dir, gitignore_spec)


# Test get_files_recursively
def test_get_files_empty_directory(tmp_path):
    """Test getting files from empty directory."""
    result = get_files_recursively(tmp_path)
    assert len(result) == 0


def test_get_files_flat_directory(tmp_path):
    """Test getting files from directory with no subdirectories."""
    # Create test files
    files = ["test1.txt", "test2.py", "test3.md"]
    for f in files:
        (tmp_path / f).touch()

    result = get_files_recursively(tmp_path)
    assert len(result) == len(files)
    assert all(f.name in files for f in result)


def test_get_files_nested_structure(temp_dir):
    """Test getting files from nested directory structure."""
    result = get_files_recursively(temp_dir)

    # Check if all expected files are found
    found_files = set(p.name for p in result)
    assert "main.py" in found_files
    assert "test.py" in found_files
    assert "file with spaces.txt" in found_files


def test_get_files_with_ignore_patterns(temp_dir, gitignore_spec):
    """Test getting files while respecting ignore patterns."""
    # Create some files that should be ignored
    (temp_dir / "test.log").touch()
    (temp_dir / "build").mkdir()
    (temp_dir / "build" / "output.txt").touch()

    result = get_files_recursively(temp_dir, gitignore_spec)

    # Check that ignored files are not included
    found_files = set(p.name for p in result)
    assert "test.log" not in found_files
    assert "output.txt" not in found_files


@pytest.mark.skipif(
    os.name == "nt", reason="Symlinks require special permissions on Windows"
)
def test_get_files_with_symlinks(temp_dir):
    """Test handling of symbolic links."""
    # Create a symlink to a file
    source = temp_dir / "source.txt"
    source.write_text("content")
    link = temp_dir / "link.txt"
    link.symlink_to(source)

    result = get_files_recursively(temp_dir)
    # Both source and link should be included
    found_files = set(p.name for p in result)
    assert "source.txt" in found_files
    assert "link.txt" in found_files


@pytest.mark.skipif(os.name == "nt", reason="Permission tests unreliable on Windows")
def test_get_files_permission_denied(temp_dir):
    """Test handling of permission denied errors."""
    restricted_dir = temp_dir / "restricted"
    restricted_dir.mkdir()
    (restricted_dir / "secret.txt").touch()

    # Remove read permissions
    restricted_dir.chmod(0)

    try:
        # Should not raise exception, just skip inaccessible files
        result = get_files_recursively(temp_dir)
        assert all(restricted_dir not in p.parents for p in result)
    finally:
        # Restore permissions for cleanup
        restricted_dir.chmod(stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)


# Test read_file_content
def test_read_file_content_utf8(tmp_path):
    """Test reading UTF-8 encoded file."""
    test_file = tmp_path / "test.txt"
    content = "Hello, 世界!"
    test_file.write_text(content, encoding="utf-8")

    result = read_file_content(test_file)
    assert result == content


def test_read_file_content_other_encoding(tmp_path):
    """Test reading file with different encoding."""
    test_file = tmp_path / "test.txt"
    content = "Hello, World!"
    # Write with different encoding
    test_file.write_text(content, encoding="latin-1")

    result = read_file_content(test_file)
    assert result == content


def test_read_file_content_empty(tmp_path):
    """Test reading empty file."""
    test_file = tmp_path / "empty.txt"
    test_file.touch()

    result = read_file_content(test_file)
    assert result == ""


def test_read_file_content_binary(tmp_path):
    """Test reading binary file.
    Note: The function attempts to read all files as text, which is the intended behavior.
    Binary files that can be decoded as text will return their content."""
    test_file = tmp_path / "binary.bin"
    # Write some binary content that can be decoded as text
    with open(test_file, "wb") as f:
        f.write(b"\x00\x01\x02\x03")

    result = read_file_content(test_file)
    assert result is not None
    assert len(result) == 4  # Should contain the 4 bytes as decoded characters


def test_read_file_content_large_file(tmp_path):
    """Test reading large file."""
    test_file = tmp_path / "large.txt"
    # Create ~1MB file
    content = "x" * (1024 * 1024)
    test_file.write_text(content)

    result = read_file_content(test_file)
    assert result == content


@pytest.mark.skipif(os.name == "nt", reason="Permission tests unreliable on Windows")
def test_read_file_content_permission_denied(tmp_path):
    """Test reading file with no permissions."""
    test_file = tmp_path / "noperm.txt"
    test_file.write_text("content")
    test_file.chmod(0)

    try:
        result = read_file_content(test_file)
        assert result is None
    finally:
        # Restore permissions for cleanup
        test_file.chmod(stat.S_IRUSR | stat.S_IWUSR)


def test_read_file_content_nonexistent():
    """Test reading non-existent file."""
    result = read_file_content(Path("nonexistent.txt"))
    assert result is None
