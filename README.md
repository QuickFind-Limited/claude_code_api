# Claude SDK Server

A minimal MVP REST API server that wraps the Claude Code SDK for easy HTTP access with conversation context management.

## 🚀 Features

- **Real Claude Code SDK Integration**: Uses the official `claude-code-sdk` package (not mocks)
- **Model Selection**: Support for both Claude Opus and Sonnet models
- **Conversation Context**: Maintains conversation history across requests
- **MCP Tool Support**: Full support for MCP (Model Context Protocol) tools including Perplexity, Context7, Firecrawl, Odoo, and more
- **Streaming Support**: Server-Sent Events (SSE) for real-time streaming responses
- **Session Management**: Create, manage, and close conversation sessions
- **FastAPI Framework**: Modern, fast web framework with automatic API documentation
- **Comprehensive Error Handling**: Proper error responses and logging
- **Type Safety**: Full Pydantic v2 validation for requests and responses

## 📋 API Endpoints

### Query Claude
- **POST** `/api/v1/claude/query` - Send a query to Claude
- **Parameters**:
  - `prompt` (string): The message to send to Claude
  - `model` (string): Either "opus" or "sonnet" (default: "sonnet")
  - `conversation_id` (string, optional): Session ID for conversation context
  - `stream` (boolean): Enable streaming response
  - `max_tokens` (int): Maximum tokens to generate
  - `temperature` (float): Sampling temperature (0.0-1.0)
  - `tools` (array, optional): List of allowed tools (default includes basic tools and MCP servers)
  - `disallowed_tools` (array, optional): List of explicitly disallowed tools
  - `mcp_servers` (object, optional): MCP server configurations for external tools

### Session Management
- **POST** `/api/v1/claude/sessions` - Create a new conversation session
- **GET** `/api/v1/claude/sessions/{session_id}` - Get session information
- **DELETE** `/api/v1/claude/sessions/{session_id}` - Delete a session

### Health Check
- **GET** `/health` - Health check endpoint

## 🛠️ Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd claude_sdk_server
   ```

2. **Install dependencies with uv**:
   ```bash
   uv sync
   ```

3. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env and add your Anthropic API key
   ```

4. **Run the server**:
   ```bash
   uv run uvicorn src.claude_sdk_server.main:app --host 0.0.0.0 --port 8000
   ```

## 🔧 Configuration

The server uses environment variables for configuration:

```env
# Application
APP_NAME="Claude SDK Server"
APP_VERSION="0.1.0"
DEBUG=false
ENVIRONMENT=development

# Server
HOST=0.0.0.0
PORT=8000

# Claude SDK
ANTHROPIC_API_KEY="your-api-key-here"
CLAUDE_MODEL=sonnet
CLAUDE_MAX_TOKENS=4096
```

## 📚 Usage Examples

### Basic Query
```bash
curl -X POST "http://localhost:8000/api/v1/claude/query" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Hello Claude!",
    "model": "sonnet"
  }'
```

### Conversation with Context
```bash
# First message
curl -X POST "http://localhost:8000/api/v1/claude/query" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "My name is Alice and I love cats.",
    "conversation_id": "my-session",
    "model": "sonnet"
  }'

# Follow-up message (remembers context)
curl -X POST "http://localhost:8000/api/v1/claude/query" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "What do you remember about me?",
    "conversation_id": "my-session",
    "model": "sonnet"
  }'
```

### Streaming Response
```bash
curl -X POST "http://localhost:8000/api/v1/claude/query" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Tell me a story",
    "stream": true,
    "model": "sonnet"
  }'
```

### Using MCP Tools
```bash
# Example with Perplexity for web search
curl -X POST "http://localhost:8000/api/v1/claude/query" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Search for the latest news about AI developments using Perplexity",
    "model": "sonnet",
    "tools": ["mcp__perplexity-ask", "WebSearch", "Read", "Write"]
  }'

# Example with custom allowed tools
curl -X POST "http://localhost:8000/api/v1/claude/query" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Help me with this task",
    "model": "sonnet",
    "tools": [
      "Read", "Write", "Edit",
      "mcp__context7",
      "mcp__Firecrawl",
      "mcp__odoo_mcp"
    ]
  }'
```

