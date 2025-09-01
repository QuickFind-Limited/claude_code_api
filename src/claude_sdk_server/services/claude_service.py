"""Claude service implementation with bulletproof message processing."""

import re
import time
import uuid
import traceback
from typing import Any, Dict, List, Optional

from claude_code_sdk import (
    AssistantMessage,
    ClaudeCodeOptions,
    ResultMessage,
    SystemMessage,
    query,
)

from src.claude_sdk_server.models.dto import QueryRequest, QueryResponse
from src.claude_sdk_server.streaming import (
    AssistantMessageEvent,
    DecisionMadeEvent,
    PerformanceMetricEvent,
    QueryCompleteEvent,
    QueryErrorEvent,
    QueryStartEvent,
    SessionInitEvent,
    SystemMessageEvent,
    ThinkingInsightEvent,
    ThinkingStartEvent,
    TodoIdentifiedEvent,
    TokenUsageEvent,
    ToolErrorEvent,
    ToolResultEvent,
    ToolUseEvent,
    emit_event,
)
from src.claude_sdk_server.utils.logging_config import get_logger

logger = get_logger(__name__)


class ClaudeService:
    """Service for interacting with Claude Code SDK with bulletproof message processing."""

    def __init__(self):
        """Initialize the service with bulletproof logging formatters."""
        self.current_step = 1
        self.todos_extracted = []
        self.tools_used = []
        self.thinking_summary = None
        self._current_tool_uses = []
        self._formatting_errors = 0  # Track formatting errors
        self._raw_messages_sent = 0  # Track raw message fallbacks

    async def safe_emit_event(self, event, fallback_message: str = None):
        """Emit event with error handling and fallback."""
        try:
            await emit_event(event)
        except Exception as e:
            self._formatting_errors += 1
            logger.error(f"Failed to emit event {type(event).__name__}: {e}")
            
            # Try to emit a basic fallback event
            if fallback_message:
                try:
                    from src.claude_sdk_server.streaming import SystemMessageEvent
                    fallback_event = SystemMessageEvent(
                        message=fallback_message,
                        subtype="formatting_error",
                        system_data={"error": str(e), "original_event": type(event).__name__}
                    )
                    await emit_event(fallback_event)
                except Exception as fallback_error:
                    logger.error(f"Even fallback event failed: {fallback_error}")

    async def query(self, request: QueryRequest) -> QueryResponse:
        """Send a query to Claude using the SDK query function with bulletproof processing."""
        start_time = time.time()

        # Emit query start event with fallback
        try:
            prompt_words = len(request.prompt.split())
            await self.safe_emit_event(
                QueryStartEvent(
                    message=f"Processing request with {request.model}",
                    session_id=request.session_id,
                    prompt_length=len(request.prompt),
                    word_count=prompt_words,
                    model=request.model,
                    max_thinking_tokens=request.max_thinking_tokens,
                    session_resumed=bool(request.session_id),
                ),
                f"Query started with {request.model}"
            )
        except Exception as e:
            logger.error(f"Failed to process query start: {e}")
            prompt_words = 0

        # Safe logging with fallbacks
        try:
            logger.info("\n" + "=" * 80)
            self._safe_log_user_friendly("🚀", "Query", 
                f"{request.prompt[:100]}..." if len(request.prompt) > 100 else request.prompt)
            logger.info("=" * 80)

            if request.session_id:
                self._safe_log_indented("Session", request.session_id[:8] + "...")
            
            self._safe_log_indented("Input", f"{prompt_words} words, {len(request.prompt)} characters")
            
            if request.max_thinking_tokens and request.max_thinking_tokens > 0:
                self._safe_log_indented("Mode", f"Deep thinking enabled ({request.max_thinking_tokens:,} tokens)")
        except Exception as e:
            logger.error(f"Failed to log query start: {e}")

        options = ClaudeCodeOptions(
            resume=request.session_id,
            max_turns=request.max_turns,
            permission_mode="bypassPermissions",
            model=request.model,
            max_thinking_tokens=request.max_thinking_tokens,
            system_prompt=request.system_prompt,
        )

        # Initialize tracking variables
        response_text: Optional[str] = None
        current_session_id: Optional[str] = request.session_id
        message_count = 0
        all_assistant_messages: List[str] = []
        tool_uses: List[Dict[str, Any]] = []

        try:
            async for message in query(prompt=request.prompt, options=options):
                message_count += 1
                try:
                    await self._bulletproof_process_message(
                        message, message_count, all_assistant_messages, tool_uses
                    )
                except Exception as e:
                    logger.error(f"Failed to process message {message_count}: {e}")
                    # Try to extract basic content even if processing fails
                    await self._extract_basic_content(message, all_assistant_messages)

                # Handle final result
                if isinstance(message, ResultMessage):
                    try:
                        response_text, current_session_id = await self._bulletproof_process_result_message(
                            message, all_assistant_messages
                        )
                    except Exception as e:
                        logger.error(f"Failed to process result message: {e}")
                        # Fallback: use collected messages
                        if all_assistant_messages:
                            response_text = "\n\n".join(all_assistant_messages)
                        current_session_id = getattr(message, 'session_id', current_session_id)

        except Exception as e:
            logger.error(f"Failed to process Claude query: {e}", exc_info=True)
            response_text = f"Error processing query: {str(e)}"

            # Emit error event with fallback
            await self.safe_emit_event(
                QueryErrorEvent(
                    message=f"Query failed: {str(e)}",
                    session_id=current_session_id or request.session_id,
                    error_type=type(e).__name__,
                    error_details=str(e),
                    stack_trace=traceback.format_exc(),
                ),
                f"Query failed: {str(e)}"
            )

        # Performance logging with error handling
        total_duration = time.time() - start_time
        try:
            logger.performance("claude_query", total_duration)
        except Exception as e:
            logger.error(f"Failed to log performance: {e}")

        # Emit performance metric event with fallback
        await self.safe_emit_event(
            PerformanceMetricEvent(
                message=f"Query completed in {total_duration:.2f}s",
                session_id=current_session_id or request.session_id,
                operation="claude_query",
                duration=total_duration,
            ),
            f"Query completed in {total_duration:.2f}s"
        )

        # Safe final summary logging
        try:
            self._safe_log_query_summary(message_count, tool_uses, response_text, total_duration)
        except Exception as e:
            logger.error(f"Failed to log query summary: {e}")

        # Ensure we have a response and session ID
        response_text = response_text or "No response received from Claude"
        current_session_id = current_session_id or str(uuid.uuid4())

        # Emit completion event if successful
        if response_text and not response_text.startswith("Error processing query:"):
            await self.safe_emit_event(
                QueryCompleteEvent(
                    message="Query completed successfully",
                    session_id=current_session_id,
                    duration_seconds=total_duration,
                    response_length=len(response_text),
                    response_words=len(response_text.split()) if response_text else 0,
                ),
                "Query completed successfully"
            )

        # Log statistics about processing issues
        if self._formatting_errors > 0 or self._raw_messages_sent > 0:
            logger.warning(f"Processing completed with {self._formatting_errors} formatting errors "
                         f"and {self._raw_messages_sent} raw message fallbacks")

        return QueryResponse(response=response_text, session_id=current_session_id)

    async def _extract_basic_content(self, message: Any, all_assistant_messages: List[str]):
        """Extract basic content from message even if advanced processing fails."""
        try:
            self._raw_messages_sent += 1
            
            if isinstance(message, AssistantMessage):
                # Try to extract text content at minimum
                text_parts = []
                
                for block in getattr(message, 'content', []):
                    try:
                        # Try different ways to get text content
                        if hasattr(block, 'text'):
                            text_parts.append(str(block.text))
                        elif hasattr(block, 'thinking'):
                            text_parts.append(f"[Thinking: {str(block.thinking)[:200]}...]")
                        elif hasattr(block, 'name'):  # Tool use
                            text_parts.append(f"[Tool: {block.name}]")
                        else:
                            text_parts.append(f"[Content: {str(block)[:100]}...]")
                    except Exception as e:
                        logger.error(f"Failed to extract content from block: {e}")
                        text_parts.append("[Content extraction failed]")
                
                if text_parts:
                    combined_text = "\n".join(text_parts)
                    all_assistant_messages.append(combined_text)
                    logger.info(f"Raw content extracted: {len(combined_text)} characters")
                    
                    # Try to emit a basic event
                    await self.safe_emit_event(
                        AssistantMessageEvent(
                            message="Assistant message (raw extraction)",
                            content_length=len(combined_text),
                            block_count=len(getattr(message, 'content', [])),
                            has_text=bool(text_parts),
                            has_thinking=any("Thinking:" in part for part in text_parts),
                            has_tools=any("Tool:" in part for part in text_parts),
                            full_content=combined_text,
                        ),
                        f"Assistant message with {len(combined_text)} characters"
                    )
                    
        except Exception as e:
            logger.error(f"Even basic content extraction failed: {e}")

    async def _bulletproof_process_message(
        self,
        message: Any,
        message_count: int,
        all_assistant_messages: List[str],
        tool_uses: List[Dict[str, Any]],
    ) -> None:
        """Process a single message with comprehensive error handling."""
        message_type = type(message).__name__

        try:
            if isinstance(message, SystemMessage):
                await self._bulletproof_process_system_message(message, message_count)
            elif isinstance(message, AssistantMessage):
                await self._bulletproof_process_assistant_message(
                    message, message_count, all_assistant_messages, tool_uses
                )
            elif isinstance(message, ResultMessage):
                # ResultMessage is handled in the main query method
                pass
            else:
                logger.debug(f"Received unknown message type: {message_type}")
                # Emit raw event for unknown types
                await self.safe_emit_event(
                    SystemMessageEvent(
                        message=f"Unknown message type: {message_type}",
                        subtype="unknown",
                        system_data={"message_type": message_type, "content": str(message)[:200]}
                    ),
                    f"Unknown message: {message_type}"
                )
        except Exception as e:
            logger.error(f"Failed to process message of type {message_type}: {e}")
            # Fallback: try to extract any useful content
            await self._extract_basic_content(message, all_assistant_messages)

    async def _bulletproof_process_system_message(
        self, message: SystemMessage, message_count: int
    ) -> None:
        """Process system messages with comprehensive error handling."""
        try:
            subtype = getattr(message, 'subtype', 'unknown')
            data = getattr(message, 'data', {})
            
            if subtype == "init":
                if isinstance(data, dict):
                    try:
                        logger.info("\n" + "-" * 60)
                        self._safe_log_user_friendly("🔧", "Session", "Initializing Claude session")
                        logger.info("-" * 60)

                        tools_count = 0
                        tool_names = []
                        mcp_servers_count = 0
                        server_names = []

                        # Safe extraction of tools info
                        try:
                            if data.get("tools"):
                                tools = data.get("tools", [])
                                tools_count = len(tools) if isinstance(tools, list) else 0
                                tool_names = []
                                for t in tools[:10]:  # Limit to 10
                                    try:
                                        if isinstance(t, dict):
                                            tool_names.append(t.get("name", "Unknown"))
                                        else:
                                            tool_names.append(str(t)[:20])  # Limit length
                                    except Exception:
                                        tool_names.append("Unknown")
                                
                                self._safe_log_indented("Tools", f"{tools_count} tools available")
                        except Exception as e:
                            logger.error(f"Failed to process tools info: {e}")

                        # Safe extraction of MCP servers info
                        try:
                            if data.get("mcp_servers"):
                                servers = data.get("mcp_servers", [])
                                if isinstance(servers, list) and servers:
                                    mcp_servers_count = len(servers)
                                    server_names = []
                                    for s in servers[:10]:  # Limit to 10
                                        try:
                                            if isinstance(s, dict):
                                                server_names.append(s.get("name", "Unknown"))
                                            else:
                                                server_names.append(str(s)[:20])  # Limit length
                                        except Exception:
                                            server_names.append("Unknown")
                                    
                                    self._safe_log_indented("MCP", f"{len(servers)} servers: {', '.join(server_names)}")
                        except Exception as e:
                            logger.error(f"Failed to process MCP servers info: {e}")

                        logger.info("-" * 60 + "\n")

                        # Emit session init event with fallback
                        await self.safe_emit_event(
                            SessionInitEvent(
                                message="Claude session initialized",
                                tools_available=tools_count,
                                tool_names=tool_names,
                                mcp_servers=mcp_servers_count,
                                server_names=server_names,
                            ),
                            "Claude session initialized"
                        )
                        
                    except Exception as e:
                        logger.error(f"Failed to process init data: {e}")
                        self._safe_log_user_friendly("🔧", "Setup", "Session initialized (with errors)")
                        await self.safe_emit_event(
                            SessionInitEvent(message="Session initialized with processing errors"),
                            "Session initialized"
                        )
                else:
                    self._safe_log_user_friendly("🔧", "Setup", "Session initialized")
                    await self.safe_emit_event(
                        SessionInitEvent(message="Session initialized"),
                        "Session initialized"
                    )
            else:
                # Other system messages - keep minimal
                logger.debug(f"System message - subtype: {subtype}")
                await self.safe_emit_event(
                    SystemMessageEvent(
                        message=f"System message: {subtype}",
                        subtype=subtype,
                        system_data=data if isinstance(data, (dict, str, int, float)) else str(data)[:200],
                    ),
                    f"System message: {subtype}"
                )
                
        except Exception as e:
            logger.error(f"Failed to process system message: {e}")
            await self.safe_emit_event(
                SystemMessageEvent(
                    message="System message processing failed",
                    subtype="error",
                    system_data={"error": str(e)}
                ),
                "System message processing failed"
            )

    async def _bulletproof_process_assistant_message(
        self,
        message: AssistantMessage,
        message_count: int,
        all_assistant_messages: List[str],
        tool_uses: List[Dict[str, Any]],
    ) -> None:
        """Process assistant messages with bulletproof error handling."""
        logger.debug(f"Processing assistant message {message_count}")

        text_content: List[str] = []
        has_text = False
        has_thinking = False
        has_tools = False
        content_blocks = []

        try:
            content_blocks = getattr(message, 'content', [])
        except Exception as e:
            logger.error(f"Failed to get message content: {e}")

        for i, block in enumerate(content_blocks):
            try:
                block_type = type(block).__name__

                # Text block processing with fallbacks
                if block_type == "TextBlock" or hasattr(block, "text"):
                    try:
                        text = getattr(block, "text", str(block))
                        text_content.append(text)
                        
                        # Safe text logging
                        if text.strip():
                            try:
                                self._safe_log_text_content(text)
                            except Exception as e:
                                logger.error(f"Failed to log text content: {e}")
                        
                        has_text = True
                    except Exception as e:
                        logger.error(f"Failed to process text block: {e}")
                        text_content.append("[Text processing failed]")
                        has_text = True

                # Thinking block processing with fallbacks
                elif block_type == "ThinkingBlock" or hasattr(block, "thinking"):
                    try:
                        thinking = getattr(block, "thinking", "")
                        signature = getattr(block, "signature", "")
                        await self._bulletproof_log_thinking_block(thinking, signature)
                        has_thinking = True
                    except Exception as e:
                        logger.error(f"Failed to process thinking block: {e}")
                        # Add raw thinking content
                        try:
                            raw_thinking = str(getattr(block, "thinking", ""))[:500]
                            text_content.append(f"[Thinking: {raw_thinking}...]")
                            has_thinking = True
                        except Exception:
                            text_content.append("[Thinking block processing failed]")

                # Tool use block processing with fallbacks
                elif block_type == "ToolUseBlock" or hasattr(block, "name"):
                    try:
                        await self._bulletproof_log_tool_use(block, tool_uses)
                        has_tools = True
                    except Exception as e:
                        logger.error(f"Failed to process tool use block: {e}")
                        # Add basic tool info
                        try:
                            tool_name = getattr(block, "name", "Unknown")
                            tool_id = getattr(block, "id", "unknown")
                            text_content.append(f"[Tool: {tool_name} ({tool_id})]")
                            has_tools = True
                        except Exception:
                            text_content.append("[Tool use processing failed]")

                # Tool result block processing with fallbacks  
                elif block_type == "ToolResultBlock" or hasattr(block, "tool_use_id"):
                    try:
                        await self._bulletproof_log_tool_result(block)
                        has_tools = True
                    except Exception as e:
                        logger.error(f"Failed to process tool result block: {e}")
                        # Add basic result info
                        try:
                            tool_use_id = getattr(block, "tool_use_id", "unknown")
                            is_error = getattr(block, "is_error", False)
                            status = "❌" if is_error else "✅"
                            text_content.append(f"[Tool Result {tool_use_id}: {status}]")
                            has_tools = True
                        except Exception:
                            text_content.append("[Tool result processing failed]")

                else:
                    logger.debug(f"Unknown block type in position {i}: {block_type}")
                    # Try to extract any content
                    try:
                        block_str = str(block)[:200]
                        text_content.append(f"[Unknown block: {block_str}...]")
                    except Exception:
                        text_content.append(f"[Unknown block type: {block_type}]")

            except Exception as e:
                logger.error(f"Failed to process block {i} of type {type(block).__name__}: {e}")
                text_content.append(f"[Block {i} processing failed]")

        # Emit assistant message event with fallback
        combined_text = "\n".join(text_content) if text_content else ""
        
        await self.safe_emit_event(
            AssistantMessageEvent(
                message=f"Assistant message with {len(content_blocks)} blocks",
                content_length=len(combined_text),
                block_count=len(content_blocks),
                has_text=has_text,
                has_thinking=has_thinking,
                has_tools=has_tools,
                full_content=combined_text,
            ),
            f"Assistant message: {len(combined_text)} chars"
        )

        # Always save text content
        if combined_text.strip():
            all_assistant_messages.append(combined_text)
            logger.debug(f"Assistant text collected: {len(combined_text)} characters")

    def _safe_log_text_content(self, text: str):
        """Safely log text content with error handling."""
        try:
            lines = text.strip().split("\n")
            for line in lines:
                line_stripped = line.strip()
                if line_stripped:
                    if line.startswith("#"):
                        self._safe_log_user_friendly("📝", "Response", line.strip("# "))
                    elif line.startswith("**") and line.endswith("**"):
                        self._safe_log_user_friendly("💡", "Point", line.strip("*"))
                    elif line.startswith("-") or line.startswith("•"):
                        self._safe_log_indented("", line)
                    else:
                        if len(line_stripped) > 20:
                            display_line = line_stripped[:120] + "..." if len(line_stripped) > 120 else line_stripped
                            logger.info(f"   {display_line}")
        except Exception as e:
            logger.error(f"Failed to log text content: {e}")
            # Fallback: log first 200 chars
            try:
                logger.info(f"   {text[:200]}...")
            except Exception:
                logger.info("   [Text content logging failed]")

    async def _bulletproof_log_thinking_block(self, thinking: str, signature: str) -> None:
        """Log thinking/reasoning blocks with bulletproof error handling."""
        if not thinking or not thinking.strip():
            return

        # Emit thinking start event with fallback
        await self.safe_emit_event(
            ThinkingStartEvent(
                message="Analyzing your request...",
                signature=signature or "",
            ),
            "Analyzing your request..."
        )

        try:
            self._safe_log_user_friendly("🤔", "Thinking", "Analyzing your request...")
        except Exception as e:
            logger.error(f"Failed to log thinking start: {e}")

        # Extract insights with error handling
        try:
            todos, insights, decisions = self._safe_extract_thinking_insights(thinking)

            # Log TODOs with error handling
            for i, todo in enumerate(todos[:5], 1):
                try:
                    self._safe_log_user_friendly("📝", "TODO", f"{i}. {todo}")
                    self.todos_extracted.append(todo)

                    await self.safe_emit_event(
                        TodoIdentifiedEvent(
                            message=f"TODO identified: {todo}",
                            todo_content=todo,
                            priority=min(5, 6 - i),
                            sequence_number=i,
                        ),
                        f"TODO: {todo[:50]}..."
                    )
                except Exception as e:
                    logger.error(f"Failed to process TODO {i}: {e}")

            # Log insights with error handling
            for insight in insights[:3]:
                try:
                    self._safe_log_user_friendly("💡", "Insight", insight)

                    await self.safe_emit_event(
                        ThinkingInsightEvent(
                            message=f"Insight: {insight}",
                            insight_type="insight",
                            content=insight,
                            priority=3,
                        ),
                        f"Insight: {insight[:50]}..."
                    )
                except Exception as e:
                    logger.error(f"Failed to process insight: {e}")

            # Log decisions with error handling
            for decision in decisions[:2]:
                try:
                    self._safe_log_user_friendly("⚡", "Decision", decision)

                    await self.safe_emit_event(
                        DecisionMadeEvent(
                            message=f"Decision: {decision}",
                            decision_content=decision,
                        ),
                        f"Decision: {decision[:50]}..."
                    )
                except Exception as e:
                    logger.error(f"Failed to process decision: {e}")

            # Store summary
            self.thinking_summary = {
                "todos_count": len(todos),
                "insights_count": len(insights),
                "decisions_count": len(decisions),
            }

        except Exception as e:
            logger.error(f"Failed to extract thinking insights: {e}")
            # Fallback: just log that thinking occurred
            try:
                thinking_preview = thinking[:200] + "..." if len(thinking) > 200 else thinking
                logger.info(f"   Thinking content: {thinking_preview}")
            except Exception:
                logger.info("   [Thinking content extraction failed]")

    def _safe_extract_thinking_insights(self, thinking: str) -> tuple[List[str], List[str], List[str]]:
        """Extract structured insights from thinking text with comprehensive error handling."""
        todos = []
        insights = []
        decisions = []

        try:
            lines = thinking.split("\n") if isinstance(thinking, str) else []

            for line in lines:
                try:
                    line = line.strip() if isinstance(line, str) else str(line).strip()
                    if not line or len(line) < 10:
                        continue

                    # Safe regex matching
                    try:
                        # Extract TODOs and action items
                        if re.search(r"\b(todo|need to|should|must|have to|will)\b", line, re.IGNORECASE):
                            if re.search(r"\b(I need to|I should|I must|I will|Let me|I have to)\b", line, re.IGNORECASE):
                                todo = re.sub(r"^(I need to|I should|I must|I will|Let me|I have to)\s*", "", line, flags=re.IGNORECASE)
                                if len(todo) > 5:
                                    todos.append(todo.capitalize()[:200])  # Limit length

                        # Extract insights
                        elif re.search(r"\b(understand|realize|notice|see that|appears|seems|indicates)\b", line, re.IGNORECASE):
                            if len(line) < 150:
                                insights.append(line.capitalize()[:200])

                        # Extract decisions
                        elif re.search(r"\b(decide|choose|select|go with|use|implement)\b", line, re.IGNORECASE):
                            if len(line) < 100:
                                decisions.append(line.capitalize()[:200])

                    except re.error as e:
                        logger.error(f"Regex error processing line: {e}")
                        continue
                        
                except Exception as e:
                    logger.error(f"Error processing thinking line: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error in thinking extraction: {e}")

        return todos[:10], insights[:5], decisions[:3]

    async def _bulletproof_log_tool_use(self, block: Any, tool_uses: List[Dict[str, Any]]) -> None:
        """Log tool usage with comprehensive error handling."""
        try:
            # Safe attribute extraction
            tool_id = getattr(block, 'id', f"unknown-{len(tool_uses)}")
            tool_name = getattr(block, 'name', 'Unknown')
            tool_input = getattr(block, 'input', {})
            
            tool_info = {"id": tool_id, "name": tool_name, "input": tool_input}
            tool_uses.append(tool_info)
            self._current_tool_uses.append(tool_info)
            self.tools_used.append(tool_name)

            # Safe logging
            try:
                if tool_name == "TodoWrite":
                    self._safe_log_user_friendly("📋", "Todo Update", "Managing task list")
                    formatted_input = self._safe_format_tool_input(tool_input, tool_name)
                    if formatted_input:
                        logger.info(formatted_input)
                else:
                    self._safe_log_user_friendly("🛠️", "Tool", tool_name)
                    formatted_input = self._safe_format_tool_input(tool_input, tool_name)
                    if formatted_input:
                        self._safe_log_indented("Input", formatted_input)
                    else:
                        self._safe_log_indented("Input", "No input details")
            except Exception as e:
                logger.error(f"Failed to log tool use details: {e}")
                self._safe_log_user_friendly("🛠️", "Tool", f"{tool_name} (logging error)")

            # Emit event with fallback
            formatted_input = self._safe_format_tool_input(tool_input, tool_name)
            await self.safe_emit_event(
                ToolUseEvent(
                    message=f"Using tool: {tool_name}",
                    tool_name=tool_name,
                    tool_id=tool_id,
                    input_summary=formatted_input if tool_name != "TodoWrite" else "Todo list update",
                    step_number=self.current_step,
                ),
                f"Using tool: {tool_name}"
            )

            self.current_step += 1

        except Exception as e:
            logger.error(f"Failed to process tool use: {e}")
            # Fallback logging
            try:
                tool_name = str(getattr(block, 'name', 'Unknown'))[:50]
                self._safe_log_user_friendly("🛠️", "Tool", f"{tool_name} (processing error)")
                self.current_step += 1
            except Exception:
                logger.error("Complete tool use processing failure")

    def _safe_format_tool_input(self, input_data: Any, tool_name: str) -> str:
        """Format tool input with comprehensive error handling."""
        try:
            if not input_data:
                return ""

            if isinstance(input_data, dict):
                try:
                    # Special handling for TodoWrite
                    if tool_name == "TodoWrite":
                        todos = input_data.get("todos", [])
                        if todos and isinstance(todos, list):
                            formatted_todos = []
                            for i, todo in enumerate(todos[:10]):  # Limit to 10
                                try:
                                    if isinstance(todo, dict):
                                        status = todo.get("status", "pending")
                                        content = str(todo.get("content", ""))[:100]
                                        status_emoji = {"pending": "⏳", "in_progress": "🔄", "completed": "✅"}.get(status, "⏳")
                                        formatted_todos.append(f"{status_emoji} {content}")
                                    else:
                                        formatted_todos.append(f"⏳ {str(todo)[:100]}")
                                except Exception:
                                    formatted_todos.append("⏳ [Todo formatting error]")
                            
                            if formatted_todos:
                                return "\n" + "\n".join(f"       {todo}" for todo in formatted_todos)
                        return "No valid todos"

                    # Other tool patterns with safe extraction
                    elif tool_name.lower() in ["bash", "shell", "command"]:
                        return str(input_data.get("command", str(input_data)))[:200]
                    elif tool_name.lower() in ["read", "file_read"]:
                        path = input_data.get('file_path', input_data.get('path', str(input_data)))
                        return f"File: {str(path)[:100]}"
                    elif tool_name.lower() in ["write", "file_write"]:
                        path = str(input_data.get("file_path", input_data.get("path", "")))[:50]
                        content_len = len(str(input_data.get("content", "")))
                        return f"File: {path} ({content_len} chars)"
                    elif tool_name.lower() in ["edit", "file_edit"]:
                        path = str(input_data.get("file_path", input_data.get("path", "")))[:100]
                        return f"Editing: {path}"
                    elif tool_name.lower() in ["grep", "search"]:
                        pattern = str(input_data.get("pattern", input_data.get("query", "")))[:50]
                        path = str(input_data.get("path", input_data.get("file", "")))[:50]
                        return f"Search '{pattern}' in {path}" if path else f"Search: '{pattern}'"
                    else:
                        # Generic safe formatting
                        key_fields = ["url", "path", "file_path", "query", "command", "pattern"]
                        for field in key_fields:
                            if field in input_data:
                                try:
                                    value = str(input_data[field])[:100]
                                    return f"{field}: {value}"
                                except Exception:
                                    continue
                        
                        # Last resort: show first few items
                        try:
                            items = list(input_data.items())[:2]
                            formatted_items = []
                            for k, v in items:
                                try:
                                    k_str = str(k)[:20]
                                    v_str = str(v)[:30]
                                    formatted_items.append(f"{k_str}: {v_str}")
                                except Exception:
                                    formatted_items.append(f"{k}: [error]")
                            return ", ".join(formatted_items)
                        except Exception:
                            return "Complex input data"
                            
                except Exception as e:
                    logger.error(f"Error formatting dict input: {e}")
                    return f"Input processing error: {str(e)[:50]}"
            else:
                # Non-dict input
                try:
                    input_str = str(input_data)[:200]
                    return input_str + "..." if len(str(input_data)) > 200 else input_str
                except Exception:
                    return "Input formatting error"
                    
        except Exception as e:
            logger.error(f"Complete input formatting failure: {e}")
            return "Input formatting failed"

    async def _bulletproof_log_tool_result(self, block: Any) -> None:
        """Log tool results with comprehensive error handling."""
        try:
            tool_use_id = getattr(block, "tool_use_id", "unknown")
            is_error = getattr(block, "is_error", False)
            content = getattr(block, "content", None)

            # Find tool name safely
            tool_name = "unknown"
            try:
                for tool_info in getattr(self, "_current_tool_uses", []):
                    if tool_info.get("id") == tool_use_id:
                        tool_name = tool_info.get("name", "unknown")
                        break
            except Exception as e:
                logger.error(f"Failed to find tool name: {e}")

            # Safe result logging
            try:
                if tool_name == "TodoWrite":
                    if not is_error:
                        self._safe_log_indented("Result", "✅ Todos updated successfully")
                    else:
                        self._safe_log_indented("Result", "❌ Failed to update todos")
                        if content:
                            try:
                                error_msg = self._safe_format_error_message(str(content))
                                self._safe_log_indented("", f"   {error_msg}")
                            except Exception:
                                self._safe_log_indented("", "   Error details unavailable")
                else:
                    if is_error:
                        self._safe_log_indented("Result", "❌ Error occurred")
                        if content:
                            try:
                                error_msg = self._safe_format_error_message(str(content))
                                self._safe_log_indented("", f"   {error_msg}")
                            except Exception:
                                self._safe_log_indented("", "   Error details unavailable")
                    else:
                        try:
                            result_summary = self._safe_format_tool_result(content)
                            if result_summary:
                                self._safe_log_indented("Result", f"✅ {result_summary}")
                            else:
                                self._safe_log_indented("Result", "✅ Completed successfully")
                        except Exception:
                            self._safe_log_indented("Result", "✅ Completed (details unavailable)")
                            
            except Exception as e:
                logger.error(f"Failed to log tool result details: {e}")

            # Emit events with error handling
            if is_error:
                await self.safe_emit_event(
                    ToolErrorEvent(
                        message=f"Tool {tool_name} failed",
                        tool_id=tool_use_id,
                        tool_name=tool_name,
                        error_message=str(content)[:500] if content else "Unknown error",
                    ),
                    f"Tool {tool_name} failed"
                )
            else:
                result_summary = self._safe_format_tool_result(content)
                await self.safe_emit_event(
                    ToolResultEvent(
                        message=f"Tool {tool_name} completed",
                        tool_id=tool_use_id,
                        tool_name=tool_name,
                        success=True,
                        result_summary=result_summary or "Completed successfully",
                        result_size=len(str(content)) if content else 0,
                    ),
                    f"Tool {tool_name} completed"
                )

        except Exception as e:
            logger.error(f"Failed to process tool result: {e}")

    def _safe_format_tool_result(self, content: Any) -> str:
        """Format tool result with comprehensive error handling."""
        try:
            if not content:
                return "No output"

            content_str = str(content)
            
            if len(content_str) < 50:
                return content_str
            elif len(content_str) < 200:
                lines = content_str.split("\n")
                if len(lines) == 1:
                    return content_str[:100] + "..."
                else:
                    return f"{lines[0][:50]}... ({len(lines)} lines total)"
            else:
                lines = content_str.split("\n")
                char_count = len(content_str)
                word_count = len(content_str.split())

                if lines and len(lines) > 1:
                    return f"Output: {len(lines)} lines, {word_count} words, {char_count} chars"
                else:
                    return f"Output: {word_count} words, {char_count} characters"
                    
        except Exception as e:
            logger.error(f"Failed to format tool result: {e}")
            return "Result formatting failed"

    def _safe_format_error_message(self, error: str) -> str:
        """Format error messages with error handling."""
        try:
            if not error:
                return "Unknown error"
                
            error_lines = str(error).split("\n")
            for line in error_lines:
                line = line.strip()
                if line and len(line) > 10 and not line.startswith(("Traceback", "  File")):
                    return line[:150] + "..." if len(line) > 150 else line
            return str(error)[:150] + "..." if len(str(error)) > 150 else str(error)
        except Exception as e:
            logger.error(f"Failed to format error message: {e}")
            return "Error message formatting failed"

    def _safe_log_user_friendly(self, emoji: str, category: str, message: str) -> None:
        """Log with comprehensive error handling."""
        try:
            safe_emoji = str(emoji)[:10] if emoji else "📌"
            safe_category = str(category)[:20] if category else "Message"
            safe_message = str(message)[:500] if message else ""
            formatted_message = f"{safe_emoji} {safe_category}: {safe_message}"
            logger.info(formatted_message)
        except Exception as e:
            logger.error(f"Failed to log user-friendly message: {e}")
            try:
                logger.info(f"Message: {str(message)[:100]}")
            except Exception:
                logger.info("Message logging completely failed")

    def _safe_log_indented(self, label: str, content: str) -> None:
        """Log indented content with error handling."""
        try:
            safe_label = str(label)[:50] if label else ""
            safe_content = str(content)[:200] if content else ""
            
            if safe_label:
                logger.info(f"   └─ {safe_label}: {safe_content}")
            else:
                logger.info(f"   {safe_content}")
        except Exception as e:
            logger.error(f"Failed to log indented content: {e}")

    async def _bulletproof_process_result_message(
        self, message: ResultMessage, all_assistant_messages: List[str]
    ) -> tuple[Optional[str], Optional[str]]:
        """Process the final result message with comprehensive error handling."""
        
        response_text = None
        session_id = None
        
        try:
            # Safe error status check
            is_error = getattr(message, 'is_error', False)
            if is_error:
                self._safe_log_user_friendly("❌", "Error", "Query completed with errors")
            else:
                self._safe_log_user_friendly("📋", "Processing", "Finalizing response...")

            # Safe session ID extraction
            try:
                session_id = getattr(message, 'session_id', None)
            except Exception as e:
                logger.error(f"Failed to get session ID: {e}")

            # Safe performance metrics logging
            try:
                duration_ms = getattr(message, 'duration_ms', None)
                if duration_ms:
                    duration_s = duration_ms / 1000
                    self._safe_log_indented("Duration", f"{duration_s:.2f}s total")
            except Exception as e:
                logger.error(f"Failed to log duration: {e}")

            try:
                num_turns = getattr(message, 'num_turns', None)
                if num_turns and num_turns > 1:
                    self._safe_log_indented("Turns", f"{num_turns} conversation turns")
            except Exception as e:
                logger.error(f"Failed to log turns: {e}")

            # Safe token usage logging
            try:
                usage = getattr(message, 'usage', None)
                if usage and isinstance(usage, dict):
                    input_tokens = usage.get("input_tokens", 0)
                    output_tokens = usage.get("output_tokens", 0) 
                    total_tokens = input_tokens + output_tokens

                    if total_tokens > 0:
                        self._safe_log_indented("Tokens", f"{total_tokens:,} total ({input_tokens:,} in, {output_tokens:,} out)")

                        # Safe cost logging
                        try:
                            total_cost_usd = getattr(message, 'total_cost_usd', None)
                            if total_cost_usd and total_cost_usd > 0.0001:
                                self._safe_log_indented("Cost", f"${total_cost_usd:.4f}")

                            # Emit token usage event
                            await self.safe_emit_event(
                                TokenUsageEvent(
                                    message=f"Token usage: {total_tokens:,} total",
                                    session_id=session_id,
                                    input_tokens=input_tokens,
                                    output_tokens=output_tokens,
                                    total_tokens=total_tokens,
                                    cost_usd=total_cost_usd,
                                ),
                                f"Used {total_tokens:,} tokens"
                            )
                        except Exception as e:
                            logger.error(f"Failed to process cost/emit token event: {e}")
            except Exception as e:
                logger.error(f"Failed to process usage: {e}")

            # Safe response text extraction
            try:
                response_text = getattr(message, 'result', None)
                if not response_text and all_assistant_messages:
                    response_text = "\n\n".join(all_assistant_messages)
            except Exception as e:
                logger.error(f"Failed to extract response text: {e}")
                if all_assistant_messages:
                    try:
                        response_text = "\n\n".join(all_assistant_messages)
                    except Exception:
                        response_text = "Response extraction failed"

        except Exception as e:
            logger.error(f"Failed to process result message: {e}")
            # Absolute fallback
            try:
                response_text = "\n\n".join(all_assistant_messages) if all_assistant_messages else "Processing failed"
                session_id = str(uuid.uuid4())
            except Exception:
                response_text = "Complete processing failure"
                session_id = str(uuid.uuid4())

        return response_text, session_id

    def _safe_log_query_summary(
        self,
        message_count: int,
        tool_uses: List[Dict[str, Any]], 
        response_text: Optional[str],
        duration: float,
    ) -> None:
        """Log a comprehensive summary with error handling."""
        try:
            logger.info("\n" + "=" * 80)
            self._safe_log_user_friendly("✅", "Complete", f"Query processed in {duration:.2f}s")
            logger.info("=" * 80)

            # Safe statistics logging
            try:
                if self.todos_extracted:
                    self._safe_log_indented("TODOs", f"Identified {len(self.todos_extracted)} action items")
            except Exception as e:
                logger.error(f"Failed to log TODO stats: {e}")

            try:
                if tool_uses:
                    todo_writes = sum(1 for tool in tool_uses if tool.get("name") == "TodoWrite")
                    other_tools = [tool.get("name", "Unknown") for tool in tool_uses if tool.get("name") != "TodoWrite"]

                    if todo_writes > 0:
                        self._safe_log_indented("Tasks", f"{todo_writes} todo list updates")

                    if other_tools:
                        unique_tools = list(set(other_tools))
                        tools_text = ", ".join(unique_tools[:10])  # Limit display
                        self._safe_log_indented("Tools", f"Used {len(other_tools)} tools: {tools_text}")
            except Exception as e:
                logger.error(f"Failed to log tool stats: {e}")

            try:
                if response_text:
                    word_count = len(response_text.split())
                    self._safe_log_indented("Response", f"Generated {word_count} words, {len(response_text)} characters")
                else:
                    self._safe_log_user_friendly("⚠️", "Warning", "No response text generated")
            except Exception as e:
                logger.error(f"Failed to log response stats: {e}")

            logger.info("=" * 80 + "\n")

        except Exception as e:
            logger.error(f"Failed to log query summary: {e}")

        # Always reset state
        try:
            self._reset_state()
        except Exception as e:
            logger.error(f"Failed to reset state: {e}")

    def _reset_state(self) -> None:
        """Reset internal state for the next query."""
        try:
            self.current_step = 1
            self.todos_extracted = []
            self.tools_used = []
            self.thinking_summary = None
            self._current_tool_uses = []
            self._formatting_errors = 0
            self._raw_messages_sent = 0
        except Exception as e:
            logger.error(f"Failed to reset state: {e}")


# Dependency injection function
_service_instance = None

def get_claude_service() -> ClaudeService:
    """Get or create Claude service instance."""
    global _service_instance
    if _service_instance is None:
        _service_instance = ClaudeService()
    return _service_instance
