# Claude SDK Server 🚀

A production-ready FastAPI server providing REST API interface to Claude Code SDK with **real-time event streaming**, **beautiful logging**, and **comprehensive monitoring**.

## ✨ Features

### Core Functionality
- ✅ **Claude Query API** - Simple `/query` endpoint for Claude interactions
- ✅ **Session Management** - Conversation continuity with session IDs
- ✅ **Health Monitoring** - Health check endpoints
- ✅ **Docker Support** - Production-ready containerization

### 🆕 New Features (v2.0)
- 🎯 **Beautiful Logging with Loguru** - Clean, structured logs with emojis
- 📡 **Real-time Event Streaming** - SSE, WebSocket, and JSON Lines support
- 📊 **Event Queue System** - Buffered event delivery for multiple clients
- 🤔 **Thinking/Reasoning Extraction** - Capture Claude's thought process
- 🛠️ **Tool Usage Tracking** - Monitor tool calls and results
- 📈 **Performance Metrics** - Token usage, costs, and timing data

## 🚀 Quick Start

```bash
# Start the server
make up

# Test the API
make test

# Watch beautiful logs
make logs-pretty

# Test streaming
make test-stream
```

## 📦 Installation

### Using Docker (Recommended)

```bash
# Using Make commands (easiest)
make up      # Build and start server
make down    # Stop server
make logs    # View logs
make restart # Restart server
```

### Manual Docker Setup

```bash
# Build the Docker image
docker build -t claude-sdk-server:latest .

# Run with Docker Compose
docker-compose up -d

# Or run directly with Docker
docker run -d \
  --name claude-sdk-server \
  -p 8000:8000 \
  -e ANTHROPIC_API_KEY=your_api_key \
  -e ATLA_INSIGHTS_API_KEY=your_atla_key \
  -e ATLA_ENVIRONMENT=development \
  claude-sdk-server:latest
```

## 🎮 Makefile Commands

### Basic Commands
```bash
make up          # Build and start the server
make down        # Stop the server
make restart     # Restart the server
make logs        # View server logs
make clean       # Clean up everything
```

### Testing Commands
```bash
make test        # Test basic API endpoints
make test-stream # Test all streaming endpoints
make test-sse    # Test Server-Sent Events
make test-ws     # Test WebSocket info
make test-events # Test event system
make test-thinking # Test with thinking mode enabled
```

### API Commands
```bash
make query       # Send a test query to Claude
make stream-status   # Check streaming system status
make stream-clients  # List active streaming clients
```

### Development Commands
```bash
make logs-pretty    # Watch logs with beautiful formatting
make demo-stream    # Run streaming demo with live query
make monitor-events # Monitor events in real-time
```

## 📡 API Endpoints

### Core Endpoints

#### Query Claude
```bash
POST /api/v1/query
Content-Type: application/json

{
  "prompt": "Your question here",
  "session_id": "optional-session-id",
  "max_turns": 30,
  "model": "claude-3-5-sonnet-20241022",
  "max_thinking_tokens": 8000
}

Response:
{
  "response": "Claude's response",
  "session_id": "session-id-for-continuity"
}
```

#### Health Check
```bash
GET /api/v1/health

Response:
{
  "status": "healthy",
  "service": "Claude SDK Server",
  "timestamp": "2024-01-19T10:00:00Z"
}
```

### 🆕 Streaming Endpoints

#### Server-Sent Events (SSE)
Perfect for web browsers with automatic reconnection support.

```javascript
// Browser Example
const eventSource = new EventSource('/api/v1/stream/sse?include_performance=true');

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Event:', data.type, data.message);
};

// Event types you'll receive:
// - query_start: Query processing started
// - session_init: Claude session initialized
// - thinking_start: Claude is reasoning
// - thinking_insight: TODOs and insights extracted
// - tool_use: Tool being called
// - tool_result: Tool execution result
// - query_complete: Query finished
```

Query Parameters:
- `event_types`: Comma-separated list of event types to filter
- `session_id`: Filter by specific session
- `include_performance`: Include performance metrics (default: false)
- `include_system`: Include system events (default: true)

