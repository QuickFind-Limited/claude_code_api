#!/bin/sh
set -e

echo "Configuring MCP servers..."

# Copy MCP configuration into ~/.claude/config.json for the app user
if [ -f "/app/claude-config.json" ]; then
    mkdir -p /home/app/.claude/
    cp /app/claude-config.json /home/app/.claude/config.json
    echo "MCP configuration copied"
fi

# Copy agent definition markdown files into ~/.claude/agents
if [ -d "/app/claude_agents" ]; then
    mkdir -p /home/app/.claude/agents/
    if find /app/claude_agents -maxdepth 1 -type f -name '*.md' | grep -q '.'; then
        find /app/claude_agents -maxdepth 1 -type f -name '*.md' -exec cp {} /home/app/.claude/agents/ \;
        echo "Agents copied"
    else
        echo "No agent markdown files found in /app/claude_agents"
    fi
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
