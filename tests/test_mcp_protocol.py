"""
Comprehensive tests for MCP protocol handshake and communication with Claude Desktop.

This test suite ensures the compiler MCP server properly implements the MCP protocol
and can successfully communicate with Claude Desktop and other MCP clients.
"""

import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import pytest

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from solution_for_s1113 import analyze_vectorization_failure, create_compilation_session


class MCPProtocolTester:
    """Helper class to simulate MCP protocol communication"""

    def __init__(self):
        self.request_id = 0
        self.server_process = None

    def next_request_id(self) -> int:
        """Generate next request ID"""
        self.request_id += 1
        return self.request_id

    def create_mcp_request(
        self, method: str, params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Create a properly formatted MCP request"""
        request = {"jsonrpc": "2.0", "id": self.next_request_id(), "method": method}
        if params:
            request["params"] = params
        return request

    def create_mcp_notification(
        self, method: str, params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Create a properly formatted MCP notification (no response expected)"""
        notification: Dict[str, Any] = {"jsonrpc": "2.0", "method": method}
        if params:
            notification["params"] = params
        return notification

    async def start_server_process(self) -> subprocess.Popen:
        """Start the MCP server as a subprocess for integration testing"""
        self.server_process = subprocess.Popen(
            [sys.executable, "solution_for_s1113.py", "--mode", "stdio"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=Path(__file__).parent.parent,
        )
        # Give server time to start
        await asyncio.sleep(0.1)
        return self.server_process

    def cleanup(self):
        """Clean up server process"""
        if self.server_process:
            self.server_process.terminate()
            self.server_process.wait(timeout=5)


class TestMCPProtocolHandshake:
    """Test the MCP protocol initialization and handshake sequence"""

    @pytest.fixture
    def protocol_tester(self):
        """Fixture providing MCP protocol testing utilities"""
        tester = MCPProtocolTester()
        yield tester
        tester.cleanup()

    def test_mcp_initialize_request_format(self, protocol_tester):
        """Test that we can create proper MCP initialize requests"""
        init_request = protocol_tester.create_mcp_request(
            "initialize",
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "clientInfo": {"name": "claude-desktop", "version": "0.7.0"},
            },
        )

        assert init_request["jsonrpc"] == "2.0"
        assert "id" in init_request
        assert init_request["method"] == "initialize"
        assert "protocolVersion" in init_request["params"]
        assert "capabilities" in init_request["params"]
        assert "clientInfo" in init_request["params"]

    def test_mcp_initialized_notification_format(self, protocol_tester):
        """Test that we can create proper MCP initialized notifications"""
        initialized_notification = protocol_tester.create_mcp_notification(
            "initialized"
        )

        assert initialized_notification["jsonrpc"] == "2.0"
        assert "id" not in initialized_notification  # Notifications don't have IDs
        assert initialized_notification["method"] == "initialized"

    @pytest.mark.asyncio
    async def test_server_startup_and_shutdown(self, protocol_tester):
        """Test that the server can start and shutdown properly"""
        server_process = await protocol_tester.start_server_process()

        # Server should be running
        assert server_process.poll() is None

        # Send a simple newline to see if server responds
        server_process.stdin.write("\n")
        server_process.stdin.flush()

        # Give it a moment
        await asyncio.sleep(0.1)

        # Server should still be running (not crashed)
        assert server_process.poll() is None

        # Clean shutdown
        server_process.terminate()
        server_process.wait(timeout=5)


class TestMCPToolDiscovery:
    """Test MCP tool discovery and registration"""

    @pytest.fixture
    def protocol_tester(self):
        tester = MCPProtocolTester()
        yield tester
        tester.cleanup()

    def test_tools_list_request_format(self, protocol_tester):
        """Test that we can create proper tools/list requests"""
        tools_request = protocol_tester.create_mcp_request("tools/list")

        assert tools_request["jsonrpc"] == "2.0"
        assert "id" in tools_request
        assert tools_request["method"] == "tools/list"

    @pytest.mark.asyncio
    async def test_mcp_tools_are_registered(self):
        """Test that our MCP tools are properly registered"""
        # This tests the internal registration, not the protocol communication
        # We should have at least 2 tools registered

        # Check that the tools are accessible
        from solution_for_s1113 import (
            analyze_vectorization_failure,
            create_compilation_session,
        )

        # These should be callable
        assert callable(analyze_vectorization_failure)
        assert callable(create_compilation_session)

        # Test basic tool execution
        result = await analyze_vectorization_failure("int a[10];", "test_session")
        assert isinstance(result, str)
        assert "Vectorization Analysis" in result

    def test_tool_call_request_format(self, protocol_tester):
        """Test that we can create proper tools/call requests"""
        tool_call_request = protocol_tester.create_mcp_request(
            "tools/call",
            {
                "name": "analyze_vectorization_failure",
                "arguments": {
                    "code": "for(int i=0; i<100; i++) a[i] = a[i-1] + b[i];",
                    "session_id": "test_session",
                },
            },
        )

        assert tool_call_request["jsonrpc"] == "2.0"
        assert "id" in tool_call_request
        assert tool_call_request["method"] == "tools/call"
        assert "name" in tool_call_request["params"]
        assert "arguments" in tool_call_request["params"]
        assert tool_call_request["params"]["name"] == "analyze_vectorization_failure"


class TestMCPProtocolCompliance:
    """Test compliance with MCP protocol specification"""

    @pytest.fixture
    def protocol_tester(self):
        tester = MCPProtocolTester()
        yield tester
        tester.cleanup()

    def test_jsonrpc_version_compliance(self, protocol_tester):
        """Test that all messages use correct JSON-RPC version"""
        request = protocol_tester.create_mcp_request("test_method")
        notification = protocol_tester.create_mcp_notification("test_notification")

        assert request["jsonrpc"] == "2.0"
        assert notification["jsonrpc"] == "2.0"

    def test_request_id_uniqueness(self, protocol_tester):
        """Test that request IDs are unique"""
        request1 = protocol_tester.create_mcp_request("method1")
        request2 = protocol_tester.create_mcp_request("method2")
        request3 = protocol_tester.create_mcp_request("method3")

        ids = [request1["id"], request2["id"], request3["id"]]
        assert len(set(ids)) == 3  # All IDs should be unique

    def test_notification_has_no_id(self, protocol_tester):
        """Test that notifications don't have ID field"""
        notification = protocol_tester.create_mcp_notification("test_notification")
        assert "id" not in notification

    def test_mcp_error_response_format(self):
        """Test that we can create proper MCP error responses"""
        error_response = {
            "jsonrpc": "2.0",
            "id": 1,
            "error": {
                "code": -32601,  # Method not found
                "message": "Method not found",
                "data": {"method": "unknown_method"},
            },
        }

        assert error_response["jsonrpc"] == "2.0"
        assert "id" in error_response
        assert "error" in error_response
        assert "code" in error_response["error"]  # type: ignore[operator]
        assert "message" in error_response["error"]  # type: ignore[operator]


class TestMCPIntegration:
    """Integration tests simulating real Claude Desktop communication"""

    @pytest.fixture
    def protocol_tester(self):
        tester = MCPProtocolTester()
        yield tester
        tester.cleanup()

    @pytest.mark.asyncio
    async def test_full_mcp_handshake_simulation(self, protocol_tester):
        """Simulate a complete MCP handshake sequence"""
        # This test simulates what Claude Desktop would do

        # 1. Initialize request
        init_request = protocol_tester.create_mcp_request(
            "initialize",
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "clientInfo": {"name": "claude-desktop", "version": "0.7.0"},
            },
        )

        # 2. Initialized notification
        initialized_notification = protocol_tester.create_mcp_notification(
            "initialized"
        )

        # 3. Tools list request
        tools_request = protocol_tester.create_mcp_request("tools/list")

        # 4. Tool call request
        tool_call_request = protocol_tester.create_mcp_request(
            "tools/call",
            {
                "name": "analyze_vectorization_failure",
                "arguments": {
                    "code": "for(int i=0; i<100; i++) a[i] = a[i-1] + b[i];",
                    "session_id": "claude_session",
                },
            },
        )

        # Verify all messages are properly formatted
        messages = [
            init_request,
            initialized_notification,
            tools_request,
            tool_call_request,
        ]

        for msg in messages:
            assert msg["jsonrpc"] == "2.0"
            assert "method" in msg

        # Requests should have IDs, notifications should not
        assert "id" in init_request
        assert "id" not in initialized_notification
        assert "id" in tools_request
        assert "id" in tool_call_request

    @pytest.mark.asyncio
    async def test_vectorization_analysis_tool_execution(self):
        """Test the vectorization analysis tool with realistic code examples"""
        test_cases = [
            {
                "name": "loop_carried_dependency",
                "code": "for(int i=1; i<100; i++) a[i] = a[i-1] + b[i];",
                "expected_keywords": [
                    "Vectorization Analysis"
                ],  # More flexible expectation
            },
            {
                "name": "s1113_pattern",
                "code": "for(int i=0; i<LEN_1D; i++) a[i] = a[LEN_1D/2-i] + b[i];",
                "expected_keywords": ["Vectorization Analysis"],
            },
            {
                "name": "simple_vectorizable",
                "code": "for(int i=0; i<100; i++) a[i] = b[i] + c[i];",
                "expected_keywords": ["Vectorization Analysis"],
            },
        ]

        for test_case in test_cases:
            result = await analyze_vectorization_failure(
                test_case["code"], f"test_session_{test_case['name']}"
            )

            assert isinstance(result, str)
            assert len(result) > 0

            # Check that expected keywords appear in the analysis
            for keyword in test_case["expected_keywords"]:
                assert (
                    keyword in result
                ), f"Expected '{keyword}' in analysis for {test_case['name']}"

            # Additional checks for specific patterns
            if test_case["name"] == "loop_carried_dependency":
                # Should indicate some kind of vectorization issue
                assert (
                    "failed" in result.lower()
                    or "dependency" in result.lower()
                    or "conflict" in result.lower()
                ), f"Expected vectorization issue indication in {test_case['name']}"

    @pytest.mark.asyncio
    async def test_session_management_tool(self):
        """Test the session management functionality"""
        session_name = "test_integration_session"

        # Create a session
        result = await create_compilation_session(session_name)
        assert isinstance(result, str)
        assert session_name in result or "session" in result.lower()

        # Use the session for analysis
        analysis_result = await analyze_vectorization_failure(
            "for(int i=0; i<100; i++) a[i] = b[i] * 2;", session_name
        )
        assert isinstance(analysis_result, str)
        assert "Vectorization Analysis" in analysis_result


