# Code-to-Prompt Repository Guide

## Project Structure

The project is organized into several modules, each with a specific responsibility:

```
code-to-prompt/
├── code_to_prompt/          # Main package directory
│   ├── __init__.py         # Package initialization and version
│   ├── cli.py              # Command-line interface implementation
│   ├── config.py           # Configuration structures and parsing
│   ├── constants.py        # Constant values and default patterns
│   ├── filesystem.py       # File system operations
│   ├── formatters.py       # Output formatting and markdown generation
│   └── handlers.py         # Output handling (console, file)
├── main.py                 # Entry point script
├── .gitignore
├── LICENSE
├── README.md
└── pyproject.toml
```

### Module Descriptions

- `__init__.py`: Package initialization, version information, and exports
- `cli.py`: Implements the command-line interface using Typer
- `config.py`: Defines configuration classes and parsing utilities
- `constants.py`: Contains default ignore patterns and other constants
- `filesystem.py`: Handles file system operations and gitignore pattern matching
- `formatters.py`: Manages output formatting and markdown generation
- `handlers.py`: Implements different output handlers (console, file)
- `main.py`: Entry point that imports and runs the application

## Project Dependencies

The application relies on a few carefully selected dependencies:

1. **typer** (required)
   - Modern library for building CLI applications
   - Built on top of Click with added type hint support
   - Used for handling command-line arguments and providing help messages

2. **rich** (required)
   - Terminal formatting and styling
   - Used for rendering Markdown output and colorized messages
   - Provides cross-platform ANSI support

3. **pathspec** (required)
   - Utility for handling gitignore-style pattern matching
   - Same pattern matching engine used by git-python
   - Ensures consistent behavior with Git's ignore patterns

### Installation
```bash
pip install typer rich pathspec
```

## Code Style Guide

### Python Standards and Best Practices

1. **Python Version**: This project uses Python 3.12+ and takes advantage of its modern features
   - Use built-in types for type hints (e.g., `list[str]` instead of `List[str]`)
   - Leverage new typing features when appropriate (e.g., `|` for unions)
   - Use modern string formatting with f-strings

2. **Type Hints**:
   - All functions must include type hints for parameters and return values
   - Use built-in types as generics (e.g., `list[Path]`, `dict[str, int]`)
   - Use `Optional[T]` or `T | None` for optional values
   - Create type aliases using `TypeAlias` for complex types
   - Use dataclasses for structured data when appropriate

3. **Code Structure**:
   - Use `pathlib.Path` for all file system operations
   - Prefer context managers (`with` statements) for file operations
   - Keep functions focused and single-purpose
   - Use descriptive variable names that reflect their purpose
   - Prefer functional approaches for simple, composable solutions

4. **Documentation**:
   - All functions must have docstrings using the following format:
     ```python
     def function_name(param: type) -> return_type:
         """
         Brief description.
         
         Args:
             param: Description of parameter
             
         Returns:
             Description of return value
         """
     ```
   - Include examples in docstrings for complex functionality
   - Add inline comments only for non-obvious code sections

5. **Error Handling**:
   - Use specific exception types when catching errors
   - Provide meaningful error messages
   - Handle edge cases gracefully
   - Use warning messages when appropriate but non-fatal issues occur

### Project-Specific Guidelines

1. **CLI Design**:
   - All CLI commands should have clear help messages
   - Use meaningful default values
   - Implement proper argument validation
   - Follow the principle of least surprise
   - Support multiple options with consistent syntax

2. **Output System**:
   - Use function-based output handlers for flexibility
   - Each handler should follow the `OutputHandler` type signature
   - Provide clear feedback for output operations
   - Support multiple simultaneous outputs
   - Default to console output when no output specified

3. **Output Format**:
   - Use rich for terminal output formatting
   - Maintain consistent Markdown formatting with proper syntax highlighting
   - Include file contents with appropriate language identification
   - Handle various file encodings gracefully
   - Ensure cross-platform compatibility in output
   - Render markdown files as raw markdown instead of code blocks
   - Use syntax highlighting for all non-markdown files

4. **File Ignoring System**:
   - Use smart defaults from DEFAULT_IGNORE_PATTERNS
   - Support both replacement and extension of default patterns
   - Handle .gitignore patterns alongside custom patterns
   - Provide clear feedback about which files are ignored
   - Maintain consistent pattern matching behavior

## Application Overview

### Purpose
Code-to-Prompt is a command-line tool designed to convert codebases into prompts suitable for Large Language Models (LLMs). It analyzes a codebase and generates a structured Markdown representation that includes both file structure and contents, making it easy to communicate code organization and implementation details to LLMs.

### Key Features
- Directory tree visualization with proper hierarchical display
- Recursive file system traversal
- Smart file ignoring system with defaults
- Gitignore support (including default Git behaviors)
- Multiple output destinations (console, file)
- Markdown-formatted output with syntax highlighting
- Automatic language detection for code blocks
- Intelligent markdown file handling (rendered as raw markdown)
- Robust file content reading with encoding handling
- Cross-platform compatibility
- Rich terminal output

