# Claude SDK Server

A minimal FastAPI server providing a REST API interface to Claude Code SDK.

## Features

- ✅ Simple `/query` endpoint for Claude interactions
- ✅ Session management for conversation continuity  
- ✅ Health check endpoint
- ✅ Clean, minimal architecture with absolute imports
- ✅ Makefile for easy management

## Quick Start

```bash
# Install dependencies and start server
make all

# Or step by step:
make install   # Install dependencies
make start     # Start server in background
make test      # Test the API
```

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd claude_sdk_server

# Install dependencies using uv
make install
# or
uv sync
```

## Usage

### Using Makefile (Recommended)

```bash
# Start server in background
make start

# Check server status
make status

# View logs
make logs

# Stop server
make stop

# Run in development mode with auto-reload
make dev

# Test API endpoints
make test
```

### Manual Start

```bash
# Using Python module
uv run python -m src.claude_sdk_server.main

# Using uvicorn directly
uv run uvicorn src.claude_sdk_server.main:app --reload --port 8000
```

## API Endpoints

### POST /api/v1/query
Send a query to Claude with optional session management.

**Request:**
```json
{
    "prompt": "Your question here",
    "session_id": "optional-session-id"
}
```

**Response:**
```json
{
    "response": "Claude's response",
    "session_id": "session-id-for-continuity"
}
```

**Example:**
```bash
# New conversation
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello Claude!"}'

# Continue conversation
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What can you help with?", "session_id": "your-session-id"}'
```

### GET /api/v1/health
Health check endpoint.

**Response:**
```json
{
    "status": "healthy"
}
```

**Example:**
```bash
curl http://localhost:8000/api/v1/health
```

## Project Structure

```
claude_sdk_server/
├── Makefile                    # Build and management commands
├── README.md                   # This file
├── pyproject.toml             # Project dependencies
├── src/
│   └── claude_sdk_server/
│       ├── __init__.py
│       ├── main.py            # FastAPI app initialization
│       ├── api/
│       │   └── routers/
│       │       └── claude_router.py   # API endpoints
│       ├── services/
│       │   └── claude_service.py      # Claude SDK integration
│       └── models/
│           └── dto.py                  # Request/Response models
├── docs/                      # Documentation and AIDD framework
└── logs/                      # Server logs
```

## Example Usage

### Python Client Example

```python
import httpx
import asyncio

async def query_claude():
    async with httpx.AsyncClient() as client:
        # New conversation
        response = await client.post(
            "http://localhost:8000/api/v1/query",
            json={"prompt": "Hello Claude!"}
        )
        result = response.json()
        print(f"Response: {result['response']}")
        print(f"Session ID: {result['session_id']}")
        
        # Continue conversation
        response = await client.post(
            "http://localhost:8000/api/v1/query",
            json={
                "prompt": "What can you help me with?",
                "session_id": result['session_id']
            }
        )
        result = response.json()
        print(f"Continued: {result['response']}")

asyncio.run(query_claude())
```

### Test Script

A test script is provided to verify the API:

```bash
# Run the test script
uv run python test_simplified_api.py
```

## Makefile Commands

| Command | Description |
|---------|-------------|
| `make help` | Show all available commands |
| `make install` | Install dependencies |
| `make setup` | Full setup (install + directories) |
| `make start` | Start server in background |
| `make stop` | Stop background server |
| `make restart` | Restart server |
| `make status` | Check server status |
| `make dev` | Run in development mode |
| `make logs` | View server logs |
| `make test` | Test API endpoints |
| `make health` | Check health endpoint |
| `make query` | Send test query |
| `make clean` | Clean up generated files |
| `make all` | Setup and start server |

### Shortcuts

- `make s` - Start
- `make st` - Stop  
- `make r` - Restart
- `make d` - Dev mode
- `make l` - Logs
- `make h` - Health
- `make t` - Test

## Dependencies

- **fastapi** - Web framework
- **uvicorn** - ASGI server
- **pydantic** - Data validation
- **claude-code-sdk** - Claude integration

## Requirements

- Python 3.13+
- uv package manager
- Claude Code SDK credentials (ANTHROPIC_API_KEY)

## Environment Variables

The server will use the `ANTHROPIC_API_KEY` environment variable if set.

## Development

### Running Tests

```bash
make test
```

### Development Mode

```bash
make dev
```

This will start the server with auto-reload enabled.

## API Documentation

When the server is running, you can access:
- Interactive API docs: http://localhost:8000/docs
- ReDoc documentation: http://localhost:8000/redoc
- OpenAPI schema: http://localhost:8000/openapi.json

## License

[Your License Here]

## Contributing

[Contributing guidelines if applicable]