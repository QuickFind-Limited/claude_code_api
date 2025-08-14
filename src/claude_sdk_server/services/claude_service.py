"""Minimal Claude service implementation using Claude Code SDK."""

from claude_code_sdk import ClaudeCodeOptions, query, ResultMessage
from src.claude_sdk_server.models.dto import QueryRequest, QueryResponse

class ClaudeService:
    """Service for interacting with Claude Code SDK."""
    
    async def query(self, request: QueryRequest) -> QueryResponse:
        """Send a query to Claude using the SDK query function."""
        response_text = ""
        current_session_id = request.session_id
        
        # Build options based on whether we have a session_id
        options = ClaudeCodeOptions(
            resume=request.session_id,
            max_turns=1
        ) if request.session_id else ClaudeCodeOptions(max_turns=1)
        
        # Execute query
        async for message in query(prompt=request.prompt, options=options):
            if isinstance(message, ResultMessage):
                response_text = message.result
                current_session_id = message.session_id
            else:
                # Accumulate any other message types as text
                response_text += str(message)
        
        if not current_session_id:
            raise Exception("Failed to get session ID from Claude")
        
        return QueryResponse(
            response=response_text,
            session_id=current_session_id
        )

# Dependency injection function
_service_instance = None

def get_claude_service() -> ClaudeService:
    """Get or create Claude service instance."""
    global _service_instance
    if _service_instance is None:
        _service_instance = ClaudeService()
    return _service_instance