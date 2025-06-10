# MCP Protocol Testing Guide

This document describes the comprehensive test suite for the compiler MCP server's protocol implementation and Claude Desktop integration.

## Overview

The test suite ensures that the compiler MCP server properly implements the Model Context Protocol (MCP) and can successfully communicate with Claude Desktop and other MCP clients.

## Test Structure

### Test Files

1. **`tests/test_mcp_connection.py`** - Basic server functionality and configuration
2. **`tests/test_mcp_protocol.py`** - Comprehensive MCP protocol compliance tests
3. **`tests/test_mcp_real_communication.py`** - Real server communication integration tests
4. **`tests/conftest.py`** - Shared fixtures and configuration

### Test Categories

Tests are organized into the following categories using pytest markers:

- `@pytest.mark.mcp_protocol` - MCP protocol implementation tests
- `@pytest.mark.integration` - Integration tests with real server communication
- `@pytest.mark.performance` - Performance and load tests
- `@pytest.mark.claude_desktop` - Claude Desktop specific tests

## Running Tests

### Quick Start

```bash
# Run all tests
python run_mcp_tests.py

# Run specific test suite
python run_mcp_tests.py --suite basic
python run_mcp_tests.py --suite protocol
python run_mcp_tests.py --suite integration

# Skip integration tests (if server startup issues)
python run_mcp_tests.py --no-integration

# Verbose output
python run_mcp_tests.py --verbose
```

### Using pytest directly

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_mcp_protocol.py

# Run tests by marker
pytest -m mcp_protocol
pytest -m integration
pytest -m "not integration"  # Skip integration tests

# Verbose output
pytest -v -s
```

## Test Coverage

### 1. MCP Protocol Handshake Tests

**File**: `tests/test_mcp_protocol.py`

- **Initialization sequence**: Tests proper MCP initialize/initialized handshake
- **Request/response format**: Validates JSON-RPC 2.0 compliance
- **Tool discovery**: Tests tools/list functionality
- **Tool execution**: Tests tools/call with proper parameters
- **Error handling**: Tests error responses and edge cases

**Key test methods**:
- `test_mcp_initialize_request_format()`
- `test_mcp_initialized_notification_format()`
- `test_tools_list_request_format()`
- `test_tool_call_request_format()`
- `test_full_mcp_handshake_simulation()`

### 2. Real Communication Tests

**File**: `tests/test_mcp_real_communication.py`

- **Server startup**: Tests actual server process startup
- **Protocol communication**: Sends real JSON-RPC messages to server
- **Tool execution**: Tests actual tool calls with real responses
- **Performance**: Tests server responsiveness and handling of large inputs

**Key test methods**:
- `test_mcp_initialize_sequence()`
- `test_tools_list_request()`
- `test_tool_call_execution()`
- `test_large_code_analysis()`

### 3. Protocol Compliance Tests

**File**: `tests/test_mcp_protocol.py`

- **JSON-RPC compliance**: Validates proper JSON-RPC 2.0 format
- **Request ID uniqueness**: Ensures proper request tracking
- **Error response format**: Tests standard error responses
- **Message structure**: Validates required fields and formats

### 4. Claude Desktop Integration

**File**: `tests/test_mcp_connection.py`

- **Configuration generation**: Tests Claude Desktop config file creation
- **Server startup**: Tests server can start in stdio mode
- **Tool registration**: Validates tools are properly registered

## Test Scenarios

### Vectorization Analysis Testing

The tests include comprehensive scenarios for the vectorization analysis tool:

1. **Simple vectorizable code**:
   ```c
   for(int i = 0; i < 100; i++) {
       a[i] = b[i] + c[i];
   }
   ```

2. **Loop-carried dependency**:
   ```c
   for(int i = 1; i < 100; i++) {
       a[i] = a[i-1] + b[i];
   }
   ```

3. **S1113 pattern**:
   ```c
   for(int i = 0; i < LEN_1D; i++) {
       a[i] = a[LEN_1D/2 - i] + b[i];
   }
   ```

4. **Complex dependencies**:
   ```c
   for(int i = 2; i < 100; i++) {
       a[i] = a[i-1] + a[i-2] + b[i];
   }
   ```

### Error Handling Testing

- **Invalid JSON**: Tests server resilience to malformed messages
- **Unknown methods**: Tests proper error responses for unsupported methods
- **Malformed tool calls**: Tests handling of invalid tool parameters
- **Large inputs**: Tests server performance with large code samples

## Expected Test Results

### Successful Test Run

When all tests pass, you should see:

```
✅ MCP initialization sequence completed successfully
✅ Found 2 tools: ['analyze_vectorization_failure', 'create_compilation_session']
✅ Tool execution successful, analysis length: 500+ chars
✅ Session creation successful
🎉 All test suites passed!
```

### Common Issues and Solutions

#### 1. Server Startup Failures

**Symptom**: Integration tests fail with "Could not start MCP server"

**Solutions**:
- Check that `solution_for_s1113.py` is in the correct location
- Verify all dependencies are installed: `pip install -r requirements.txt`
- Run with `--no-integration` to skip these tests
- Check for Python path issues

#### 2. Import Errors

**Symptom**: `ImportError` or `ModuleNotFoundError`

**Solutions**:
- Ensure you're running from the project root directory
- Install test dependencies: `pip install pytest pytest-asyncio`
- Check that the MCP library is installed: `pip install fastmcp`

#### 3. Timeout Issues

**Symptom**: Tests timeout waiting for server responses

**Solutions**:
- Increase timeout values in test configuration
- Check system performance and available resources
- Run tests individually to isolate issues

## Continuous Integration

The tests are designed to run in CI environments. For GitHub Actions:

```yaml
- name: Run MCP Protocol Tests
  run: |
    python run_mcp_tests.py --suite basic
    python run_mcp_tests.py --suite protocol
    # Skip integration tests in CI if needed
    # python run_mcp_tests.py --suite integration
