# Simplified Claude SDK API Server

A minimal FastAPI server providing a REST API interface to Claude Code SDK.

## Features

- Single `/query` endpoint for Claude interactions
- Session management for conversation continuity
- Health check endpoint
- Clean, minimal architecture

## Installation

```bash
# Install dependencies
uv sync
```

## Usage

### Start the server

```bash
# Method 1: Using Python module
uv run python -m src.claude_sdk_server.main

# Method 2: Using uvicorn directly
uv run uvicorn src.claude_sdk_server.main:app --reload --port 8000
```

### API Endpoints

#### POST /api/v1/query
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

#### GET /api/v1/health
Health check endpoint.

**Response:**
```json
{
    "status": "healthy"
}
```

## Example Usage

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

## Architecture

```
src/claude_sdk_server/
├── main.py                    # FastAPI app initialization
├── api/
│   └── routers/
│       └── claude_router.py   # API endpoints
├── services/
│   └── claude_service.py      # Claude SDK integration
└── models/
    └── dto.py                  # Request/Response models
```

## Dependencies

- fastapi - Web framework
- uvicorn - ASGI server
- pydantic - Data validation
- claude-code-sdk - Claude integration