## 🏗️ Architecture

The server follows a clean architecture pattern:

```
src/claude_sdk_server/
├── main.py                    # FastAPI application entry point
├── core/
│   ├── config.py             # Configuration management
│   └── logging.py            # Logging setup
├── models/
│   ├── dto.py                # Data Transfer Objects (Pydantic models)
│   └── errors.py             # Custom exception classes
├── services/
│   └── claude_service.py     # Claude Code SDK integration
└── api/
    ├── middleware/           # CORS and logging middleware
    └── routers/             # API route handlers
        └── claude_router.py
```

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src --cov-report=html

# Run specific test file
uv run pytest tests/test_claude_service.py -v
```

## 🔧 MCP Tools Configuration

The server supports MCP (Model Context Protocol) tools for enhanced capabilities:

### Default Enabled MCP Servers
By default, the following MCP servers are enabled:
- **perplexity-ask**: Web search and research capabilities
- **context7**: Documentation and library reference
- **Firecrawl**: Web scraping and data extraction
- **odoo_mcp**: Odoo ERP integration
- **playwright**: Browser automation

### Tool Naming Convention
MCP tools follow the pattern: `mcp__<server_name>__<tool_name>`

Examples:
- `mcp__perplexity-ask__perplexity_ask` - Specific tool
- `mcp__perplexity-ask` - All tools from Perplexity server
- `mcp__context7` - All tools from Context7 server

### Custom MCP Server Configuration
You can configure custom MCP servers in your request:

```json
{
  "prompt": "Your query",
  "mcp_servers": {
    "custom_server": {
      "command": "npx",
      "args": ["-y", "@your/mcp-server"],
      "env": {
        "API_KEY": "your-key"
      }
    }
  }
}
```

### Security Considerations
- Use `disallowed_tools` to block dangerous operations
- Carefully review which MCP servers you enable
- Consider limiting tools in production environments

## 🔍 Conversation Context Implementation

The server implements conversation context by:

1. **Session Storage**: Each `conversation_id` maintains message history
2. **History Injection**: Previous messages are included in the system prompt
3. **Context Building**: Fresh Claude Code SDK clients receive full conversation history

This approach works because:
- Claude Code SDK sessions are independent
- Context is managed at the application level
- Message history is preserved across requests

## 📝 API Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🚨 Error Handling

The server provides comprehensive error handling:

- **400 Bad Request**: Invalid input parameters
- **401 Unauthorized**: Authentication issues with Claude API
- **429 Too Many Requests**: Rate limiting
- **500 Internal Server Error**: Unexpected server errors

All errors include detailed error messages and error codes for proper client handling.

## 🛡️ Security

- **CORS**: Configurable Cross-Origin Resource Sharing
- **Input Validation**: Pydantic validation for all inputs
- **API Key Security**: Environment-based API key management
- **Error Sanitization**: Sensitive information filtering in error responses

## 📊 Performance

- **Async/Await**: Fully asynchronous request handling
- **Connection Reuse**: Efficient HTTP connection management
- **Streaming**: Real-time response streaming for long responses
- **Logging**: Structured logging with performance metrics

## 🔗 Dependencies

- **FastAPI**: Modern web framework
- **Claude Code SDK**: Official Anthropic SDK
- **Pydantic v2**: Data validation and settings
- **Uvicorn**: ASGI server
- **Loguru**: Structured logging

## 📈 Development

This project follows TDD (Test-Driven Development) principles and uses:

- **uv**: Fast Python package manager
- **pytest**: Testing framework
- **black**: Code formatting
- **ruff**: Linting
- **mypy**: Type checking

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Write tests for your changes
4. Implement your feature
5. Run the test suite
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🌟 Status

- **Version**: 0.1.0 (Initial Release)
- **Status**: Production Ready
- **Tested**: Fully tested with real Claude Code SDK
- **Repository**: [QuickFind-Limited/claude_code_api](https://github.com/QuickFind-Limited/claude_code_api)