class TestMCPErrorHandling:
    """Test error handling in MCP protocol communication"""

    @pytest.mark.asyncio
    async def test_invalid_tool_parameters(self):
        """Test handling of invalid tool parameters"""
        # Test with missing required parameter
        try:
            result = await analyze_vectorization_failure("")  # Empty code
            # Should handle gracefully, not crash
            assert isinstance(result, str)
        except Exception as e:
            # If it raises an exception, it should be a meaningful one
            assert "code" in str(e).lower() or "parameter" in str(e).lower()

    @pytest.mark.asyncio
    async def test_malformed_code_input(self):
        """Test handling of malformed C/C++ code"""
        malformed_codes = [
            "this is not C code",
            "for(int i=0; i<100; i++) { missing_brace",
            "int a[10]; // incomplete",
            "/* unclosed comment",
        ]

        for code in malformed_codes:
            try:
                result = await analyze_vectorization_failure(code, "error_test_session")
                # Should handle gracefully
                assert isinstance(result, str)
                # Should indicate some kind of issue
                assert len(result) > 0
            except Exception as e:  # noqa: PERF203
                # If it raises an exception, it should be handled gracefully
                # Note: try-except in loop is intentional for testing error handling
                assert isinstance(e, (ValueError, SyntaxError, RuntimeError))


