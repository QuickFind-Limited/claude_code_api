# Claude SDK Server 🚀

A production-ready FastAPI server providing REST API interface to Claude Code SDK with **real-time event streaming**, **beautiful logging**, and **comprehensive monitoring**.

## ✨ Features

### Core Functionality
- ✅ **Streaming Query API** – `/api/v1/query/stream` exposes Claude Code responses over Server-Sent Events with rich event metadata.
- ✅ **Attachment Delivery** – `/api/v1/files/conversations/{conversationId}/attachments/{file}` serves generated artifacts for inline preview or download.
- ✅ **Observability Ready** – Logfire instrumentation and Atla Insights hooks are preconfigured for traceable runs.

### Project Layout
- 🗂️ **`legacy/` Archive** – Historical scripts, datasets, and experiments have been moved out of the active workspace but remain available for reference.
- 🧱 **Focused Backend** – `src/claude_sdk_server` now contains only the production API surface and dependencies required by the current frontend.

## 🚀 Quick Start

```bash
cp .env.example .env   # Populate with real ANTHROPIC, ATLA, and LOGFIRE secrets
make up                # Build and start the API container
make logs              # Tail runtime logs
make logs-pretty       # Optional: filtered log stream
```

Once the stack is up, exercise the streaming endpoint:

```bash
curl -N -X POST http://localhost:8000/api/v1/query/stream \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{
        "prompt": "Generate a concise deployment checklist",
        "model": "claude-sonnet-4-20250514"
      }'
```

Each event includes a labeled `event` field (`connection`, `log`, `response`, `complete`, or `error`) and structured JSON data that the React frontend consumes directly. The final `response` payload matches the `QueryResponse` DTO so attachments and file-change metadata are available immediately.

## 🎮 Makefile Commands

```bash
make up            # Build and start the server
make down          # Stop the server
make restart       # Restart the server
make logs          # View server logs
make logs-pretty   # Filter logs for key events
make frontend-3002 # Launch the React dashboard (optional)
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

### Attachment Delivery
```bash
curl -LO "http://localhost:8000/api/v1/files/conversations/<conversationId>/attachments/<relative-path>?download=true"
```

Paths are validated against `./tmp/{conversationId}/attachments/` and support inline preview or forced download via the `download` query parameter.

> Legacy admin endpoints, WebSocket bridges, and JSONL streams have been archived under `legacy/` and are no longer loaded by default.

## 🔎 Observability

- Logfire traces are exported via OTLP; set `LOGFIRE_TOKEN` to authorize ingestion.
- Atla Insights hooks remain active; provide `ATLA_INSIGHTS_API_KEY` and `ATLA_ENVIRONMENT` to funnel runtime metadata.
- Server logs continue to stream through the custom logger configuration in `src/claude_sdk_server/utils/logging_config.py`.

## 🗄️ Legacy Workspace

Historical scripts, datasets, reports, and manual test harnesses now live in the [`legacy/`](legacy/) folder. They remain available for reference but are excluded from linting and pre-commit hooks.

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
├── legacy/                                # Archived scripts, data, docs, tests
├── tests/                                 # Active test suite
├── Makefile                               # Common commands
├── docker-compose.yml                     # Docker configuration
└── README.md                              # This file
```

### Running Tests
```bash
uv run pytest
```

## 📝 License

MIT License - See LICENSE file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 🐛 Troubleshooting

### Port 8000 Already in Use
```bash
lsof -i :8000
kill -9 <PID>

docker stop claude-sdk-server
```

### No Events Appearing
1. Confirm the container is running: `docker ps | grep claude-sdk-server`
2. Verify required secrets exist in `.env`
3. Tail logs for errors: `make logs`

## 📚 Additional Resources

- [Claude Code SDK Documentation](https://docs.anthropic.com/claude/docs/claude-code)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Server-Sent Events Spec](https://html.spec.whatwg.org/multipage/server-sent-events.html)
