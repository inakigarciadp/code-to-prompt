from pathlib import Path

import pytest

from code_to_prompt.filesystem import (
    get_files_recursively,
    load_gitignore,
    read_file_content,
    should_ignore,
)


@pytest.fixture
def temp_dir(tmp_path):
    """Create a temporary directory with test files and structure."""
    # Create some test files
    test_file = tmp_path / "test.txt"
    test_file.write_text("test content")

    # Create a subdirectory with files
    subdir = tmp_path / "subdir"
    subdir.mkdir()
    subdir_file = subdir / "subfile.txt"
    subdir_file.write_text("subdir content")

    # Create a .gitignore file
    gitignore = tmp_path / ".gitignore"
    gitignore.write_text("*.log\ntemp/")

    return tmp_path


def test_load_gitignore(temp_dir):
    """Test loading gitignore patterns."""
    # Test with additional patterns
    additional_patterns = ["*.pyc", "node_modules/"]
    gitignore_spec = load_gitignore(temp_dir, additional_patterns)

    # Verify the spec matches both .gitignore and additional patterns
    assert gitignore_spec.match_file("test.log")  # From .gitignore
    assert gitignore_spec.match_file("temp/file.txt")  # From .gitignore
    assert gitignore_spec.match_file("test.pyc")  # From additional patterns
    assert gitignore_spec.match_file("node_modules/file.js")  # From additional patterns

    # Verify non-ignored files don't match
    assert not gitignore_spec.match_file("test.txt")
    assert not gitignore_spec.match_file("subdir/file.txt")


def test_should_ignore(temp_dir):
    """Test if files are correctly identified for ignoring."""
    gitignore_spec = load_gitignore(temp_dir, ["*.log"])

    # Test ignored file
    ignored_file = temp_dir / "test.log"
    assert should_ignore(ignored_file, temp_dir, gitignore_spec)

    # Test non-ignored file
    normal_file = temp_dir / "test.txt"
    assert not should_ignore(normal_file, temp_dir, gitignore_spec)

    # Test .git directory is always ignored
    git_file = temp_dir / ".git" / "config"
    assert should_ignore(git_file, temp_dir, gitignore_spec)


def test_get_files_recursively(temp_dir):
    """Test recursive file discovery with ignore patterns."""
    # Include .gitignore in the ignore patterns
    gitignore_spec = load_gitignore(temp_dir, ["*.log", ".gitignore"])

    # Create some test files including ones that should be ignored
    (temp_dir / "test.log").write_text("should be ignored")
    (temp_dir / "test2.txt").write_text("should be included")

    files = get_files_recursively(temp_dir, gitignore_spec)

    # Convert to set of Path objects for platform-independent comparison
    file_paths = {f.relative_to(temp_dir) for f in files}

    # Check expected files are present using Path objects
    assert Path("test.txt") in file_paths
    assert (
        Path("subdir") / "subfile.txt" in file_paths
    )  # Using path joining for clarity
    assert Path("test2.txt") in file_paths

    # Check ignored files are not present
    assert Path("test.log") not in file_paths  # Ignored by pattern
    assert Path(".gitignore") not in file_paths  # Ignored by pattern


def test_read_file_content(temp_dir):
    """Test file content reading with different encodings."""
    # Test reading UTF-8 file
    test_file = temp_dir / "test.txt"
    content = read_file_content(test_file)
    assert content == "test content"

    # Test reading non-existent file
    nonexistent = temp_dir / "nonexistent.txt"
    assert read_file_content(nonexistent) is None
