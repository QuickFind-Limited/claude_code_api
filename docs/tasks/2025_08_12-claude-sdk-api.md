# Instruction: Claude SDK API Server

Build a minimal MVP REST API server that wraps Claude Code SDK for easy HTTP access.

## Existing files
- src/claude_sdk_server/__init__.py
- pyproject.toml
- CLAUDE.md

## New files to create
- src/claude_sdk_server/main.py
- src/claude_sdk_server/api/routers/claude_router.py
- src/claude_sdk_server/api/middleware/cors.py
- src/claude_sdk_server/api/middleware/logging.py
- src/claude_sdk_server/services/claude_service.py
- src/claude_sdk_server/models/dto.py
- src/claude_sdk_server/models/errors.py
- src/claude_sdk_server/core/config.py
- src/claude_sdk_server/core/logging.py
- tests/conftest.py
- tests/integration/test_claude_api.py
- tests/unit/test_claude_service.py

## Grouped tasks

### Setup & Dependencies
> Install and configure required packages
- Update pyproject.toml with FastAPI, uvicorn, claude-code-sdk, pytest, loguru, python-dotenv dependencies
- Create basic package structure with __init__.py files
- Setup logging configuration with loguru

### TDD: Write Tests First
> Follow Test-Driven Development approach
- Write unit tests for claude_service expected behavior
- Write integration tests for API endpoints
- Define test fixtures in conftest.py
- Tests should fail initially (Red phase)

### Core Models & Config
> Define data structures and configuration
- Create Pydantic DTOs for request/response in models/dto.py
- Create error models for standardized error responses
- Setup configuration in core/config.py with python-dotenv for .env loading
- Configure loguru logging system in core/logging.py

### Service Layer (Green Phase)
> Implement Claude SDK integration to pass tests
- Create claude_service.py with ClaudeSDKClient wrapper
- Implement async query method that calls Claude Code SDK
- Add comprehensive error handling (auth, rate limits, timeouts)
- Include loguru logging for debugging
- Handle response streaming or collection based on request

### Middleware Layer
> Setup cross-cutting concerns
- Create CORS middleware in api/middleware/cors.py for web client access
- Create logging middleware in api/middleware/logging.py for request/response logging
- Configure middleware registration order properly

### API Layer  
> Build REST endpoints
- Create FastAPI router in claude_router.py with POST /api/v1/claude/query endpoint
- Add /health endpoint for monitoring
- Implement request validation and error handling
- Setup main.py with FastAPI app initialization, middleware, and router registration

### Refactor Phase (TDD)
> Clean up and optimize code
- Refactor code for better readability
- Extract common patterns
- Ensure all tests still pass (Green)
- Add any missing edge case tests

### Documentation & Running
> Enable easy usage
- Add API documentation via FastAPI's automatic OpenAPI
- Create run script or command for local development with uvicorn
- Update README with usage instructions

## Validation checkpoints
- All tests pass in TDD cycle (Red → Green → Refactor)
- API server starts successfully on http://localhost:8000
- POST /api/v1/claude/query accepts prompt and returns Claude response
- GET /health returns 200 OK
- Integration tests pass with pytest
- OpenAPI docs available at /docs
- Clean separation between layers (router → service → SDK)
- Middleware properly handles CORS and logging
- Loguru logs are properly formatted and informative
- Error responses follow consistent format

## Estimations
- Confidence: 9/10
- Time to implement: 30-45 minutes