#### WebSocket
For bidirectional communication and real-time updates.

```javascript
// JavaScript Example
const ws = new WebSocket('ws://localhost:8000/api/v1/stream/ws');

ws.onopen = () => {
  console.log('Connected to stream');
  
  // Subscribe to specific events
  ws.send(JSON.stringify({
    action: 'subscribe',
    event_types: ['query_start', 'tool_use', 'query_complete']
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Event received:', data);
};

// Send commands
ws.send(JSON.stringify({ action: 'ping' }));
ws.send(JSON.stringify({ action: 'get_recent', count: 10 }));
```

Using wscat CLI:
```bash
npm install -g wscat
wscat -c ws://localhost:8000/api/v1/stream/ws
```

#### JSON Lines Stream
For programmatic consumption and log processing.

```bash
# Stream events as JSON Lines
curl -N http://localhost:8000/api/v1/stream/jsonl

# With filters
curl -N "http://localhost:8000/api/v1/stream/jsonl?session_id=abc123&event_types=tool_use,tool_result"

# Process with jq
curl -N http://localhost:8000/api/v1/stream/jsonl | while read line; do
  echo "$line" | jq '.type, .message'
done
```

#### Stream Status
```bash
GET /api/v1/stream/status

Response:
{
  "active_connections": 3,
  "events_queued": 42,
  "total_events_sent": 1337,
  "uptime_seconds": 3600.5
}
```

#### Recent Events
```bash
GET /api/v1/stream/events/recent?count=10&event_types=tool_use,tool_result

Response: Array of recent events
```

#### Active Clients
```bash
GET /api/v1/stream/clients

Response:
{
  "active_clients": 2,
  "websocket_connections": 1,
  "clients": [...]
}
```

## 🎨 Beautiful Logging Examples

The new loguru-based logging system provides clean, structured output:

```
🚀 Starting: Processing your request with claude-3-5-sonnet
   └─ Input: 12 words, 89 characters
   └─ Mode: Deep thinking enabled (8,000 tokens)

🔧 Setup: Claude session initialized
   └─ Tools: 19 tools available
   └─ MCP: 1 servers: useless-hornet

🤔 Thinking: Analyzing your request...
📝 TODO: 1. Analyze the user's code structure
📝 TODO: 2. Identify refactoring opportunities
💡 Insight: The code follows clean architecture

🛠️ Tool: Read
   └─ Input: File: /src/main.py
   └─ Result: ✅ Output: 45 lines, 230 words

✅ Complete: Query processed in 2.35s
   └─ TODOs: Identified 4 action items
   └─ Tools: Used 3 tools: Read, Bash, Edit
   └─ Response: Generated 180 words
```

## 📊 Event Types

The streaming system emits these event types:

| Event Type | Description | Key Data |
|------------|-------------|----------|
| `query_start` | Query processing begins | prompt_length, model, thinking_tokens |
| `session_init` | Claude session initialized | tools_available, mcp_servers |
| `thinking_start` | Reasoning begins | signature |
| `thinking_insight` | TODO/insight extracted | content, priority |
| `tool_use` | Tool being called | tool_name, input_summary |
| `tool_result` | Tool execution result | success, result_summary |
| `tool_error` | Tool failed | error_message |
| `todo_identified` | TODO item found | todo_content, priority |
| `decision_made` | Key decision made | decision_content |
| `performance_metric` | Performance data | operation, duration |
| `token_usage` | Token consumption | input_tokens, output_tokens, cost_usd |
| `query_complete` | Query finished | duration_seconds, response_length |
| `query_error` | Query failed | error_type, error_details |

## 🔧 Environment Variables

```bash
# Required
ANTHROPIC_API_KEY=sk-ant-...        # Your Anthropic API key

# Optional Monitoring
ATLA_INSIGHTS_API_KEY=...           # Atla Insights monitoring
ATLA_ENVIRONMENT=development        # Environment name
LOGFIRE_API_KEY=...                 # Logfire monitoring (optional)

# Logging
LOG_LEVEL=INFO                      # Log level (DEBUG, INFO, WARNING, ERROR)
```

