import io

import pytest
import rich
import typer
from rich.console import Console

from code_to_prompt.config import OutputConfig
from code_to_prompt.handlers import (
    console_output,
    file_output,
    get_output_handlers,
)


@pytest.fixture
def temp_dir(tmp_path):
    """Provide a temporary directory for file output tests."""
    return tmp_path


@pytest.fixture
def capture_rich_output():
    """Capture rich console output for testing."""
    console = Console(file=io.StringIO(), force_terminal=True)
    # Save the original console
    original_console = rich.get_console()
    # Set our test console as the global console
    rich.get_console = lambda: console

    yield console

    # Restore the original console
    rich.get_console = lambda: original_console


def test_console_output(capture_rich_output):
    """Test that console output correctly formats markdown content."""
    test_content = "# Test Header\nTest content"
    console_output(test_content)

    # Get the output from our captured console
    output = capture_rich_output.file.getvalue()

    # Check that output contains our content
    assert "Test Header" in output
    assert "Test content" in output


def test_file_output(temp_dir):
    """Test that file output writes content to the specified file."""
    test_content = "# Test Content\nThis is test content"
    output_file = temp_dir / "test_output.md"

    # Write content to file
    file_output(test_content, str(output_file))

    # Verify file exists and contains correct content
    assert output_file.exists()
    assert output_file.read_text() == test_content


def test_get_output_handlers_console():
    """Test that get_output_handlers creates correct console handler."""
    configs = [OutputConfig(type="console")]
    handlers = get_output_handlers(configs)

    # Should return a list with one handler
    assert len(handlers) == 1
    # Handler should be callable
    assert callable(handlers[0])


def test_get_output_handlers_file(temp_dir):
    """Test that get_output_handlers creates correct file handler."""
    output_path = temp_dir / "test.md"
    configs = [OutputConfig(type="file", path=str(output_path))]
    handlers = get_output_handlers(configs)

    # Should return a list with one handler
    assert len(handlers) == 1
    # Handler should be callable
    assert callable(handlers[0])

    # Test the handler works
    test_content = "# Test"
    handlers[0](test_content)
    assert output_path.exists()
    assert output_path.read_text() == test_content


def test_get_output_handlers_multiple(temp_dir):
    """Test that get_output_handlers handles multiple output configurations."""
    output_path = temp_dir / "test.md"
    configs = [
        OutputConfig(type="console"),
        OutputConfig(type="file", path=str(output_path)),
    ]
    handlers = get_output_handlers(configs)

    # Should return two handlers
    assert len(handlers) == 2
    # Both handlers should be callable
    assert all(callable(h) for h in handlers)


def test_get_output_handlers_invalid_type():
    """Test that get_output_handlers raises error for invalid output type."""
    configs = [OutputConfig(type="invalid")]

    with pytest.raises(typer.BadParameter):
        get_output_handlers(configs)


def test_get_output_handlers_missing_file_path():
    """Test that get_output_handlers raises error when file path is missing."""
    configs = [OutputConfig(type="file")]

    with pytest.raises(typer.BadParameter):
        get_output_handlers(configs)
