#!/bin/bash

echo "Testing SSE streaming with curl..."
echo "Starting at: $(date +%H:%M:%S.%3N)"
echo "---"

curl -N -X POST http://localhost:8000/api/v1/query/stream \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{
    "prompt": "Count to 3 slowly",
    "model": "claude-sonnet-4-20250514",
    "max_turns": 1
  }' 2>/dev/null | while IFS= read -r line; do
    echo "[$(date +%H:%M:%S.%3N)] $line"
done