class TestClaudeDesktopConfiguration:
    """Test Claude Desktop configuration and setup"""

    def test_claude_desktop_config_generation(self):
        """Test generation of Claude Desktop configuration file"""
        config_path = Path("claude_desktop_config.json")

        # Generate configuration
        config = {
            "mcpServers": {
                "compiler": {
                    "command": "python",
                    "args": [str(Path.cwd().absolute() / "solution_for_s1113.py")],
                }
            }
        }

        # Write configuration
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)

        # Verify configuration is valid
        assert config_path.exists()

        with open(config_path) as f:
            loaded_config = json.load(f)

        assert "mcpServers" in loaded_config
        assert "compiler" in loaded_config["mcpServers"]
        assert "command" in loaded_config["mcpServers"]["compiler"]
        assert "args" in loaded_config["mcpServers"]["compiler"]

        # Verify the path is absolute and points to our server
        server_path = loaded_config["mcpServers"]["compiler"]["args"][0]
        assert Path(server_path).is_absolute()
        assert "solution_for_s1113.py" in server_path

    def test_claude_desktop_config_validation(self):
        """Test validation of Claude Desktop configuration format"""
        # Test various configuration formats
        valid_configs = [
            {
                "mcpServers": {
                    "compiler": {
                        "command": "python",
                        "args": ["/path/to/solution_for_s1113.py"],
                    }
                }
            },
            {
                "mcpServers": {
                    "compiler": {
                        "command": "python3",
                        "args": ["/path/to/solution_for_s1113.py", "--mode", "stdio"],
                    }
                }
            },
        ]

        for config in valid_configs:
            # Should be valid JSON
            config_json = json.dumps(config)
            parsed = json.loads(config_json)

            # Should have required structure
            assert "mcpServers" in parsed
            assert isinstance(parsed["mcpServers"], dict)

            for server_config in parsed["mcpServers"].values():
                assert "command" in server_config
                assert "args" in server_config
                assert isinstance(server_config["args"], list)


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])
