#!/bin/bash

# Build Docker image with embedded odoo_mcp

echo "Preparing build context..."

# Create a temporary directory for the build context
BUILD_DIR=$(mktemp -d)
trap "rm -rf $BUILD_DIR" EXIT

# Copy the current project files
cp -r . "$BUILD_DIR/"

# Copy odoo_mcp from the parent directory
if [ -d "../odoo_mcp" ]; then
    echo "Copying odoo_mcp from ../odoo_mcp..."
    cp -r ../odoo_mcp "$BUILD_DIR/odoo_mcp"
else
    echo "Error: odoo_mcp directory not found at ../odoo_mcp"
    exit 1
fi

# Build the Docker image
echo "Building Docker image..."
cd "$BUILD_DIR"
docker build -t claude-sdk-server:latest .

echo "Build complete!"
echo "Run with: docker compose up -d"