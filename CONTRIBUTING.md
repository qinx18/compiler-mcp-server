# Contributing to Compiler MCP Server

## Development Setup

### Prerequisites

- Python 3.8+
- Git

### Setting up the development environment

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd compiler-mcp-server
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   pip install pre-commit
   ```

3. Install pre-commit hooks:
   ```bash
   pre-commit install
   ```

## Code Quality

This project uses pre-commit hooks to maintain code quality. The following tools are configured:

### Formatting
- **Black**: Code formatter with 88-character line length
- **isort**: Import statement organizer

### Linting
- **flake8**: Python linting with relaxed line length rules
- **bandit**: Security vulnerability scanner (configured for compiler context)

### General Checks
- Trailing whitespace removal
- End-of-file fixing
- YAML validation
- Large file detection
- Merge conflict detection

## Pre-commit Usage

### Automatic execution
Pre-commit hooks run automatically on every commit. If any hook fails, the commit is blocked until issues are fixed.

### Manual execution
Run hooks on all files:
```bash
pre-commit run --all-files
```

Run hooks on specific files:
```bash
pre-commit run --files solution_for_s1113.py
```

### Updating hooks
Update to the latest versions:
```bash
pre-commit autoupdate
```

## Testing

Test the MCP server functionality:
```bash
python solution_for_s1113.py --mode test
```

Run as HTTP server for testing:
```bash
python solution_for_s1113.py --mode http --port 8080
```

## Security Considerations

The bandit security scanner is configured to skip certain warnings that are expected in a compiler analysis context:
- B404: subprocess module usage (needed for compiler invocation)
- B603: subprocess calls (needed for compilation)
- B104: binding to all interfaces (needed for HTTP server mode)

## Commit Guidelines

1. Make sure all pre-commit hooks pass
2. Write clear, descriptive commit messages
3. Test your changes with the built-in test mode
4. Focus on minimal changes that solve specific problems

## Code Style

- Follow PEP 8 with 88-character line length
- Use type hints where appropriate
- Write docstrings for public functions and classes
- Keep functions focused and modular
- Prefer composition over inheritance
