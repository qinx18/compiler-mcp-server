# Implement proper MCP protocol handshake testing

## Issue Description

The compiler MCP server needs comprehensive tests to ensure it properly handles the MCP protocol handshake with Claude Desktop. Currently, we have basic tests but no tests for the actual protocol communication.

## Requirements

1. Test that the server responds correctly to MCP initialization messages
2. Test that the server properly advertises its capabilities
3. Test error handling for malformed requests
4. Test the complete handshake sequence

## Test-Driven Development Instructions

Read this github issue: [URL to this issue]

Once you have understood the issue, first read the existing testing code in `tests/test_mcp_connection.py` and find a good place to add one or more new tests that fail, demonstrating that the issue exists.

Do NOT write any code to fix the issue until you have written a test reproducing the issue and confirmed that it fails when running. If you are not able to reproduce the issue, ask me for help.

The tests should:

1. Send proper MCP protocol messages to the server
2. Verify the server responds with correct protocol messages
3. Test both success and failure cases

Start by creating failing tests in `tests/test_mcp_protocol.py` that demonstrate what proper MCP communication should look like.
