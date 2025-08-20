#!/bin/bash
# Start the frontend dashboard

cd "$(dirname "$0")/frontend"
echo "Starting Claude SDK Server Frontend Dashboard..."
echo "Access the dashboard at: http://localhost:3000"
echo "Make sure the API server is running with: make up"
echo ""
python3 serve.py