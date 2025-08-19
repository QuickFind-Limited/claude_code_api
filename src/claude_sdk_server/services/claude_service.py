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
            logger.info(f"[Message {message_count}] Type: {message_type}")
            
            # Log full message details for debugging
            logger.debug(f"[Message {message_count}] Full content: {str(message)[:500]}...")
            
            if isinstance(message, ResultMessage):
                # ResultMessage contains the final result after all turns
                logger.info(f"[FINAL RESULT] Session ID: {message.session_id}")
                if message.result:
                    response_text = message.result
                    logger.info(f"[FINAL RESULT] Response length: {len(response_text)} chars")
                elif all_assistant_messages:
                    # Use the concatenated assistant messages if result is empty
                    response_text = '\n\n'.join(all_assistant_messages)
                    logger.info(f"[FINAL RESULT] Using concatenated messages: {len(response_text)} chars")
                current_session_id = message.session_id
                
            elif message_type == "AssistantMessage":
                logger.info(f"[ASSISTANT] Processing assistant message")
                # Collect all assistant messages
                text_content = None
                if hasattr(message, 'content'):
                    content = message.content
                    # Handle list of content blocks (e.g., tool use blocks)
                    if isinstance(content, list):
                        logger.info(f"[ASSISTANT] Content has {len(content)} blocks")
                        text_parts = []
                        for i, block in enumerate(content):
                            block_type = getattr(block, 'type', 'unknown')
                            logger.debug(f"[ASSISTANT] Block {i+1}/{len(content)} - Type: {block_type}")
                            
                            # Log tool usage
                            if hasattr(block, 'name') and hasattr(block, 'input'):
                                logger.info(f"[TOOL USE] Tool: {block.name}")
                                logger.debug(f"[TOOL USE] Input: {str(block.input)[:200]}...")
                            
                            if hasattr(block, 'text'):
                                text_parts.append(block.text)
                                logger.debug(f"[ASSISTANT] Text block: {block.text[:100]}...")
                            elif hasattr(block, 'type') and block.type == 'text':
                                text_parts.append(str(block))
                            elif isinstance(block, str):
                                text_parts.append(block)
                        if text_parts:
                            text_content = '\n'.join(text_parts)
                    elif isinstance(content, str):
                        text_content = content
                        logger.debug(f"[ASSISTANT] String content: {content[:200]}...")
                    else:
                        text_content = str(content)
                        logger.debug(f"[ASSISTANT] Other content type: {type(content)}")
                elif hasattr(message, 'text'):
                    text_content = message.text
                    logger.debug(f"[ASSISTANT] Direct text: {text_content[:200]}...")
                else:
                    text_content = str(message)
                    logger.debug(f"[ASSISTANT] Stringified message: {text_content[:200]}...")
                
                # Only add non-empty text content
                if text_content and text_content.strip():
                    all_assistant_messages.append(text_content)
                    logger.info(f"[ASSISTANT] Added message to collection (total: {len(all_assistant_messages)})")
                    
            elif message_type == "HumanMessage":
                logger.info(f"[HUMAN] Human message detected")
                if hasattr(message, 'content'):
                    logger.debug(f"[HUMAN] Content: {str(message.content)[:200]}...")
                    
            elif message_type == "SystemMessage":
                logger.info(f"[SYSTEM] System message detected")
                if hasattr(message, 'content'):
                    logger.debug(f"[SYSTEM] Content: {str(message.content)[:200]}...")
                    
            elif message_type == "ToolMessage":
                logger.info(f"[TOOL RESULT] Tool message detected")
                if hasattr(message, 'content'):
                    logger.debug(f"[TOOL RESULT] Content: {str(message.content)[:200]}...")
                if hasattr(message, 'tool_use_id'):
                    logger.debug(f"[TOOL RESULT] Tool use ID: {message.tool_use_id}")
                    
            elif message_type == "ThinkingMessage":
                logger.info(f"[THINKING] Claude is thinking...")
                if hasattr(message, 'content'):
                    # Log Claude's reasoning process
                    thinking_content = str(message.content)
                    logger.info(f"[THINKING] Reasoning: {thinking_content[:300]}...")
                    logger.debug(f"[THINKING] Full reasoning: {thinking_content}")
                    
            else:
                logger.info(f"[OTHER] Unknown message type: {message_type}")
                logger.debug(f"[OTHER] Message attributes: {dir(message)}")
        
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
