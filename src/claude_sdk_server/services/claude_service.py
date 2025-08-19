"""Minimal Claude service implementation using Claude Code SDK."""

import os
import logging
from claude_code_sdk import ClaudeCodeOptions, query, ResultMessage
from src.claude_sdk_server.models.dto import QueryRequest, QueryResponse

logger = logging.getLogger(__name__)

class ClaudeService:
    """Service for interacting with Claude Code SDK."""
    
    async def query(self, request: QueryRequest) -> QueryResponse:
        """Send a query to Claude using the SDK query function."""
        response_text = None
        current_session_id = request.session_id
        
        # Log environment check
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            logger.warning("ANTHROPIC_API_KEY not found in environment")
        else:
            logger.info(f"API key found: ...{api_key[-4:]}")
        
        options = ClaudeCodeOptions(
            resume=request.session_id,
            max_turns=request.max_turns,
            permission_mode="bypassPermissions"
        )
        
        logger.info(f"Querying with prompt: {request.prompt[:50]}...")
        
        # Execute query
        message_count = 0
        all_assistant_messages = []
        
        async for message in query(prompt=request.prompt, options=options):
            message_count += 1
            message_type = type(message).__name__
            logger.info(f"Received message type: {message_type}")
            
            if isinstance(message, ResultMessage):
                # ResultMessage contains the final result after all turns
                if message.result:
                    response_text = message.result
                elif all_assistant_messages:
                    # Use the concatenated assistant messages if result is empty
                    response_text = '\n\n'.join(all_assistant_messages)
                current_session_id = message.session_id
            elif message_type == "AssistantMessage":
                # Collect all assistant messages
                text_content = None
                if hasattr(message, 'content'):
                    content = message.content
                    # Handle list of content blocks (e.g., tool use blocks)
                    if isinstance(content, list):
                        text_parts = []
                        for block in content:
                            if hasattr(block, 'text'):
                                text_parts.append(block.text)
                            elif hasattr(block, 'type') and block.type == 'text':
                                text_parts.append(str(block))
                            elif isinstance(block, str):
                                text_parts.append(block)
                        if text_parts:
                            text_content = '\n'.join(text_parts)
                    elif isinstance(content, str):
                        text_content = content
                    else:
                        text_content = str(content)
                elif hasattr(message, 'text'):
                    text_content = message.text
                else:
                    text_content = str(message)
                
                # Only add non-empty text content
                if text_content and text_content.strip():
                    all_assistant_messages.append(text_content)
        
        logger.info(f"Total messages received: {message_count}")
        
        # Ensure we have a response
        if response_text is None:
            response_text = "No response received from Claude"
        
        if not current_session_id:
            # Generate a simple session ID if none provided
            import uuid
            current_session_id = str(uuid.uuid4())
        
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