```

## Adding New Tests

### For New MCP Tools

When adding a new MCP tool:

1. Add tool tests to `test_mcp_protocol.py`:
   ```python
   @pytest.mark.asyncio
   async def test_new_tool_execution(self):
       result = await new_tool_function("test_input")
       assert "expected_output" in result
   ```

2. Add real communication tests to `test_mcp_real_communication.py`:
   ```python
   @pytest.mark.asyncio
   async def test_new_tool_via_mcp(self, mcp_server):
       tool_call_request = mcp_server.create_request(
           "tools/call",
           {"name": "new_tool", "arguments": {"param": "value"}}
       )
       # ... test implementation
   ```

### For New Protocol Features

When implementing new MCP protocol features:

1. Add protocol compliance tests
2. Add real communication tests
3. Update fixtures in `conftest.py` if needed
4. Update this documentation

## Debugging Tests

### Verbose Output

Use `-v -s` flags for detailed output:

```bash
pytest tests/test_mcp_real_communication.py -v -s
```

### Individual Test Execution

Run specific tests for debugging:

```bash
pytest tests/test_mcp_protocol.py::TestMCPProtocolHandshake::test_mcp_initialize_request_format -v -s
```

### Server Logs

For integration tests, check server stderr for detailed error information:

```python
# In test code
if response is None:
    stderr = mcp_server.server_process.stderr.read()
    print(f"Server stderr: {stderr}")
```

## Performance Benchmarks

The performance tests establish baselines for:

- **Tool execution time**: < 5 seconds for typical code analysis
- **Large code handling**: < 10 seconds for 10,000+ line files
- **Multiple requests**: Server should handle 5+ rapid requests
- **Memory usage**: Server should remain stable during extended use

## Security Considerations

The tests include security-related scenarios:

- **Input validation**: Tests with malformed and malicious inputs
- **Resource limits**: Tests with large inputs to prevent DoS
- **Error information**: Ensures errors don't leak sensitive information

## Contributing

When contributing new tests:

1. Follow the existing test structure and naming conventions
2. Add appropriate pytest markers
3. Include both positive and negative test cases
4. Update this documentation
5. Ensure tests are deterministic and don't depend on external resources
