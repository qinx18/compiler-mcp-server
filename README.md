# Compiler MCP Server

An intelligent compiler MCP server focused on vectorization analysis for C/C++ code.

## Features

- Loop-carried dependency detection
- Vectorization failure analysis  
- Optimization suggestions for C/C++ code
- Stateful compilation sessions
- MCP protocol compliance
- Real-time compilation feedback

## Quick Start

### Installation

```bash
# Install in development mode
make install-dev

# Or manually
pip install -e ".[dev]"
pre-commit install
```

## Development

### Prerequisites

- Python 3.8+
- GCC or compatible C/C++ compiler
- Git

### Development Setup

```bash
# Clone and setup
git clone <repository-url>
cd compiler-mcp-server
make dev-setup
```

### Code Quality

This project uses modern Python development practices:

- **Type Checking**: MyPy for static type analysis
- **Linting**: Ruff for fast Python linting
- **Formatting**: Black and Ruff for code formatting
- **Security**: Bandit for security vulnerability scanning
- **Pre-commit Hooks**: Automated quality checks
- **Testing**: Pytest with coverage reporting
- **CI/CD**: GitHub Actions for continuous integration

### Available Commands

```bash
# Development workflow
make help              # Show all available commands
make quality           # Run all quality checks
make test              # Run tests with coverage
make lint              # Run linting
make format            # Format code
make type-check        # Run type checking
make security-check    # Run security analysis
make pre-commit        # Run pre-commit hooks
make clean             # Clean build artifacts
make build             # Build package

# Quick development cycle
make format lint type-check test
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed development guidelines.

## Usage

```bash
# Test mode
python solution_for_s1113.py --mode test

# Run as MCP server
python solution_for_s1113.py
```

## OpenHands Resolver Setup

This repository includes an automated issue resolver using OpenHands. To enable it:

1. **Set up GitHub Secrets** (in repository Settings > Secrets and variables > Actions):
   - `PAT_TOKEN`: Personal Access Token with repo permissions
   - `PAT_USERNAME`: Your GitHub username
   - `LLM_API_KEY`: API key for Claude or other LLM service
   - `LLM_MODEL`: Model name (e.g., `anthropic/claude-3-5-sonnet-20241022`)

2. **Enable Workflow Permissions**:
   - Go to Settings > Actions > General > Workflow permissions
   - Select "Read and write permissions"
   - Enable "Allow GitHub Actions to create and approve pull requests"

3. **Usage**:
   - Add the `fix-me` label to any issue for automatic resolution
   - Or mention `@openhands-agent` in a comment

## Example

```c
The server can analyze code like this s1113 pattern:

for (int i = 0; i < LEN_1D; i++) {
    a[i] = a[LEN_1D/2 - i] + b[i];
}

And provide detailed feedback about why vectorization fails.
```
