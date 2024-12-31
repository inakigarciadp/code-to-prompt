# Code-to-Prompt Repository Guide

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

## Application Overview

### Purpose
Code-to-Prompt is a command-line tool designed to convert codebases into prompts suitable for Large Language Models (LLMs). It analyzes a codebase and generates a structured Markdown representation that includes both file structure and contents, making it easy to communicate code organization and implementation details to LLMs.

### Key Features
- Recursive file system traversal
- Gitignore support (including default Git behaviors)
- Multiple output destinations (console, file)
- Markdown-formatted output with syntax highlighting
- Automatic language detection for code blocks
- Robust file content reading with encoding handling
- Cross-platform compatibility
- Rich terminal output

### How It Works
The application follows these high-level steps:
1. Accepts a directory path (or uses current directory)
2. Loads and parses `.gitignore` rules if present
3. Recursively traverses the directory while respecting ignore patterns
4. Reads file contents with appropriate encoding detection
5. Determines programming language for syntax highlighting
6. Generates a structured Markdown output with code blocks
7. Routes output to selected destinations (console, file)
8. Provides feedback on output operations

## Code Explanation

### Core Components

#### CLI Interface (`app = typer.Typer()`)
The application uses Typer to create a user-friendly command-line interface. The main command accepts:
- An optional directory argument
- Multiple output destinations via `--output` options
- Provides helpful error messages and usage information

#### File Content System
The file content system consists of three main components:
- `read_file_content()`: Safely reads file contents with encoding handling
- `get_file_language()`: Determines appropriate language for syntax highlighting
- `generate_markdown_output()`: Formats files and their contents into Markdown

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
1. `get_files_recursively()`: Collects all relevant files while applying ignore rules
2. `read_file_content()`: Reads and processes file contents with encoding detection
3. `get_file_language()`: Determines appropriate syntax highlighting
4. `generate_markdown_output()`: Formats everything into Markdown with code blocks
5. Output handlers: Route content to specified destinations

### Data Flow
1. User input → CLI argument parsing
2. Directory resolution and validation
3. Output configuration parsing
4. Gitignore rules loading (if present)
5. File discovery and filtering
6. File content reading and processing
7. Language detection and markdown generation
8. Output distribution to handlers

### CLI Usage Examples

Basic usage with default output (console):
```bash
code-to-prompt
```

Output to a file:
```bash
code-to-prompt --output file=output.md
```

Multiple outputs:
```bash
code-to-prompt --output console --output file=output.md
```

Short form:
```bash
code-to-prompt -o console -o file=output.md
```

### Output Format
The tool generates Markdown output with the following structure:
```markdown
# Codebase Contents

## File: `src/example.py`

```python
def hello():
    print("Hello, world!")
```