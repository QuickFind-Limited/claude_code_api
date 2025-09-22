# Claude SDK Server 🚀

A lean FastAPI backend that powers the Claude Code chatbot with **SSE streaming** and **secure attachment delivery**.

## ✨ Features

### Core Functionality
- ✅ **Streaming Query API** – `/api/v1/query/stream` streams Claude Code responses via Server-Sent Events.
- ✅ **Attachment Delivery** – `/api/v1/files/conversations/{conversationId}/attachments/{file}` serves generated artifacts safely.
- ✅ **Observability Ready** – Logfire and Atla Insights instrumentation is preconfigured.

### Project Layout
- 🧱 **Focused Backend** – `src/claude_sdk_server` contains only the production API surface required by the current frontend.
- 🗂️ **`legacy/` Archive** – Historical scripts, datasets, docs, and experimental tests now live under `legacy/` for reference.

## 🚀 Quick Start

```bash
# Start the server
make up

# Exercise the streaming endpoint
make test-stream

# Watch formatted logs
make logs-pretty
```

## 📦 Installation

### Using Docker (Recommended)

```bash
# Using Make commands (easiest)
make up      # Build and start server
make down    # Stop server
make logs    # Tail logs
make restart # Restart server
```

### Manual Docker Setup

```bash
# Build the Docker image
docker build -t claude-sdk-server:latest .

# Run with Docker Compose
docker-compose up -d

# Or run the container directly
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
make clean       # Remove containers and images
```

### Testing Commands
```bash
make test        # Run backend test suite
make test-stream # Exercise the streaming pipeline
make test-sse    # Smoke-test the SSE endpoint
```

### Development Commands
```bash
make logs-pretty    # Watch logs with beautiful formatting
make demo-stream    # Run streaming demo with live query
```

## 📡 API Endpoints

### Streaming Conversation
```bash
curl -N -X POST http://localhost:8000/api/v1/query/stream \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{
        "prompt": "Refactor the data loader",
        "model": "claude-sonnet-4-20250514",
        "session_id": null
      }'
```

Events are labeled (`connection`, `log`, `response`, `complete`, `error`) and encoded as JSON so the frontend can display progress updates, tool usage, and final results. The final `response` payload mirrors the `QueryResponse` DTO (attachments, new_files, updated_files, etc.).

### Attachment Delivery
```bash
curl -LO "http://localhost:8000/api/v1/files/conversations/<conversationId>/attachments/<relative-path>?download=true"
```

Files are served from `./tmp/{conversationId}/attachments/` with extension and size checks. Use `download=true` to force download; omit it for inline preview when supported by the browser.

> Legacy admin endpoints (websocket bridges, JSONL stream, clean-up utilities) now live under `legacy/` and are not mounted by default.

## 🗄️ Legacy Workspace

The [`legacy/`](legacy/) directory collects archival assets:
- `scripts/` – one-off automation and exploration scripts.
- `docs/` – historical reports and write-ups.
- `data/` – JSON/CSV artifacts created during previous research.
- `tests/` – deprecated integration scripts and shell utilities.
- `demos/` – experimental frontends, including the retired `frontend/` bundle.
- `logs/` – preserved log files.

These paths are excluded from linting and pre-commit checks but remain versioned for reference.

## 🔎 Observability

- `logfire_exporter` + `FastAPIInstrumentor` capture traces for every request.
- Atla Insights is wired via `instrument_claude_code_sdk()`; set `ATLA_INSIGHTS_API_KEY` / `ATLA_ENVIRONMENT` to enable.
- Structured Loguru configuration lives in `src/claude_sdk_server/utils/logging_config.py`.

## 🚧 Development

### Project Structure
```
claude_sdk_server/
├── src/
│   └── claude_sdk_server/
│       ├── api/
│       │   └── routers/
│       │       ├── attachments_router.py  # Attachment download endpoint
│       │       └── claude_router.py       # SSE conversation endpoint
│       ├── legacy/                        # Archived router implementations
│       ├── models/
│       ├── services/
│       ├── streaming/
│       └── utils/
├── legacy/                                # Archived scripts, docs, data, tests
├── chatbot-frontend/                      # Active React frontend
├── Makefile
├── docker-compose.yml
└── README.md
```

### Running Tests
```bash
make test
make test-stream
make test-sse
```

### Debugging
```bash
make logs
make logs-pretty
```

## 📝 License

MIT License - see `LICENSE` for details.
