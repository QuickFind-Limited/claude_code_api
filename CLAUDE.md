## UV

- This project uses UV for package management
- Use:
  - `uv venv` to create a virtual environment
  - `uv pip install -r requirements.txt|pyproject.toml` to install dependencies
- Update any documentation when it's relevant, including CLAUDE.md
## Environment Variables
- Store secrets in a .env file (never commit it)
- A .env.example file should be provided for reference and any new secrets should be added to it
- The implementation should use the dotenv (or similar) library to load environment variables from .env files
- Variables should also be loaded from the environment

## File Organization

The API automatically enhances the system prompt to include file organization instructions:

- **Temporary files**: `tmp/{conversationId}/utils/` - For intermediate results and working files
- **Response attachments**: `tmp/{conversationId}/attachments/` - For files that should be provided to the user

### File Change Tracking

The API automatically tracks file changes in the attachments directory:

- **Before/After Comparison**: Captures file state before and after each Claude query
- **Change Detection**: Identifies new files and updated files based on modification timestamps
- **Response Enhancement**: Returns file information in the QueryResponse including:
  - `attachments`: List of all files with metadata (FileInfo objects)
  - `new_files`: List of newly created file paths
  - `updated_files`: List of modified file paths

This ensures consistent file organization across all Claude interactions and provides visibility into file changes made during each request.
**Core Principle**: We need to intelligently decide when to fail hard and fast to quickly address issues, and when to allow processes to complete in critical services despite failures. Read below carefully and make intelligent decisions on a case-by-case basis.
#### When to Fail Fast and Loud (Let it Crash!)

These errors should stop execution and bubble up immediately:

- **Service startup failures** - If credentials, database, or any service can't initialize, the system should crash with a clear error
- **Missing configuration** - Missing environment variables or invalid settings should stop the system
- **Service connection failures** - Don't hide connection issues, expose them
- **Authentication/authorization failures** - Security errors must be visible and halt the operation
- **Data corruption or validation errors** - Never silently accept bad data, Pydantic should raise
- **Critical dependencies unavailable** - If a required service is down, fail immediately
- **Invalid data that would corrupt state** - Never store malformed JSON or other invalid data
#### When to Complete but Log Detailed Errors

These operations should continue but track and report failures clearly:

- **WebSocket events** - Don't crash on a single event failure, log it and continue serving other clients
- Prioritize functionality over production-ready patterns
- Focus on user experience and feature completeness
- When updating code, don't reference what is changing
- Avoid keywords like LEGACY, CHANGED, REMOVED
- Focus on comments that document just the functionality of the code
- Remove dead code immediately rather than maintaining it
- No backward compatibility or legacy functions
- Always keep code SUPER minimal
- Never introduce features not explicitly mentioned
