# Instruction: Simplified Claude SDK API Server

Create a minimal FastAPI server with a single `/query` endpoint that interfaces with Claude Code SDK, maintaining clean architecture with routers and services while removing all unnecessary complexity.

## Reference Implementation Example

Use @claude_code_example.py as the pattern for Claude SDK integration:

```python
import asyncio
from claude_code_sdk import ClaudeSDKClient, ClaudeCodeOptions, query, ResultMessage

# Method 1: Using ClaudeSDKClient for persistent conversations
async def multi_turn_conversation() -> str:
    session_id = None
    async with ClaudeSDKClient() as client:
        while True:
            query: str = input("Enter a query: ")
            if query == "exit":
                break
            else:
                await client.query(query)
                async for msg in client.receive_response():
                    print(msg)
                    if isinstance(msg, ResultMessage):
                        session_id = msg.session_id
        return session_id
        # The conversation context is maintained throughout

# Method 2: Using query function with session management (USE THIS PATTERN FOR API)
async def resume_session():
    # Resume specific session
    async for message in query(
        prompt=input("Enter a query: "), 
        options=ClaudeCodeOptions(
            resume="21573a4c-872b-4866-96c6-084e8085451d",
            max_turns=3
        )
    ):
        if type(message).__name__ == "ResultMessage":
            print(message.result)

# Run the examples
# session_id = asyncio.run(multi_turn_conversation())
# print(session_id)
# asyncio.run(resume_session())
```

**Key patterns to implement in the API:**
- Use `query()` function from `claude_code_sdk` (Method 2)
- Pass `ClaudeCodeOptions` with `resume=session_id` for continuing sessions
- Set `max_turns=50` for single request/response
- Extract `response` from `message.result` and `session_id` from `message.session_id`
- Handle `ResultMessage` type to get the final response

## Existing files
- src/claude_sdk_server/main.py (to replace)
- src/claude_sdk_server/api/routers/claude_router.py (to simplify)
- src/claude_sdk_server/services/claude_service.py (to simplify)
- src/claude_sdk_server/models/dto.py (to simplify)
- pyproject.toml (to update)
- claude_code_example.py (reference implementation)

## New files to create
- None (all files will be replacements/simplifications)

## Grouped tasks

### Clean Project Structure
> Remove all unnecessary complexity from src/
- Delete auth, middleware, database, redis, monitoring code
- Remove complex error handling and custom exceptions
- Clean up configuration files and unused imports
- Delete complex implementations (everything is versioned in git)

### Core API Implementation
> Implement minimal `/query` endpoint using claude_code_example.py patterns
- Create simplified main.py with FastAPI app initialization
- Implement claude_router.py with single POST /query endpoint
- Build claude_service.py using query() from claude_code_sdk
- Define minimal DTOs: QueryRequest (prompt, session_id?) and QueryResponse

### Service Layer
> Implement Claude SDK integration following example patterns
- Use query() function with ClaudeCodeOptions for session management
- Handle ResultMessage to extract response and session_id
- Return 500 on any SDK failures without complex error handling
- Prepare structure for future streaming support (not implemented yet)

### Project Configuration
> Update project files for minimal dependencies
- Update pyproject.toml with only: fastapi, uvicorn, pydantic, claude-code-sdk
- Remove all test dependencies and complex build configurations
- Update imports in __init__.py for simplified structure
- Clean up unused configuration files

### Final Cleanup
> Ensure clean, minimal codebase
- Remove all test files and directories
- Delete unused service files and models
- Verify only essential code remains
- Add simple health check endpoint for basic monitoring

## Validation checkpoints
- API starts with `python -m claude_sdk_server` or `uvicorn`
- POST /query accepts prompt and optional session_id
- Response includes Claude's answer and session_id
- Session continuation works with provided session_id
- No authentication required
- Returns 500 on any errors

## Estimations
- Confidence: 9/10
- Time to implement: 30-45 minutes
