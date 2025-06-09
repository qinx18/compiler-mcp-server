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

## Example

```c
The server can analyze code like this s1113 pattern:

for (int i = 0; i < LEN_1D; i++) {
    a[i] = a[LEN_1D/2 - i] + b[i];
}

And provide detailed feedback about why vectorization fails.
```
