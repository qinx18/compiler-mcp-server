---
name: Compiler MCP Server Repository Agent
trigger_type: always
---

# Compiler MCP Server Repository Agent

This is an intelligent compiler MCP server focused on vectorization analysis for C/C++ code.

## Project Overview

The main file is `solution_for_s1113.py` which implements a Model Context Protocol (MCP) server that provides:

- Loop-carried dependency detection
- Vectorization failure analysis
- Optimization suggestions for C/C++ code
- Stateful compilation sessions

## Key Commands

- Test the server: `python solution_for_s1113.py --mode test`
- Run as MCP server: `python solution_for_s1113.py`
- Run as HTTP server: `python solution_for_s1113.py --mode http --port 8080`

## Development Guidelines

1. Always test changes with the built-in test mode first
2. The server uses GCC by default but can be configured for other compilers
3. Focus on improving dependency analysis accuracy
4. Maintain backward compatibility with the MCP protocol

## Code Structure

- `CompilerMCPServer`: Main server class handling compilation and analysis
- `DependencyAnalyzer`: Analyzes loop-carried dependencies
- `@mcp.tool()` decorators: Define MCP-accessible functions

## Testing

When making changes, test with the s1113 pattern:

```c
for (int i = 0; i < LEN_1D; i++) {
    a[i] = a[LEN_1D/2 - i] + b[i];
}
```

This pattern should detect a loop-carried dependency at distance LEN_1D/4.
