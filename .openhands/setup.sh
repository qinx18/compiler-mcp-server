#!/bin/bash
# OpenHands setup script for compiler-mcp-server

echo "Setting up Compiler MCP Server environment..."

# Install Python dependencies
pip install -r requirements.txt

# Install system dependencies if needed
if ! command -v gcc &> /dev/null; then
    echo "GCC not found. Please install GCC for full functionality."
fi

# Create test directory if it doesn't exist
mkdir -p test_output

echo "Setup complete!"
