#!/bin/bash

# Test SSE streaming with default model
echo "Testing SSE Streaming with Default Model"
echo "=========================================="
echo ""

# Simple query without specifying model
PAYLOAD='{
  "prompt": "Write a haiku about coding"
}'

echo "Request payload (no model specified):"
echo "$PAYLOAD" | python3 -m json.tool
echo ""
echo "Streaming response:"
echo "------------------"

curl -N \
     -X POST \
     -H "Content-Type: application/json" \
     -H "Accept: text/event-stream" \
     -d "$PAYLOAD" \
     "http://localhost:8001/api/v1/query/stream" 2>/dev/null | while IFS= read -r line
do
    if [[ $line == "event:"* ]]; then
        EVENT_TYPE=${line#event: }
        printf "\n[%s] " "$EVENT_TYPE"
    elif [[ $line == "data:"* ]]; then
        DATA=${line#data: }
        echo "$DATA" | python3 -c "
import sys
import json
try:
    data = json.loads(sys.stdin.read())
    if 'display' in data:
        print(data['display'])
        if 'details' in data and data['details']:
            if isinstance(data['details'], dict):
                for k, v in data['details'].items():
                    if v:
                        print(f'  └─ {k}: {v}')
            else:
                print(f'  └─ {data[\"details\"]}')
    elif 'status' in data:
        print(f'Status: {data[\"status\"]}')
    elif 'response' in data:
        print(f'\\nFinal Response: {data[\"response\"]}')
    elif 'error' in data:
        print(f'ERROR: {data[\"error\"]}')
except:
    pass
" 2>/dev/null
    fi
done

echo ""
echo "=========================================="