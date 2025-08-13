"""Claude service implementation using the real Claude Code SDK."""

import os
import uuid
from datetime import datetime
from typing import Any, AsyncGenerator, Dict, Optional

from claude_code_sdk import ClaudeCodeOptions, ClaudeSDKClient
from loguru import logger

from ..core.config import settings
from ..models.dto import QueryRequest, QueryResponse, StreamChunk
from ..models.errors import (AuthenticationError, RateLimitError, SDKError,
                             TimeoutError)


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
        system_prompt = """You are a report generation assistant for high SKUs retail brands operation manager with expertise in Odoo ERP operations.

## Core Capabilities

1. **Odoo ERP Integration**: You can generate Python code to interact with Odoo systems using JSON-RPC protocol. You have access to comprehensive templates in /home/yoan/projects/claude_code_api/odoo_templates/.

2. **Available Odoo Templates**:
   - odoo_connection.py - Base connection class with async/await
   - 02_crud_operations.py - Create, Read, Update, Delete operations
   - 03_search_and_filter.py - Search patterns and filtering
   - 04_product_management.py - Product operations
   - 05_sales_orders.py - Sales order management
   - 06_invoicing.py - Invoice handling
   - 07_batch_operations.py - Bulk operations
   - ODOO_API_GUIDE.md - Complete reference

## Odoo Operation Guidelines

When users request Odoo operations:
1. Use the Read tool to examine relevant templates
2. Generate complete, working Python scripts
3. Always use async/await patterns
4. Include proper error handling
5. Use search_read for efficiency
6. Handle authentication properly

## Key Odoo Models
- res.partner - Contacts (customers/suppliers)
- product.template - Products
- sale.order - Sales orders
- account.move - Invoices
- res.users - Users

## Important Notes
- Always authenticate before operations
- Computed fields can't be used in search domains
- Use 'consu' type for products if inventory module is not available
- Specify fields when reading to reduce data transfer
- Process records in batches of 50-100 for large operations

For retail operations and high SKU management, prioritize using Odoo's built-in capabilities for:
- Product catalog management
- Sales order processing
- Customer relationship management
- Inventory tracking (if available)
- Invoice generation

Use tools as much as possible. Generate Python code directly for Odoo operations instead of relying on MCP tools."""
        
        if conversation_id in self._sessions:
            messages = self._sessions[conversation_id].get("messages", [])
            if messages:
                system_prompt += "\n\nConversation history:\n"
                for msg in messages:
                    role = msg["role"].capitalize()
                    content = msg["content"]
                    system_prompt += f"{role}: {content}\n"
                system_prompt += "\nPlease respond to the following message while maintaining context from our conversation history."
        
        # Default tools including common MCP tools (explicitly exclude web search providers)
        default_tools = [
            # Basic Claude Code tools - Essential for Odoo template access
            "Read", "Write", "Edit", "MultiEdit",  # File operations for templates
            "Bash", "BashOutput", "KillBash",  # Execute Python scripts
            "Glob", "Grep", "LS",  # Navigate templates
            "TodoWrite", "ExitPlanMode", "NotebookEdit",
            "Task",  # For complex operations
            # Note: odoo_mcp is optional - we generate Python code directly
        ]

        # Strict allowlist to prevent accidental enabling of external search providers
        allowed_whitelist = set(default_tools)

        # Define disabled tool identifiers (case-insensitive match)
        disabled_exact = {"websearch", "webfetch"}
        disabled_prefixes = [
            "mcp__perplexity",
            "mcp__perplexity-ask",
            "mcp__firecrawl",
            "mcp__context7",
        ]

        def _is_disabled_tool(tool_name: str) -> bool:
            name_l = tool_name.lower()
            if name_l in disabled_exact:
                return True
            return any(name_l.startswith(prefix) for prefix in disabled_prefixes)
        
        # Compute allowed tools with enforced filtering and strict allowlist
        requested_tools = request.tools or default_tools
        filtered_allowed_tools = [
            t for t in requested_tools
            if (t in allowed_whitelist) and (not _is_disabled_tool(t))
        ]
        # If user provided only disallowed/unknown tools, fall back to safe defaults
        if not filtered_allowed_tools:
            filtered_allowed_tools = list(default_tools)

        # Build disallowed list by combining explicit disallowed and enforced blocks
        enforced_disallowed = [
            "WebSearch", "WebFetch",
            # Perplexity
            "mcp__perplexity", "mcp__perplexity-ask", "mcp__perplexity-ask__perplexity_ask",
            # Firecrawl
            "mcp__Firecrawl", "mcp__firecrawl",
            # Context7
            "mcp__context7",
        ]
        combined_disallowed = list({*(request.disallowed_tools or []), *enforced_disallowed})

        # Create options for this session
        options_dict = {
            "model": claude_model,  # Pass the mapped model
            "system_prompt": system_prompt,
            "max_turns": 100,  # Allow long conversations
            "max_thinking_tokens": request.max_tokens if request.max_tokens <= 32000 else 32000,
            "allowed_tools": filtered_allowed_tools
        }
        
        # Add MCP servers configuration if provided, otherwise use from settings
        if request.mcp_servers:
            options_dict["mcp_servers"] = request.mcp_servers
        elif settings.mcp_servers:
            options_dict["mcp_servers"] = settings.mcp_servers
        
        # Add disallowed tools (explicit + enforced)
        if combined_disallowed:
            options_dict["disallowed_tools"] = combined_disallowed

        dropped = [t for t in requested_tools if _is_disabled_tool(t)]
        if dropped:
            logger.info(f"Filtered disallowed tools from allowed list: {dropped}")
        
        options = ClaudeCodeOptions(**options_dict)
        
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
            tools_used = []
            tool_details = []  # Store detailed tool information
            
            # Use Claude Code SDK with proper connection handling
            async with client:
                # Send the query
                await client.query(request.prompt)
                logger.info("Query sent to Claude. Awaiting response...")
                
                # Collect the response and track tool usage
                async for message in client.receive_response():
                    # Log the message type for debugging
                    message_type = type(message).__name__
                    logger.debug(f"Received message type: {message_type}")
                    
                    # Check for AssistantMessage with content
                    if message_type == 'AssistantMessage' and hasattr(message, 'content'):
                        # Process each content block
                        for block in message.content:
                            block_str = str(block)
                            logger.debug(f"Processing block: {block_str[:200]}")
                            
                            # Check if it's a ToolUseBlock
                            if 'ToolUseBlock' in block_str:
                                # Extract tool info from the string representation
                                # Format: ToolUseBlock(id='...', name='tool_name', input={...})
                                try:
                                    # Extract name
                                    name_start = block_str.find("name='") + 6
                                    if name_start > 5:
                                        name_end = block_str.find("'", name_start)
                                        tool_name = block_str[name_start:name_end]
                                    else:
                                        # Try with double quotes
                                        name_start = block_str.find('name="') + 6
                                        name_end = block_str.find('"', name_start)
                                        tool_name = block_str[name_start:name_end]
                                    
                                    # Extract id
                                    id_start = block_str.find("id='") + 4
                                    if id_start > 3:
                                        id_end = block_str.find("'", id_start)
                                        tool_id = block_str[id_start:id_end]
                                    else:
                                        tool_id = None
                                    
                                    if tool_name and tool_name not in tools_used:
                                        tools_used.append(tool_name)
                                        tool_details.append({
                                            "tool": tool_name,
                                            "id": tool_id,
                                            "timestamp": datetime.utcnow().isoformat()
                                        })
                                        logger.info(f"🔧 Tool used: {tool_name} (ID: {tool_id})")
                                except Exception as e:
                                    logger.debug(f"Error parsing tool block: {e}")
                            
                            # Check if it's a TextBlock
                            elif 'TextBlock' in block_str:
                                # Extract text from TextBlock(text="...")
                                try:
                                    text_start = block_str.find('text="') + 6
                                    if text_start > 5:
                                        text_end = block_str.find('")', text_start)
                                        if text_end == -1:
                                            text_end = len(block_str) - 2
                                        text_content = block_str[text_start:text_end]
                                        # Unescape basic sequences
                                        text_content = text_content.replace('\\n', '\n').replace('\\t', '\t').replace("\\'", "'").replace('\\"', '"')
                                        full_response += text_content
                                except Exception as e:
                                    logger.debug(f"Error parsing text block: {e}")
                    
                    # Also check for system messages and result messages
                    elif message_type == 'ResultMessage' and hasattr(message, 'result'):
                        # The final result contains the full response
                        if not full_response:
                            full_response = message.result
                        logger.debug(f"Result message received with {len(message.result)} chars")
            
            # Store in session
            self._sessions[conversation_id]["messages"].extend([
                {"role": "user", "content": request.prompt, "timestamp": datetime.utcnow().isoformat()},
                {"role": "assistant", "content": full_response, "timestamp": datetime.utcnow().isoformat()}
            ])
            
            logger.info(f"Query completed successfully for conversation {conversation_id}")
            logger.info(f"Total tools used: {len(tools_used)} - {tools_used}")
            
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
                    "tools_used": tools_used,  # Return the actual tools used, not the allowed tools
                    "tool_details": tool_details if tool_details else None,  # Include detailed tool information
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
