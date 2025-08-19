"""Minimal Claude service implementation using Claude Code SDK."""

import os
import logging
from claude_code_sdk import ClaudeCodeOptions, query, ResultMessage, AssistantMessage, SystemMessage
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
        tool_uses = []
        
        async for message in query(prompt=request.prompt, options=options):
            message_count += 1
            message_type = type(message).__name__
            
            if isinstance(message, SystemMessage):
                logger.info(f"[Message {message_count}] SYSTEM - Subtype: {message.subtype}")
                if message.subtype == 'init':
                    data = message.data
                    logger.info(f"  Session ID: {data.get('session_id')}")
                    logger.info(f"  Model: {data.get('model')}")
                    logger.info(f"  Available tools: {len(data.get('tools', []))} tools")
                    logger.debug(f"  Tools: {data.get('tools', [])[:5]}...")  # Show first 5 tools
                    if data.get('mcp_servers'):
                        logger.info(f"  MCP servers: {data.get('mcp_servers')}")
                
            elif isinstance(message, AssistantMessage):
                logger.info(f"[Message {message_count}] ASSISTANT - {len(message.content)} content blocks")
                
                text_content = []
                for i, block in enumerate(message.content):
                    block_type = type(block).__name__
                    
                    if block_type == 'TextBlock':
                        text = block.text
                        text_content.append(text)
                        logger.info(f"  Block {i+1}: TEXT - {text[:100]}...")
                        
                    elif block_type == 'ThinkingBlock':
                        thinking = block.thinking
                        logger.info(f"  Block {i+1}: THINKING")
                        logger.info(f"    Reasoning: {thinking[:200]}...")
                        logger.debug(f"    Full thinking: {thinking}")
                        
                    elif block_type == 'ToolUseBlock':
                        tool_uses.append({
                            'id': block.id,
                            'name': block.name,
                            'input': block.input
                        })
                        logger.info(f"  Block {i+1}: TOOL USE - {block.name}")
                        logger.info(f"    Tool ID: {block.id}")
                        logger.debug(f"    Input: {str(block.input)[:200]}...")
                        
                    elif block_type == 'ToolResultBlock':
                        logger.info(f"  Block {i+1}: TOOL RESULT")
                        logger.info(f"    Tool use ID: {block.tool_use_id}")
                        logger.info(f"    Is error: {block.is_error}")
                        if block.content:
                            content_preview = str(block.content)[:200] if block.content else "None"
                            logger.debug(f"    Content: {content_preview}...")
                    else:
                        logger.warning(f"  Block {i+1}: Unknown block type: {block_type}")
                
                # Combine text blocks for response
                if text_content:
                    combined_text = '\n'.join(text_content)
                    all_assistant_messages.append(combined_text)
                    logger.info(f"  Total text collected: {len(combined_text)} chars")
                    
            elif isinstance(message, ResultMessage):
                logger.info(f"[Message {message_count}] RESULT - Subtype: {message.subtype}")
                logger.info(f"  Session ID: {message.session_id}")
                logger.info(f"  Duration: {message.duration_ms}ms (API: {message.duration_api_ms}ms)")
                logger.info(f"  Turns used: {message.num_turns}")
                logger.info(f"  Is error: {message.is_error}")
                
                if message.total_cost_usd:
                    logger.info(f"  Cost: ${message.total_cost_usd:.6f}")
                
                if message.usage:
                    usage = message.usage
                    logger.info(f"  Token usage:")
                    logger.info(f"    Input: {usage.get('input_tokens', 0)}")
                    logger.info(f"    Output: {usage.get('output_tokens', 0)}")
                    logger.info(f"    Cache read: {usage.get('cache_read_input_tokens', 0)}")
                    logger.info(f"    Cache creation: {usage.get('cache_creation_input_tokens', 0)}")
                
                if message.result:
                    response_text = message.result
                    logger.info(f"  Final response: {len(response_text)} chars")
                elif all_assistant_messages:
                    response_text = '\n\n'.join(all_assistant_messages)
                    logger.info(f"  Using concatenated messages: {len(response_text)} chars")
                    
                current_session_id = message.session_id
                
            else:
                # Handle any other message types
                logger.info(f"[Message {message_count}] {message_type}")
                logger.debug(f"  Content: {str(message)[:200]}...")
        
        logger.info(f"Query completed - Total messages: {message_count}, Tools used: {len(tool_uses)}")
        if tool_uses:
            for tool in tool_uses:
                logger.info(f"  - {tool['name']} (ID: {tool['id'][:8]}...)")
        
        # Ensure we have a response
        if response_text is None:
            response_text = "No response received from Claude"
            logger.warning("No response text received, using default message")
        
        if not current_session_id:
            # Generate a simple session ID if none provided
            import uuid
            current_session_id = str(uuid.uuid4())
            logger.info(f"Generated new session ID: {current_session_id}")
        
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