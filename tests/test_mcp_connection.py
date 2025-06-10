import pytest
import json
import subprocess
import sys
import os
import asyncio
from pathlib import Path

# Add parent directory to path so we can import our server
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from solution_for_s1113 import CompilerMCPServer, analyze_vectorization_failure

class TestMCPConnection:
    """Test suite for MCP server connection and configuration"""
    
    def test_server_imports_correctly(self):
        """Test that all required modules import without errors"""
        try:
            from fastmcp import FastMCP
            from solution_for_s1113 import mcp
            assert mcp is not None
            assert hasattr(mcp, 'tool')
        except ImportError as e:
            pytest.fail(f"Failed to import required modules: {e}")
    
    def test_server_starts_without_error(self):
        """Test that the server can start in stdio mode"""
        # This test spawns the server as a subprocess and checks it starts
        process = subprocess.Popen(
            [sys.executable, "solution_for_s1113.py"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Give it a moment to start
        try:
            # Server should be waiting for input, not crashing
            process.wait(timeout=2)
            # If we get here, process ended (bad)
            stderr = process.stderr.read()
            pytest.fail(f"Server crashed on startup: {stderr}")
        except subprocess.TimeoutExpired:
            # Good! Server is still running
            process.terminate()
            assert True
    
    def test_claude_desktop_config_format(self):
        """Test that we can generate valid Claude Desktop configuration"""
        config = {
            "mcpServers": {
                "compiler": {
                    "command": "python",
                    "args": [str(Path.cwd() / "solution_for_s1113.py")]
                }
            }
        }
        
        # Verify it's valid JSON
        config_json = json.dumps(config, indent=2)
        parsed = json.loads(config_json)
        
        assert "mcpServers" in parsed
        assert "compiler" in parsed["mcpServers"]
        assert "command" in parsed["mcpServers"]["compiler"]
        assert parsed["mcpServers"]["compiler"]["command"] == "python"
    
    @pytest.mark.asyncio
    async def test_mcp_tool_registration(self):
        """Test that MCP tools are properly registered"""
        # Check that our tools are registered
        result = await analyze_vectorization_failure("int a[10];", "test_session")
        assert "Vectorization Analysis" in result
        assert isinstance(result, str)
    
    @pytest.mark.asyncio
    async def test_basic_vectorization_analysis(self):
        """Test that basic vectorization analysis works"""
        test_code = """
        for (int i = 0; i < 100; i++) {
            a[i] = a[i-1] + b[i];
        }
        """
        
        server = CompilerMCPServer()
        analysis = await server.analyze_vectorization(test_code)
        
        assert analysis is not None
        assert hasattr(analysis, 'status')
        assert hasattr(analysis, 'dependencies')
        assert len(analysis.dependencies) > 0  # Should detect dependency

class TestClaudeDesktopIntegration:
    """Test cases specifically for Claude Desktop integration"""
    
    def test_generate_claude_config_file(self):
        """Generate a claude_desktop_config.json file for testing"""
        config_path = Path("claude_desktop_config.json")
        
        config = {
            "mcpServers": {
                "compiler": {
                    "command": "python",
                    "args": [
                        str(Path.cwd().absolute() / "solution_for_s1113.py")
                    ]
                }
            }
        }
        
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        assert config_path.exists()
        print(f"\nClaude Desktop config generated at: {config_path}")
        print("Copy this to your Claude Desktop configuration directory")
    
    def test_server_handles_mcp_protocol(self):
        """Test that server properly handles MCP protocol initialization"""
        # This is a placeholder for more complex protocol testing
        # In a real scenario, we'd send actual MCP protocol messages
        assert True  # Placeholder for now