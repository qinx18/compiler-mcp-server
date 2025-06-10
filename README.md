# Compiler MCP Server

An intelligent compiler server that provides detailed vectorization analysis and optimization suggestions for C/C++ code.

## Features

- Loop-carried dependency detection
- Vectorization failure analysis
- Optimization suggestions
- Stateful compilation sessions

## Installation

```bash
pip install -r requirements.txt
```

## Development Setup

For contributors, install pre-commit hooks for code quality:

```bash
pip install pre-commit
pre-commit install
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
