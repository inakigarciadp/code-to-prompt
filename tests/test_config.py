from code_to_prompt.config import OutputConfig, parse_output_config


def test_output_config_creation():
    """Test basic creation of OutputConfig objects."""
    # Test with both type and path
    config = OutputConfig(type="file", path="output.md")
    assert config.type == "file"
    assert config.path == "output.md"

    # Test with only type
    config = OutputConfig(type="console")
    assert config.type == "console"
    assert config.path is None


def test_parse_output_config_console():
    """Test parsing console output configuration."""
    config = parse_output_config("console")
    assert config.type == "console"
    assert config.path is None


def test_parse_output_config_file():
    """Test parsing file output configuration."""
    config = parse_output_config("file=output.md")
    assert config.type == "file"
    assert config.path == "output.md"

    # Test with spaces around equals sign
    config = parse_output_config("file = test.md")
    assert config.type == "file"
    assert config.path == "test.md"


def test_parse_output_config_with_spaces():
    """Test parsing output configuration with extra spaces."""
    # Test with spaces before and after
    config = parse_output_config("  console  ")
    assert config.type == "console"
    assert config.path is None

    # Test with spaces around equals and values
    config = parse_output_config("  file  =  output.md  ")
    assert config.type == "file"
    assert config.path == "output.md"
