#!/bin/sh
set -e

echo "Configuring MCP servers..."

# Simply copy the claude configuration to the home directory
if [ -f "/app/claude-config.json" ]; then
    cp /app/claude-config.json /home/app/.claude.json
    echo "MCP configuration copied"
fi

# Include all the files of agents from claude_agents folder without the folder itself in the .claude/agents directory
if [ -d "/app/claude_agents" ]; then
    mkdir -p /home/app/.claude/agents/
    cp -r /app/claude_agents/* /home/app/.claude/agents/
    echo "Agents copied"
fi

# Echo the content of the .claude/agents directory
echo "Content of the .claude/agents directory:"
ls -la /home/app/.claude/agents/

# List MCP servers to verify and count them
echo "Checking MCP servers..."
MCP_OUTPUT=$(claude mcp list)
echo "$MCP_OUTPUT"

# Count the number of connected MCP servers (lines with checkmark)
MCP_COUNT=$(echo "$MCP_OUTPUT" | grep -c "✓ Connected" || echo "0")
MCP_COUNT_FAILED=$(echo "$MCP_OUTPUT" | grep -c "Failed" || echo "0")

echo "$MCP_COUNT MCP server(s) connected"
echo "$MCP_COUNT_FAILED MCP server(s) failed"

# Execute the main command
exec "$@"
