import os
from pathlib import Path
from typing import Generator

import pytest
from typer.testing import CliRunner

from code_to_prompt.cli import app

# Setup test runner
runner = CliRunner()


@pytest.fixture
def temp_project(tmp_path) -> Generator[Path, None, None]:
    """Create a temporary project structure for testing."""
    # Create main project directory
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()

    # Create some test files and directories
    src_dir = project_dir / "src"
    src_dir.mkdir()

    # Create a Python file
    python_file = src_dir / "main.py"
    python_file.write_text("print('Hello, World!')")

    # Create a README
    readme = project_dir / "README.md"
    readme.write_text("# Test Project\nThis is a test.")

    # Create a .gitignore file
    gitignore = project_dir / ".gitignore"
    gitignore.write_text("*.log\ntemp/")

    yield project_dir


def test_cli_default_directory(temp_project):
    """Test CLI with default directory (current working directory)."""
    # Change to the temporary project directory
    with runner.isolated_filesystem():
        os.chdir(str(temp_project))
        result = runner.invoke(app)

        # Check the command executed successfully
        assert result.exit_code == 0

        # Check output contains expected content (with rich formatting)
        assert "Codebase Contents" in result.stdout  # Check for title without markdown
        assert "Directory Structure" in result.stdout
        assert "test_project" in result.stdout
        assert "src" in result.stdout
        assert "main.py" in result.stdout
        assert "README.md" in result.stdout


def test_cli_explicit_directory(temp_project):
    """Test CLI with explicitly provided directory."""
    result = runner.invoke(app, [str(temp_project)])

    assert result.exit_code == 0
    assert "Codebase Contents" in result.stdout  # Check for title without markdown
    assert "Directory Structure" in result.stdout
    assert "test_project" in result.stdout


def test_cli_custom_output_file(temp_project):
    """Test CLI with file output."""
    output_file = temp_project / "output.md"
    result = runner.invoke(app, [str(temp_project), "--output", f"file={output_file}"])

    assert result.exit_code == 0
    assert output_file.exists()

    # Check the content of the output file
    content = output_file.read_text()
    assert "# Codebase Contents" in content
    assert "Directory Structure" in content


def test_cli_ignore_patterns(temp_project):
    """Test CLI with custom ignore patterns."""
    # Create a file that should be ignored
    log_file = temp_project / "test.log"
    log_file.write_text("This should be ignored")

    result = runner.invoke(app, [str(temp_project), "--ignore", "*.log"])

    assert result.exit_code == 0
    assert "test.log" not in result.stdout


def test_cli_extra_ignore_patterns(temp_project):
    """Test CLI with extra ignore patterns."""
    # Create files that should be ignored
    custom_file = temp_project / "custom.txt"
    custom_file.write_text("This should be ignored")

    result = runner.invoke(app, [str(temp_project), "--extra-ignore", "*.txt"])

    assert result.exit_code == 0
    assert "custom.txt" not in result.stdout


def test_cli_multiple_outputs(temp_project):
    """Test CLI with multiple output destinations."""
    output_file = temp_project / "output.md"
    result = runner.invoke(
        app,
        [str(temp_project), "--output", "console", "--output", f"file={output_file}"],
    )

    assert result.exit_code == 0
    # Check console output (with rich formatting)
    assert "Codebase Contents" in result.stdout
    # Check file output (should be markdown)
    assert output_file.exists()
    assert "# Codebase Contents" in output_file.read_text()


def test_cli_non_existent_directory():
    """Test CLI with non-existent directory."""
    result = runner.invoke(app, ["non_existent_dir"])
    assert result.exit_code != 0  # Should fail
