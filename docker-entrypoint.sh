#!/bin/sh
set -e

echo "Adding MCP servers..."
claude mcp add --scope user --transport http useless-hornet https://useless-hornet.fastmcp.app/mcp || echo "MCP server already configured"

# List MCP servers to verify
echo "Checking MCP servers..."
claude mcp list
echo "MCP servers added"

# Execute the main command
exec "$@"