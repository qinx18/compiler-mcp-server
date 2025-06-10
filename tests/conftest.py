"""
Pytest configuration for MCP protocol tests.

This file contains shared fixtures and configuration for testing the
compiler MCP server's protocol implementation.
"""

import pytest
import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def sample_codes():
    """Provide sample C/C++ code snippets for testing"""
    return {
        "simple_vectorizable": """
            for(int i = 0; i < 100; i++) {
                a[i] = b[i] + c[i];
            }
        """,
        "loop_carried_dependency": """
            for(int i = 1; i < 100; i++) {
                a[i] = a[i-1] + b[i];
            }
        """,
        "s1113_pattern": """
            for(int i = 0; i < LEN_1D; i++) {
                a[i] = a[LEN_1D/2 - i] + b[i];
            }
        """,
        "complex_dependency": """
            for(int i = 2; i < 100; i++) {
                a[i] = a[i-1] + a[i-2] + b[i];
            }
        """,
        "nested_loops": """
            for(int i = 0; i < 100; i++) {
                for(int j = 0; j < 100; j++) {
                    a[i][j] = b[i][j] + c[i][j];
                }
            }
        """,
        "malformed_syntax": """
            for(int i = 0; i < 100; i++) {
                a[i] = b[i] +  // missing operand
            }
        """,
        "pointer_aliasing": """
            void func(int* a, int* b, int n) {
                for(int i = 0; i < n; i++) {
                    a[i] = b[i] + 1;  // a and b might alias
                }
            }
        """
    }


@pytest.fixture
def mcp_protocol_messages():
    """Provide sample MCP protocol messages for testing"""
    return {
        "initialize_request": {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "clientInfo": {
                    "name": "claude-desktop",
                    "version": "0.7.0"
                }
            }
        },
        "initialized_notification": {
            "jsonrpc": "2.0",
            "method": "initialized"
        },
        "tools_list_request": {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list"
        },
        "tool_call_request": {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "analyze_vectorization_failure",
                "arguments": {
                    "code": "for(int i=0; i<100; i++) a[i] = b[i] + c[i];",
                    "session_id": "test_session"
                }
            }
        }
    }


@pytest.fixture
def claude_desktop_config():
    """Provide Claude Desktop configuration for testing"""
    return {
        "mcpServers": {
            "compiler": {
                "command": "python",
                "args": [str(Path.cwd().absolute() / "solution_for_s1113.py")]
            }
        }
    }


# Pytest markers for different test categories
def pytest_configure(config):
    """Configure pytest markers"""
    config.addinivalue_line(
        "markers", "mcp_protocol: tests for MCP protocol implementation"
    )
    config.addinivalue_line(
        "markers", "integration: integration tests with real server communication"
    )
    config.addinivalue_line(
        "markers", "performance: performance and load tests"
    )
    config.addinivalue_line(
        "markers", "claude_desktop: tests specific to Claude Desktop integration"
    )


# Custom pytest collection hook to organize tests
def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test names"""
    for item in items:
        # Add markers based on test file names
        if "mcp_protocol" in item.nodeid:
            item.add_marker(pytest.mark.mcp_protocol)
        if "real_communication" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        if "performance" in item.name.lower():
            item.add_marker(pytest.mark.performance)
        if "claude" in item.name.lower():
            item.add_marker(pytest.mark.claude_desktop)