### How It Works
The application follows these high-level steps:
1. Accepts a directory path (or uses current directory)
2. Processes ignore patterns (defaults, custom, or extra)
3. Loads and parses `.gitignore` rules if present
4. Recursively traverses the directory while respecting ignore patterns
5. Generates a hierarchical tree view of the directory structure
6. Reads file contents with appropriate encoding detection
7. Determines programming language for syntax highlighting (except for markdown files)
8. Generates a structured Markdown output with tree view and formatted content
9. Routes output to selected destinations (console, file)
10. Provides feedback on output operations

### Core Components

#### CLI Interface (`app = typer.Typer()`)
The application uses Typer to create a user-friendly command-line interface. The main command accepts:
- An optional directory or file path argument
- Multiple output destinations via `--output` options
- File ignore patterns via `--ignore` and `--extra-ignore` options
- Analyze imports flag for Python files
- Provides helpful error messages and usage information

The CLI operates in two modes:
- Directory mode: Processes an entire directory structure (default)
- File mode: Processes a single file, providing focused output

#### File Ignoring System
The file ignoring system consists of several components:
- `DEFAULT_IGNORE_PATTERNS`: Predefined list of common files to ignore
- `--ignore` option: Replaces default patterns with custom ones
- `--extra-ignore` option: Adds patterns to the defaults
- Integration with .gitignore patterns
- Smart pattern matching with pathspec

#### Directory Tree Generation
The directory tree system provides a visual representation of the codebase structure:
- Generates an ASCII tree view of the directory hierarchy
- Respects all ignore patterns and gitignore rules
- Maintains consistent sorting for predictable output
- Provides visual indicators for directory structure
- Ensures cross-platform compatibility in display

#### File Content System
The file content system consists of three main components:
- `read_file_content()`: Safely reads file contents with encoding handling
- `get_file_language()`: Determines appropriate language for syntax highlighting
- `generate_markdown_output()`: Formats files and their contents into Markdown
  - Special handling for markdown files (rendered as raw markdown)
  - Code block formatting for all other file types

#### Output System
The output system uses a functional approach with three main components:
- `OutputConfig`: Dataclass for storing output configuration
- Output handlers: Functions that process content for different destinations
- Handler factory: Creates appropriate handlers based on user configuration

#### Gitignore Handling
The gitignore system consists of two main components:
- `load_gitignore()`: Reads and parses the `.gitignore` file using the `pathspec` library
- `should_ignore()`: Implements the ignore logic, including both `.gitignore` patterns and default Git behaviors

#### File System Operations
The application uses `pathlib.Path` for all file system operations, providing:
- Cross-platform compatibility
- Type-safe path manipulation
- Consistent API for file operations
- Robust file content reading with encoding handling

#### Output Generation
The output system uses a multi-step process:
1. `generate_directory_tree()`: Creates a visual tree representation of the codebase
2. `get_files_recursively()`: Collects all relevant files while applying ignore rules
3. `read_file_content()`: Reads and processes file contents with encoding detection
4. `get_file_language()`: Determines appropriate syntax highlighting (skipped for markdown)
5. `generate_markdown_output()`: Formats everything into appropriate format
6. Output handlers: Route content to specified destinations

### Data Flow
1. User input → CLI argument parsing
2. Directory resolution and validation
3. Output configuration parsing
4. Ignore pattern processing
5. Gitignore rules loading (if present)
6. Directory tree generation
7. File discovery and filtering
8. File content reading and processing
9. Content formatting (raw markdown or syntax highlighted)
10. Output distribution to handlers

### CLI Usage Examples

Basic usage with default output and ignore patterns:
```bash
code-to-prompt
```

Custom ignore patterns (replacing defaults):
```bash
code-to-prompt --ignore "*.log" "temp/"
```

Additional ignore patterns (extending defaults):
```bash
code-to-prompt --extra-ignore "*.custom" "private/"
```

Disable all ignore patterns:
```bash
code-to-prompt --ignore
```

Output to a file:
```bash
code-to-prompt --output file=output.md
```

Multiple outputs with custom ignore patterns:
```bash
code-to-prompt --output console --output file=output.md --ignore "*.log" --extra-ignore "private/"
```

Short form:
```bash
code-to-prompt -o console -o file=output.md -i "*.log" -e "private/"
```

Process a single file:
```bash
code-to-prompt path/to/file.py
```

Analyze imports in a file:
```bash
code-to-prompt path/to/file.py --analyze-imports
```

### Output Format
The tool generates Markdown output with the following structure:
```markdown
# Codebase Contents

## Directory Structure

project_name
├── src
│   ├── module1
│   │   └── file1.py
│   └── module2
│       ├── file2.py
│       └── file3.py
└── README.md

## File Contents

### File: `README.md`

# Project documentation
This is rendered as raw markdown

### File: `src/module1/file1.py`

```python
def hello():
    print("Hello, world!")
```
