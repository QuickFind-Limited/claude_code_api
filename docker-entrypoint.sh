#!/bin/sh
set -e

# Create MCP configuration directory
mkdir -p /root/.config/claude

# Create MCP configuration with odoo_mcp using environment variables directly
cat > /root/.config/claude/mcp_servers.json << EOF
{
  "mcpServers": {
    "odoo_mcp": {
      "command": "uv",
      "args": [
        "--project",
        "/opt/odoo_mcp/",
        "run",
        "odoo-mcp-server"
      ],
      "env": {
        "ODOO_URL": "$ODOO_URL",
        "ODOO_DB": "$ODOO_DB",
        "ODOO_USERNAME": "$ODOO_USERNAME",
        "ODOO_API_KEY": "$ODOO_API_KEY"
      }
    }
  }
}
EOF

echo "MCP configuration created with odoo_mcp server"

# Execute the main command
exec "$@"