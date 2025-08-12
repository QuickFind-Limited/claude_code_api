"""Claude service implementation using the real Claude Code SDK."""

import os
import uuid
from typing import Optional, Dict, Any, AsyncGenerator, List
from datetime import datetime

from claude_code_sdk import ClaudeSDKClient, ClaudeCodeOptions
from loguru import logger

from ..models.dto import QueryRequest, QueryResponse, StreamChunk
from ..models.errors import (
    AuthenticationError,
    RateLimitError,
    SDKError,
    TimeoutError
)
from ..core.config import settings


class ClaudeService:
    """Service for interacting with Claude Code SDK."""
    
    def __init__(self):
        """Initialize Claude service."""
        self._client: Optional[ClaudeSDKClient] = None
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._initialize_client()
    
    def _initialize_client(self) -> None:
        """Initialize Claude Code SDK client."""
        try:
            # Get API key from environment
            api_key = settings.claude_api_key or os.getenv("ANTHROPIC_API_KEY")
            
            if not api_key:
                logger.warning("No Anthropic API key found. Claude Code SDK will not be functional.")
                return
            
            # Set environment variable for Claude Code SDK
            os.environ["ANTHROPIC_API_KEY"] = api_key
            
            logger.info("Claude Code SDK client configuration ready")
            
        except Exception as e:
            logger.error(f"Failed to initialize Claude Code SDK client: {e}")
            self._client = None
    
    def _map_model_name(self, model_input: str) -> str:
        """Map user-friendly model names to Claude Code SDK model names."""
        model_mapping = {
            "opus": "claude-opus-4-1-20250805",
            "sonnet": "claude-sonnet-4-20250514"
        }
        
        # Return mapped model or default to sonnet if invalid
        return model_mapping.get(model_input.lower(), "claude-sonnet-4-20250514")

    async def _get_client_for_session(
        self,
        conversation_id: str,
        request: QueryRequest
    ) -> ClaudeSDKClient:
        """Create a client for a session with conversation history context."""        
        # Map model name to Claude Code SDK format
        claude_model = self._map_model_name(request.model)
        
        # Build system prompt with conversation history if available
        system_prompt = "You are Claude, a helpful AI assistant."
        
        if conversation_id in self._sessions:
            messages = self._sessions[conversation_id].get("messages", [])
            if messages:
                system_prompt += "\n\nConversation history:\n"
                for msg in messages:
                    role = msg["role"].capitalize()
                    content = msg["content"]
                    system_prompt += f"{role}: {content}\n"
                system_prompt += "\nPlease respond to the following message while maintaining context from our conversation history."
        
        # Create options for this session
        options = ClaudeCodeOptions(
            model=claude_model,  # Pass the mapped model
            system_prompt=system_prompt,
            max_turns=100,  # Allow long conversations
            max_thinking_tokens=request.max_tokens if request.max_tokens <= 8000 else 8000,
            allowed_tools=request.tools or [
                "Bash", "Read", "Write", "WebSearch", "Glob", "Grep"
            ]
        )
        
        logger.info(f"Creating Claude Code SDK client with model: {claude_model} for conversation: {conversation_id}")
        
        # Create new client for this session (each request gets fresh client but with history)
        client = ClaudeSDKClient(options=options)
        
        return client
    
    async def query(self, request: QueryRequest) -> QueryResponse:
        """Send query to Claude Code SDK."""
        try:
            logger.info(f"Sending query to Claude Code SDK: {request.prompt[:100]}...")
            
            # Generate conversation ID if not provided
            conversation_id = request.conversation_id or str(uuid.uuid4())
            
            # Get or create session
            if conversation_id not in self._sessions:
                self._sessions[conversation_id] = {
                    "id": conversation_id,
                    "created_at": datetime.utcnow().isoformat(),
                    "messages": []
                }
            
            # Get client for this session
            client = await self._get_client_for_session(conversation_id, request)
            
            full_response = ""
            
            # Use Claude Code SDK with proper connection handling
            async with client:
                # Send the query
                await client.query(request.prompt)
                
                # Collect the response
                async for message in client.receive_response():
                    if hasattr(message, 'content'):
                        for block in message.content:
                            if hasattr(block, 'text'):
                                full_response += block.text
                            elif hasattr(block, 'type') and block.type == 'text':
                                full_response += getattr(block, 'text', str(block))
                    elif hasattr(message, 'text'):
                        full_response += message.text
                    else:
                        # Fallback: convert message to string
                        full_response += str(message)
            
            # Store in session
            self._sessions[conversation_id]["messages"].extend([
                {"role": "user", "content": request.prompt, "timestamp": datetime.utcnow().isoformat()},
                {"role": "assistant", "content": full_response, "timestamp": datetime.utcnow().isoformat()}
            ])
            
            logger.info(f"Query completed successfully for conversation {conversation_id}")
            
            # Estimate token usage (approximation)
            prompt_tokens = len(request.prompt.split())
            completion_tokens = len(full_response.split())
            
            # Get the actual model used
            claude_model = self._map_model_name(request.model)
            
            return QueryResponse(
                response=full_response,
                conversation_id=conversation_id,
                model=claude_model,  # Return the actual Claude model name
                usage={
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": prompt_tokens + completion_tokens
                },
                metadata={
                    "claude_code_sdk": True,
                    "requested_model": request.model,  # Original request
                    "actual_model": claude_model,  # Mapped model
                    "tools_used": request.tools or [],
                    "session_message_count": len(self._sessions[conversation_id]["messages"])
                }
            )
            
        except Exception as e:
            error_msg = str(e).lower()
            logger.error(f"Error calling Claude Code SDK: {e}")
            
            # Categorize errors based on message content
            if "authentication" in error_msg or "api key" in error_msg or "401" in str(e):
                raise AuthenticationError(f"Authentication failed: {e}")
            elif "rate" in error_msg and "limit" in error_msg or "429" in str(e):
                raise RateLimitError(f"Rate limit exceeded: {e}")
            elif "timeout" in error_msg:
                raise TimeoutError(f"Request timed out: {e}")
            else:
                raise SDKError(f"Claude Code SDK error: {e}")
    
    async def stream_query(self, request: QueryRequest) -> AsyncGenerator[StreamChunk, None]:
        """Stream query response from Claude Code SDK."""
        try:
            logger.info(f"Starting streaming query with Claude Code SDK: {request.prompt[:100]}...")
            
            # Generate conversation ID
            conversation_id = request.conversation_id or str(uuid.uuid4())
            
            # Get the actual model used
            claude_model = self._map_model_name(request.model)
            
            # Get client for this session
            client = await self._get_client_for_session(conversation_id, request)
            
            full_response = ""
            
            # Use Claude Code SDK with proper connection handling
            async with client:
                # Send the query
                await client.query(request.prompt)
                
                # Stream the response
                async for message in client.receive_response():
                    chunk_text = ""
                    
                    if hasattr(message, 'content'):
                        for block in message.content:
                            if hasattr(block, 'text'):
                                chunk_text = block.text
                            elif hasattr(block, 'type') and block.type == 'text':
                                chunk_text = getattr(block, 'text', str(block))
                    elif hasattr(message, 'text'):
                        chunk_text = message.text
                    else:
                        chunk_text = str(message)
                    
                    if chunk_text:
                        full_response += chunk_text
                        
                        yield StreamChunk(
                            chunk=chunk_text,
                            finished=False,
                            metadata={"claude_code_sdk": True}
                        )
                
                # Final completion chunk
                yield StreamChunk(
                    chunk="",
                    finished=True,
                    metadata={
                        "claude_code_sdk": True,
                        "requested_model": request.model,
                        "actual_model": claude_model,
                        "full_response_length": len(full_response),
                        "conversation_id": conversation_id
                    }
                )
                
                # Store in session if we have content
                if conversation_id not in self._sessions:
                    self._sessions[conversation_id] = {
                        "id": conversation_id,
                        "created_at": datetime.utcnow().isoformat(),
                        "messages": []
                    }
                
                if full_response:
                    self._sessions[conversation_id]["messages"].extend([
                        {"role": "user", "content": request.prompt, "timestamp": datetime.utcnow().isoformat()},
                        {"role": "assistant", "content": full_response, "timestamp": datetime.utcnow().isoformat()}
                    ])
            
        except Exception as e:
            logger.error(f"Error in Claude Code SDK streaming query: {e}")
            raise SDKError(f"Claude Code SDK streaming error: {e}")
    
    async def create_session(self, conversation_id: Optional[str] = None) -> Dict[str, Any]:
        """Create a new conversation session."""
        session_id = conversation_id or str(uuid.uuid4())
        
        self._sessions[session_id] = {
            "id": session_id,
            "created_at": datetime.utcnow().isoformat(),
            "messages": [],
            "metadata": {
                "claude_code_sdk": True
            }
        }
        
        logger.info(f"Created Claude Code SDK session: {session_id}")
        return self._sessions[session_id]
    
    async def is_session_active(self, conversation_id: str) -> bool:
        """Check if a session is active."""
        return conversation_id in self._sessions
    
    async def get_session(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get session information."""
        return self._sessions.get(conversation_id)
    
    async def close_session(self, conversation_id: str) -> None:
        """Close a conversation session."""
        if conversation_id in self._sessions:
            del self._sessions[conversation_id]
            logger.info(f"Closed Claude Code SDK session: {conversation_id}")
    
    async def clear_all_sessions(self) -> None:
        """Clear all sessions."""
        count = len(self._sessions)
        
        # Clean up all sessions
        for session_id in list(self._sessions.keys()):
            await self.close_session(session_id)
        
        logger.info(f"Cleared {count} Claude Code SDK sessions")


# Singleton instance
_service_instance: Optional[ClaudeService] = None


def get_claude_service() -> ClaudeService:
    """Get Claude service singleton instance."""
    global _service_instance
    if _service_instance is None:
        _service_instance = ClaudeService()
    return _service_instance
