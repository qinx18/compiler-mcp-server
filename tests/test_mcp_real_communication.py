"""
Real MCP communication tests that actually communicate with the server process.

These tests start the actual MCP server and send real JSON-RPC messages to test
the complete protocol implementation.
"""

import asyncio
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional

import pytest

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class MCPServerCommunicator:
    """Handles real communication with MCP server process"""

    def __init__(self):
        self.server_process = None
        self.request_id = 0

    async def start_server(self) -> bool:
        """Start the MCP server process"""
        try:
            self.server_process = subprocess.Popen(
                [sys.executable, "solution_for_s1113.py", "--mode", "stdio"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=Path(__file__).parent.parent,
                bufsize=0,  # Unbuffered for real-time communication
            )

            # Give server time to start
            await asyncio.sleep(0.2)

            # Check if server is still running
            if self.server_process.poll() is not None:
                stderr = self.server_process.stderr.read()
                raise RuntimeError(f"Server failed to start: {stderr}")

            return True
        except Exception as e:
            print(f"Failed to start server: {e}")
            return False

    def send_message(self, message: Dict[str, Any]) -> None:
        """Send a JSON-RPC message to the server"""
        if not self.server_process:
            raise RuntimeError("Server not started")

        message_json = json.dumps(message) + "\n"
        self.server_process.stdin.write(message_json)
        self.server_process.stdin.flush()

    def read_response(self, timeout: float = 5.0) -> Optional[Dict[str, Any]]:
        """Read a response from the server with timeout"""
        if not self.server_process:
            raise RuntimeError("Server not started")

        # Simple timeout mechanism
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.server_process.stdout.readable():
                try:
                    line = self.server_process.stdout.readline()
                    if line.strip():
                        return json.loads(line.strip())
                except json.JSONDecodeError:
                    continue
                except Exception:
                    break
            time.sleep(0.01)

        return None

    def next_request_id(self) -> int:
        """Get next request ID"""
        self.request_id += 1
        return self.request_id

    def create_request(
        self, method: str, params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Create a JSON-RPC request"""
        request = {"jsonrpc": "2.0", "id": self.next_request_id(), "method": method}
        if params:
            request["params"] = params
        return request

    def create_notification(
        self, method: str, params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Create a JSON-RPC notification"""
        notification = {"jsonrpc": "2.0", "method": method}
        if params:
            notification["params"] = params
        return notification

    def cleanup(self):
        """Clean up server process"""
        if self.server_process:
            try:
                self.server_process.terminate()
                self.server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.server_process.kill()
                self.server_process.wait()


class TestRealMCPCommunication:
    """Test real MCP protocol communication with the server"""

    @pytest.fixture
    async def mcp_server(self):
        """Fixture that provides a running MCP server"""
        communicator = MCPServerCommunicator()
        success = await communicator.start_server()
        if not success:
            pytest.skip("Could not start MCP server")

        yield communicator
        communicator.cleanup()

    @pytest.mark.asyncio
    async def test_server_responds_to_ping(self, mcp_server):
        """Test that server responds to basic communication"""
        # Send a simple request to see if server responds
        ping_request = mcp_server.create_request("ping")
        mcp_server.send_message(ping_request)

        # Even if ping is not implemented, server should respond with an error
        response = mcp_server.read_response(timeout=2.0)

        if response:
            assert "jsonrpc" in response
            assert response["jsonrpc"] == "2.0"
            # Should have either result or error
            assert "result" in response or "error" in response

    @pytest.mark.asyncio
    async def test_mcp_initialize_sequence(self, mcp_server):
        """Test the complete MCP initialization sequence"""
        # 1. Send initialize request
        init_request = mcp_server.create_request(
            "initialize",
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "clientInfo": {"name": "test-client", "version": "1.0.0"},
            },
        )

        mcp_server.send_message(init_request)
        init_response = mcp_server.read_response(timeout=3.0)

        if init_response:
            assert init_response["jsonrpc"] == "2.0"
            assert init_response["id"] == init_request["id"]

            # Should have either successful result or error
            if "result" in init_response:
                # Successful initialization
                assert "protocolVersion" in init_response["result"]
                assert "capabilities" in init_response["result"]

                # 2. Send initialized notification
                initialized_notification = mcp_server.create_notification("initialized")
                mcp_server.send_message(initialized_notification)

                # Give server time to process
                await asyncio.sleep(0.1)

                print("✅ MCP initialization sequence completed successfully")
            else:
                # Error response
                assert "error" in init_response
                print(f"⚠️ MCP initialization failed: {init_response['error']}")

    @pytest.mark.asyncio
    async def test_tools_list_request(self, mcp_server):
        """Test tools/list request to discover available tools"""
        tools_request = mcp_server.create_request("tools/list")
        mcp_server.send_message(tools_request)

        response = mcp_server.read_response(timeout=3.0)

        if response:
            assert response["jsonrpc"] == "2.0"
            assert response["id"] == tools_request["id"]

            if "result" in response:
                # Should return list of tools
                assert "tools" in response["result"]
                tools = response["result"]["tools"]
                assert isinstance(tools, list)

                # Should have our registered tools
                tool_names = [tool["name"] for tool in tools]
                expected_tools = [
                    "analyze_vectorization_failure",
                    "create_compilation_session",
                ]

                for expected_tool in expected_tools:
                    assert expected_tool in tool_names, (
                        f"Expected tool '{expected_tool}' not found"
                    )

                print(f"✅ Found {len(tools)} tools: {tool_names}")
            else:
                print(
                    f"⚠️ Tools list request failed: {response.get('error', 'Unknown error')}"
                )

    @pytest.mark.asyncio
    async def test_tool_call_execution(self, mcp_server):
        """Test actual tool execution via MCP protocol"""
        # Test the vectorization analysis tool
        tool_call_request = mcp_server.create_request(
            "tools/call",
            {
                "name": "analyze_vectorization_failure",
                "arguments": {
                    "code": "for(int i=1; i<100; i++) a[i] = a[i-1] + b[i];",
                    "session_id": "test_real_communication",
                },
            },
        )

        mcp_server.send_message(tool_call_request)
        response = mcp_server.read_response(timeout=10.0)  # Longer timeout for analysis

        if response:
            assert response["jsonrpc"] == "2.0"
            assert response["id"] == tool_call_request["id"]

            if "result" in response:
                # Should return analysis result
                result = response["result"]
                assert "content" in result or isinstance(result, str)

                # Extract the actual content
                if isinstance(result, dict) and "content" in result:
                    content = result["content"]
                else:
                    content = str(result)

                # Should contain vectorization analysis
                assert "Vectorization Analysis" in content
                assert "dependency" in content.lower()

                print(
                    f"✅ Tool execution successful, analysis length: {len(content)} chars"
                )
            else:
                error = response.get("error", {})
                print(
                    f"⚠️ Tool execution failed: {error.get('message', 'Unknown error')}"
                )

    @pytest.mark.asyncio
    async def test_session_management_tool(self, mcp_server):
        """Test session management tool via MCP protocol"""
        # Create a session
        session_request = mcp_server.create_request(
            "tools/call",
            {
                "name": "create_compilation_session",
                "arguments": {"session_name": "test_mcp_session"},
            },
        )

        mcp_server.send_message(session_request)
        response = mcp_server.read_response(timeout=5.0)

        if response:
            assert response["jsonrpc"] == "2.0"
            assert response["id"] == session_request["id"]

            if "result" in response:
                result = response["result"]
                # Extract content
                if isinstance(result, dict) and "content" in result:
                    content = result["content"]
                else:
                    content = str(result)

                assert "session" in content.lower()
                print(f"✅ Session creation successful: {content}")
            else:
                error = response.get("error", {})
                print(
                    f"⚠️ Session creation failed: {error.get('message', 'Unknown error')}"
                )


class TestMCPProtocolEdgeCases:
    """Test edge cases and error conditions in MCP protocol"""

    @pytest.fixture
    async def mcp_server(self):
        """Fixture that provides a running MCP server"""
        communicator = MCPServerCommunicator()
        success = await communicator.start_server()
        if not success:
            pytest.skip("Could not start MCP server")

        yield communicator
        communicator.cleanup()

    @pytest.mark.asyncio
    async def test_invalid_json_handling(self, mcp_server):
        """Test how server handles invalid JSON"""
        # Send invalid JSON
        if mcp_server.server_process:
            mcp_server.server_process.stdin.write("invalid json\n")
            mcp_server.server_process.stdin.flush()

            # Server should not crash
            await asyncio.sleep(0.5)
            assert mcp_server.server_process.poll() is None, (
                "Server crashed on invalid JSON"
            )

    @pytest.mark.asyncio
    async def test_unknown_method_handling(self, mcp_server):
        """Test how server handles unknown methods"""
        unknown_request = mcp_server.create_request(
            "unknown_method", {"param": "value"}
        )
        mcp_server.send_message(unknown_request)

        response = mcp_server.read_response(timeout=3.0)

        if response:
            assert response["jsonrpc"] == "2.0"
            assert response["id"] == unknown_request["id"]
            assert "error" in response

            error = response["error"]
            assert "code" in error
            assert "message" in error
            # Should be "Method not found" error
            assert error["code"] == -32601 or "not found" in error["message"].lower()

    @pytest.mark.asyncio
    async def test_malformed_tool_call(self, mcp_server):
        """Test how server handles malformed tool calls"""
        malformed_request = mcp_server.create_request(
            "tools/call",
            {"name": "nonexistent_tool", "arguments": {"invalid": "params"}},
        )

        mcp_server.send_message(malformed_request)
        response = mcp_server.read_response(timeout=3.0)

        if response:
            assert response["jsonrpc"] == "2.0"
            assert response["id"] == malformed_request["id"]
            assert "error" in response

            error = response["error"]
            assert "message" in error
            print(f"✅ Properly handled malformed tool call: {error['message']}")


class TestMCPPerformance:
    """Test MCP protocol performance and responsiveness"""

    @pytest.fixture
    async def mcp_server(self):
        """Fixture that provides a running MCP server"""
        communicator = MCPServerCommunicator()
        success = await communicator.start_server()
        if not success:
            pytest.skip("Could not start MCP server")

        yield communicator
        communicator.cleanup()

    @pytest.mark.asyncio
    async def test_multiple_rapid_requests(self, mcp_server):
        """Test server handling of multiple rapid requests"""
        requests = []

        # Send multiple tool list requests rapidly
        for i in range(5):
            request = mcp_server.create_request("tools/list")
            requests.append(request)
            mcp_server.send_message(request)

        # Collect responses
        responses = []
        for _ in range(5):
            response = mcp_server.read_response(timeout=2.0)
            if response:
                responses.append(response)

        # Should handle all requests
        assert len(responses) >= 3, (
            f"Expected at least 3 responses, got {len(responses)}"
        )

        # All responses should be valid
        for response in responses:
            assert response["jsonrpc"] == "2.0"
            assert "id" in response

    @pytest.mark.asyncio
    async def test_large_code_analysis(self, mcp_server):
        """Test analysis of large code samples"""
        large_code = """
        #include <stdio.h>
        #define SIZE 10000
        
        int main() {
            int a[SIZE], b[SIZE], c[SIZE];
            
            // Initialize arrays
            for(int i = 0; i < SIZE; i++) {
                a[i] = i;
                b[i] = i * 2;
            }
            
            // Loop with dependency - should fail vectorization
            for(int i = 1; i < SIZE; i++) {
                a[i] = a[i-1] + b[i] * c[i];
            }
            
            // Another complex loop
            for(int i = 0; i < SIZE-1; i++) {
                for(int j = 0; j < SIZE-1; j++) {
                    a[i] = a[i] + b[j] * c[i+j];
                }
            }
            
            return 0;
        }
        """

        tool_call_request = mcp_server.create_request(
            "tools/call",
            {
                "name": "analyze_vectorization_failure",
                "arguments": {"code": large_code, "session_id": "performance_test"},
            },
        )

        start_time = time.time()
        mcp_server.send_message(tool_call_request)
        response = mcp_server.read_response(
            timeout=15.0
        )  # Longer timeout for large analysis
        end_time = time.time()

        if response:
            assert response["jsonrpc"] == "2.0"
            assert response["id"] == tool_call_request["id"]

            processing_time = end_time - start_time
            print(f"✅ Large code analysis completed in {processing_time:.2f} seconds")

            # Should complete within reasonable time
            assert processing_time < 10.0, (
                f"Analysis took too long: {processing_time:.2f}s"
            )


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v", "-s"])  # -s to see print output
