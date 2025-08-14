#!/bin/sh
set -e

# Install odoo_mcp dependencies if needed
if [ -d "/opt/odoo_mcp" ]; then
    echo "Installing odoo_mcp dependencies..."
    cd /opt/odoo_mcp
    # Remove old venv if it exists
    rm -rf .venv
    # Install dependencies
    uv sync || echo "Warning: Could not install odoo_mcp dependencies"
    cd /app
fi

# Configure Claude MCP servers
echo "Configuring Claude MCP servers..."
claude mcp add-json odoo_mcp '{
  "command": "uv",
  "args": [
    "--project",
    "/opt/odoo_mcp/",
    "run",
    "odoo-mcp-server"
  ],
  "env": {
    "ODOO_URL": "'"$ODOO_URL"'",
    "ODOO_DB": "'"$ODOO_DB"'",
    "ODOO_USERNAME": "'"$ODOO_USERNAME"'",
    "ODOO_API_KEY": "'"$ODOO_API_KEY"'"
  }
}' || echo "MCP server already configured"

# List MCP servers to verify
echo "Checking MCP servers..."
claude mcp list

# Execute the main command
exec "$@"