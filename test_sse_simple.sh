#!/bin/bash

echo "Testing SSE stream with curl..."
echo "================================"

curl -N -X POST http://localhost:8000/api/v1/query/stream \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{
    "prompt": "Count to 3 slowly",
    "model": "claude-sonnet-4-20250514"
  }' 2>/dev/null | while IFS= read -r line; do
    if [[ $line == event:* ]]; then
        echo -e "\033[32m$line\033[0m"
    elif [[ $line == data:* ]]; then
        echo -e "\033[33m$line\033[0m"
    elif [[ $line == :* ]]; then
        echo -e "\033[90m$line\033[0m"
    else
        echo "$line"
    fi
done