## 📈 Monitoring & Observability

### Real-time Event Monitoring
```bash
# Monitor events in real-time
make monitor-events

# Watch beautiful logs
make logs-pretty

# Check streaming status
make stream-status
```

### Integration Examples

#### React Component
```jsx
import { useEffect, useState } from 'react';

function ClaudeStream() {
  const [events, setEvents] = useState([]);
  
  useEffect(() => {
    const eventSource = new EventSource('/api/v1/stream/sse');
    
    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setEvents(prev => [...prev, data]);
      
      // Handle specific event types
      switch(data.type) {
        case 'thinking_insight':
          console.log('Claude is thinking:', data.content);
          break;
        case 'tool_use':
          console.log('Using tool:', data.tool_name);
          break;
        case 'query_complete':
          console.log('Query completed in', data.duration_seconds, 's');
          break;
      }
    };
    
    return () => eventSource.close();
  }, []);
  
  return (
    <div>
      {events.map(event => (
        <div key={event.id}>
          {event.type}: {event.message}
        </div>
      ))}
    </div>
  );
}
```

#### Python Client
```python
import json
import requests
import sseclient

# Query with streaming
def query_with_stream(prompt):
    # Start SSE connection
    stream_url = "http://localhost:8000/api/v1/stream/sse"
    stream = requests.get(stream_url, stream=True)
    client = sseclient.SSEClient(stream)
    
    # Send query
    query_response = requests.post(
        "http://localhost:8000/api/v1/query",
        json={"prompt": prompt}
    )
    
    # Process events
    for event in client.events():
        data = json.loads(event.data)
        print(f"{data['type']}: {data['message']}")
        
        if data['type'] == 'query_complete':
            break
    
    return query_response.json()
```

## 🚧 Development

### Project Structure
```
claude_sdk_server/
├── src/
│   └── claude_sdk_server/
│       ├── api/
│       │   └── routers/
│       │       ├── claude_router.py      # Main API endpoints
│       │       └── streaming_router.py   # Streaming endpoints
│       ├── models/
│       │   ├── dto.py                   # Request/Response models
│       │   └── events.py                # Event models
│       ├── services/
│       │   └── claude_service.py        # Claude interaction logic
│       ├── streaming/
│       │   └── event_stream.py          # Event streaming engine
│       └── utils/
│           └── logging_config.py        # Loguru configuration
├── tests/                               # Test files
├── Makefile                            # All commands
├── docker-compose.yml                  # Docker configuration
└── README.md                           # This file
```

### Running Tests
```bash
# Test everything
make test
make test-stream

# Specific tests
make test-sse
make test-events
make test-thinking

# Live demo
make demo-stream
```

### Debugging
```bash
# View logs
make logs

# Pretty logs (filtered)
make logs-pretty

# Monitor events
make monitor-events

# Check status
make stream-status
make stream-clients
```

## 📝 License

MIT License - See LICENSE file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 🐛 Troubleshooting

### Port 8000 Already in Use
```bash
# Find and stop the process using port 8000
lsof -i :8000
kill -9 <PID>

# Or stop Docker container
docker stop claude-sdk-server
```

### No Events Appearing
1. Check server is running: `make stream-status`
2. Verify Claude API key is set correctly
3. Check logs for errors: `make logs`

### WebSocket Connection Failed
1. Ensure server is running: `curl http://localhost:8000/api/v1/health`
2. Check firewall/proxy settings
3. Try SSE or JSON Lines as alternatives

## 📚 Additional Resources

- [Claude Code SDK Documentation](https://github.com/anthropics/claude-code-sdk)
- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [Server-Sent Events Spec](https://html.spec.whatwg.org/multipage/server-sent-events.html)
- [WebSocket Protocol](https://datatracker.ietf.org/doc/html/rfc6455)

---

Built with ❤️ using Claude Code SDK, FastAPI, and Loguru