"""Claude service implementation with real-time event streaming support."""

import re
import time
import uuid
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
    """Service for interacting with Claude Code SDK."""

    def __init__(self):
        """Initialize the service with beautiful logging formatters."""
        self.current_step = 1
        self.todos_extracted = []
        self.tools_used = []
        self.thinking_summary = None
        self._current_tool_uses = []  # Track current tool uses for result matching

    async def query(self, request: QueryRequest) -> QueryResponse:
        """Send a query to Claude using the SDK query function."""
        start_time = time.time()

        # Emit query start event
        prompt_words = len(request.prompt.split())
        await emit_event(
            QueryStartEvent(
                message=f"Processing request with {request.model}",
                session_id=request.session_id,
                prompt_length=len(request.prompt),
                word_count=prompt_words,
                model=request.model,
                max_thinking_tokens=request.max_thinking_tokens,
                session_resumed=bool(request.session_id),
            )
        )

        # Log query initiation with beautiful user-friendly formatting
        logger.info("\n" + "=" * 80)
        self._log_user_friendly(
            "🚀",
            "Query",
            f"{request.prompt[:100]}..."
            if len(request.prompt) > 100
            else request.prompt,
        )
        logger.info("=" * 80)

        if request.session_id:
            self._log_indented("Session", request.session_id[:8] + "...")

        self._log_indented(
            "Input", f"{prompt_words} words, {len(request.prompt)} characters"
        )

        if request.max_thinking_tokens and request.max_thinking_tokens > 0:
            self._log_indented(
                "Mode",
                f"Deep thinking enabled ({request.max_thinking_tokens:,} tokens)",
            )

        options = ClaudeCodeOptions(
            resume=request.session_id,
            max_turns=request.max_turns,
            permission_mode="bypassPermissions",
            model=request.model,
            max_thinking_tokens=request.max_thinking_tokens,
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
                await self._process_message(
                    message, message_count, all_assistant_messages, tool_uses
                )

                # Handle final result
                if isinstance(message, ResultMessage):
                    (
                        response_text,
                        current_session_id,
                    ) = await self._process_result_message(
                        message, all_assistant_messages
                    )

        except Exception as e:
            logger.error(f"Failed to process Claude query: {e}", exc_info=True)
            response_text = f"Error processing query: {str(e)}"

            # Emit error event
            await emit_event(
                QueryErrorEvent(
                    message=f"Query failed: {str(e)}",
                    session_id=current_session_id or request.session_id,
                    error_type=type(e).__name__,
                    error_details=str(e),
                    stack_trace=None,  # Could add traceback if needed
                )
            )

        # Performance logging
        total_duration = time.time() - start_time
        logger.performance("claude_query", total_duration)

        # Emit performance metric event
        await emit_event(
            PerformanceMetricEvent(
                message=f"Query completed in {total_duration:.2f}s",
                session_id=current_session_id or request.session_id,
                operation="claude_query",
                duration=total_duration,
            )
        )

        # Log final summary
        self._log_query_summary(message_count, tool_uses, response_text, total_duration)

        # Ensure we have a response and session ID
        response_text = response_text or "No response received from Claude"
        current_session_id = current_session_id or str(uuid.uuid4())

        # Emit completion event if successful
        if response_text and not response_text.startswith("Error processing query:"):
            await emit_event(
                QueryCompleteEvent(
                    message="Query completed successfully",
                    session_id=current_session_id,
                    duration_seconds=total_duration,
                    response_length=len(response_text),
                    response_words=len(response_text.split()),
                )
            )

        return QueryResponse(response=response_text, session_id=current_session_id)

    def _extract_thinking_insights(
        self, thinking: str
    ) -> tuple[List[str], List[str], List[str]]:
        """Extract structured insights from thinking text."""
        todos = []
        insights = []
        decisions = []

        lines = thinking.split("\n")

        for line in lines:
            line = line.strip()
            if not line or len(line) < 10:
                continue

            # Extract TODOs and action items
            if re.search(
                r"\b(todo|need to|should|must|have to|will)\b", line, re.IGNORECASE
            ):
                if re.search(
                    r"\b(I need to|I should|I must|I will|Let me|I have to)\b",
                    line,
                    re.IGNORECASE,
                ):
                    # Clean up the TODO
                    todo = re.sub(
                        r"^(I need to|I should|I must|I will|Let me|I have to)\s*",
                        "",
                        line,
                        flags=re.IGNORECASE,
                    )
                    if len(todo) > 5:
                        todos.append(todo.capitalize())

            # Extract insights and analysis
            elif re.search(
                r"\b(understand|realize|notice|see that|appears|seems|indicates)\b",
                line,
                re.IGNORECASE,
            ):
                if len(line) < 150:  # Keep insights concise
                    insights.append(line.capitalize())

            # Extract decisions
            elif re.search(
                r"\b(decide|choose|select|go with|use|implement)\b", line, re.IGNORECASE
            ):
                if len(line) < 100:  # Keep decisions concise
                    decisions.append(line.capitalize())

        return todos[:10], insights[:5], decisions[:3]

    def _format_tool_input(self, input_data: Any, tool_name: str) -> str:
        """Format tool input in a user-friendly way based on tool type."""
        if not input_data:
            return ""

        if isinstance(input_data, dict):
            # Special handling for TodoWrite
            if tool_name == "TodoWrite":
                todos = input_data.get("todos", [])
                if todos:
                    formatted_todos = []
                    for i, todo in enumerate(todos, 1):
                        status_emoji = {
                            "pending": "⏳",
                            "in_progress": "🔄",
                            "completed": "✅",
                        }.get(todo.get("status", "pending"), "⏳")
                        content = todo.get("content", "")
                        formatted_todos.append(f"{status_emoji} {content}")
                    return "\n" + "\n".join(
                        f"       {todo}" for todo in formatted_todos
                    )
                return "No todos"

            # Format based on common tool patterns
            elif tool_name.lower() in ["bash", "shell", "command"]:
                return input_data.get("command", str(input_data))
            elif tool_name.lower() in ["read", "file_read"]:
                return f"File: {input_data.get('file_path', input_data.get('path', str(input_data)))}"
            elif tool_name.lower() in ["write", "file_write"]:
                path = input_data.get("file_path", input_data.get("path", ""))
                content_len = len(str(input_data.get("content", "")))
                return f"File: {path} ({content_len} chars)"
            elif tool_name.lower() in ["edit", "file_edit"]:
                path = input_data.get("file_path", input_data.get("path", ""))
                return f"Editing: {path}"
            elif tool_name.lower() in ["grep", "search"]:
                pattern = input_data.get("pattern", input_data.get("query", ""))
                path = input_data.get("path", input_data.get("file", ""))
                return (
                    f"Search '{pattern}' in {path}" if path else f"Search: '{pattern}'"
                )
            else:
                # Generic formatting for other tools
                key_fields = ["url", "path", "file_path", "query", "command", "pattern"]
                for field in key_fields:
                    if field in input_data:
                        value = str(input_data[field])
                        if len(value) > 50:
                            value = value[:50] + "..."
                        return f"{field}: {value}"

                # Fallback: show first few key-value pairs
                items = list(input_data.items())[:2]
                return ", ".join(
                    f"{k}: {str(v)[:30]}..." if len(str(v)) > 30 else f"{k}: {v}"
                    for k, v in items
                )
        else:
            # Non-dict input
            input_str = str(input_data)
            return input_str[:100] + "..." if len(input_str) > 100 else input_str

    def _format_tool_result(self, content: Any) -> str:
        """Format tool result in a concise, user-friendly way."""
        if not content:
            return "No output"

        content_str = str(content)

        # Handle different types of results
        if len(content_str) < 50:
            return content_str
        elif len(content_str) < 200:
            # Medium length - show with ellipsis
            lines = content_str.split("\n")
            if len(lines) == 1:
                return content_str[:100] + "..."
            else:
                return f"{lines[0]}... ({len(lines)} lines total)"
        else:
            # Long result - show summary
            lines = content_str.split("\n")
            char_count = len(content_str)
            word_count = len(content_str.split())

            if lines and len(lines) > 1:
                return f"Output: {len(lines)} lines, {word_count} words, {char_count} chars"
            else:
                return f"Output: {word_count} words, {char_count} characters"

    def _format_error_message(self, error: str) -> str:
        """Format error messages to be more user-friendly."""
        error_lines = error.split("\n")
        # Take first meaningful line
        for line in error_lines:
            line = line.strip()
            if line and len(line) > 10 and not line.startswith(("Traceback", "  File")):
                return line[:150] + "..." if len(line) > 150 else line
        return error[:150] + "..." if len(error) > 150 else error

    def _log_user_friendly(self, emoji: str, category: str, message: str) -> None:
        """Log a message with beautiful, consistent formatting for end users."""
        formatted_message = f"{emoji} {category}: {message}"
        logger.info(formatted_message)

    def _log_indented(self, label: str, content: str) -> None:
        """Log indented content for hierarchical display."""
        if label:
            logger.info(f"   └─ {label}: {content}")
        else:
            logger.info(f"   {content}")

    def _reset_state(self) -> None:
        """Reset internal state for the next query."""
        self.current_step = 1
        self.todos_extracted = []
        self.tools_used = []
        self.thinking_summary = None
        self._current_tool_uses = []

    async def _process_message(
        self,
        message: Any,
        message_count: int,
        all_assistant_messages: List[str],
        tool_uses: List[Dict[str, Any]],
    ) -> None:
        """Process a single message from Claude's response stream."""
        message_type = type(message).__name__

        if isinstance(message, SystemMessage):
            await self._process_system_message(message, message_count)
        elif isinstance(message, AssistantMessage):
            await self._process_assistant_message(
                message, message_count, all_assistant_messages, tool_uses
            )
        elif isinstance(message, ResultMessage):
            # ResultMessage is handled in the main query method
            pass
        else:
            logger.debug(f"Received unknown message type: {message_type}")

    async def _process_system_message(
        self, message: SystemMessage, message_count: int
    ) -> None:
        """Process system messages with beautiful, user-friendly logging."""
        if message.subtype == "init":
            data = message.data
            # Handle both dict and string data types
            if isinstance(data, dict):
                logger.info("\n" + "-" * 60)
                self._log_user_friendly("🔧", "Session", "Initializing Claude session")
                logger.info("-" * 60)

                tools_count = 0
                tool_names = []
                mcp_servers_count = 0
                server_names = []

                if data.get("tools"):
                    tools = data.get("tools", [])
                    tools_count = len(tools)
                    tool_names = [
                        t.get("name", "Unknown") if isinstance(t, dict) else str(t)
                        for t in tools[:10]
                    ]
                    self._log_indented("Tools", f"{tools_count} tools available")

                if data.get("mcp_servers"):
                    servers = data.get("mcp_servers", [])
                    if isinstance(servers, list) and servers:
                        mcp_servers_count = len(servers)
                        server_names = [
                            s.get("name", "Unknown") if isinstance(s, dict) else str(s)
                            for s in servers[:10]
                        ]
                        self._log_indented(
                            "MCP", f"{len(servers)} servers: {', '.join(server_names)}"
                        )

                logger.info("-" * 60 + "\n")

                # Emit session init event
                await emit_event(
                    SessionInitEvent(
                        message="Claude session initialized",
                        tools_available=tools_count,
                        tool_names=tool_names,
                        mcp_servers=mcp_servers_count,
                        server_names=server_names,
                    )
                )
            else:
                self._log_user_friendly("🔧", "Setup", "Session initialized")
                await emit_event(SessionInitEvent(message="Session initialized"))
        else:
            # Other system messages - keep minimal
            logger.debug(f"System message - subtype: {message.subtype}")
            await emit_event(
                SystemMessageEvent(
                    message=f"System message: {message.subtype}",
                    subtype=message.subtype,
                    system_data=getattr(message, "data", None),
                )
            )

    async def _process_assistant_message(
        self,
        message: AssistantMessage,
        message_count: int,
        all_assistant_messages: List[str],
        tool_uses: List[Dict[str, Any]],
    ) -> None:
        """Process assistant messages with clean, structured logging."""
        logger.debug(f"Processing assistant message with {len(message.content)} blocks")

        text_content: List[str] = []
        has_text = False
        has_thinking = False
        has_tools = False

        for block in message.content:
            block_type = type(block).__name__

            if block_type == "TextBlock" or hasattr(block, "text"):
                text = getattr(block, "text", str(block))
                text_content.append(text)

                # Log text content with nice formatting
                if text.strip():
                    # Format text with proper indentation and section headers
                    lines = text.strip().split("\n")
                    for line in lines:
                        if line.strip():
                            if line.startswith("#"):
                                # Section headers
                                self._log_user_friendly(
                                    "📝", "Response", line.strip("# ")
                                )
                            elif line.startswith("**") and line.endswith("**"):
                                # Bold sections
                                self._log_user_friendly("💡", "Point", line.strip("*"))
                            elif line.startswith("-") or line.startswith("•"):
                                # Bullet points
                                self._log_indented("", line)
                            else:
                                # Regular text - only log if substantial
                                if len(line.strip()) > 20:
                                    logger.info(
                                        f"   {line.strip()[:120]}..."
                                        if len(line.strip()) > 120
                                        else f"   {line.strip()}"
                                    )

                has_text = True

            elif block_type == "ThinkingBlock" or hasattr(block, "thinking"):
                thinking = getattr(block, "thinking", "")
                signature = getattr(block, "signature", "")
                await self._log_thinking_block(thinking, signature)
                has_thinking = True

            elif block_type == "ToolUseBlock" or hasattr(block, "name"):
                await self._log_tool_use(block, tool_uses)
                has_tools = True

            elif block_type == "ToolResultBlock" or hasattr(block, "tool_use_id"):
                await self._log_tool_result(block)
                has_tools = True

            else:
                logger.debug(f"Unknown block type: {block_type}")

        # Emit assistant message event
        combined_text = "\n".join(text_content) if text_content else ""
        await emit_event(
            AssistantMessageEvent(
                message=f"Assistant message with {len(message.content)} blocks",
                content_length=len(combined_text),
                block_count=len(message.content),
                has_text=has_text,
                has_thinking=has_thinking,
                has_tools=has_tools,
            )
        )

        # Combine text blocks for response
        if text_content:
            all_assistant_messages.append(combined_text)
            logger.debug(f"Assistant text collected: {len(combined_text)} characters")

    async def _log_thinking_block(self, thinking: str, signature: str) -> None:
        """Log thinking/reasoning blocks with beautiful, streamable formatting."""
        if not thinking.strip():
            return

        # Emit thinking start event
        await emit_event(
            ThinkingStartEvent(
                message="Analyzing your request...",
                signature=signature,
            )
        )

        # Start thinking section
        self._log_user_friendly("🤔", "Thinking", "Analyzing your request...")

        # Extract and format key insights from thinking
        todos, insights, decisions = self._extract_thinking_insights(thinking)

        # Log TODOs with beautiful formatting
        if todos:
            for i, todo in enumerate(todos[:5], 1):  # Limit to 5 most important TODOs
                self._log_user_friendly("📝", "TODO", f"{i}. {todo}")
                self.todos_extracted.append(todo)

                # Emit TODO event
                await emit_event(
                    TodoIdentifiedEvent(
                        message=f"TODO identified: {todo}",
                        todo_content=todo,
                        priority=min(5, 6 - i),  # Higher priority for earlier todos
                        sequence_number=i,
                    )
                )

        # Log key insights
        if insights:
            for insight in insights[:3]:  # Top 3 insights
                self._log_user_friendly("💡", "Insight", insight)

                # Emit insight event
                await emit_event(
                    ThinkingInsightEvent(
                        message=f"Insight: {insight}",
                        insight_type="insight",
                        content=insight,
                        priority=3,
                    )
                )

        # Log key decisions
        if decisions:
            for decision in decisions[:2]:  # Top 2 decisions
                self._log_user_friendly("⚡", "Decision", decision)

                # Emit decision event
                await emit_event(
                    DecisionMadeEvent(
                        message=f"Decision: {decision}",
                        decision_content=decision,
                    )
                )

        # Store summary for final output
        self.thinking_summary = {
            "todos_count": len(todos),
            "insights_count": len(insights),
            "decisions_count": len(decisions),
        }

    async def _log_tool_use(self, block: Any, tool_uses: List[Dict[str, Any]]) -> None:
        """Log tool usage with beautiful, user-friendly formatting."""
        tool_info = {"id": block.id, "name": block.name, "input": block.input}
        tool_uses.append(tool_info)
        self._current_tool_uses.append(tool_info)  # Track for result matching
        self.tools_used.append(block.name)

        # Special formatting for TodoWrite
        if block.name == "TodoWrite":
            self._log_user_friendly("📋", "Todo Update", "Managing task list")
            formatted_input = self._format_tool_input(block.input, block.name)
            if formatted_input:
                logger.info(formatted_input)
        else:
            # Format other tool calls
            self._log_user_friendly("🛠️", "Tool", block.name)
            formatted_input = self._format_tool_input(block.input, block.name)
            if formatted_input:
                self._log_indented("Input", formatted_input)

        # Emit tool use event
        await emit_event(
            ToolUseEvent(
                message=f"Using tool: {block.name}",
                tool_name=block.name,
                tool_id=block.id,
                input_summary=formatted_input
                if block.name != "TodoWrite"
                else "Todo list update",
                step_number=self.current_step,
            )
        )

        # Track step progression
        self.current_step += 1

    async def _log_tool_result(self, block: Any) -> None:
        """Log tool results with beautiful, user-friendly formatting."""
        tool_use_id = getattr(block, "tool_use_id", "unknown")
        is_error = getattr(block, "is_error", False)
        content = getattr(block, "content", None)

        # Find tool name from tool_use_id if possible
        tool_name = "unknown"
        for tool_info in getattr(self, "_current_tool_uses", []):
            if tool_info.get("id") == tool_use_id:
                tool_name = tool_info.get("name", "unknown")
                break

        # Don't log TodoWrite results verbosely
        if tool_name == "TodoWrite":
            if not is_error:
                self._log_indented("Result", "✅ Todos updated successfully")
            else:
                self._log_indented("Result", "❌ Failed to update todos")
                if content:
                    error_msg = self._format_error_message(str(content))
                    self._log_indented("", f"   {error_msg}")
        else:
            if is_error:
                self._log_indented("Result", "❌ Error occurred")
                if content:
                    error_msg = self._format_error_message(str(content))
                    self._log_indented("", f"   {error_msg}")

                # Emit tool error event
                await emit_event(
                    ToolErrorEvent(
                        message=f"Tool {tool_name} failed",
                        tool_id=tool_use_id,
                        tool_name=tool_name,
                        error_message=str(content) if content else "Unknown error",
                    )
                )
            else:
                # Format result in a user-friendly way
                result_summary = self._format_tool_result(content)
                if result_summary:
                    self._log_indented("Result", f"✅ {result_summary}")
                else:
                    self._log_indented("Result", "✅ Completed successfully")

                # Emit tool result event
                await emit_event(
                    ToolResultEvent(
                        message=f"Tool {tool_name} completed",
                        tool_id=tool_use_id,
                        tool_name=tool_name,
                        success=True,
                        result_summary=result_summary or "Completed successfully",
                        result_size=len(str(content)) if content else 0,
                    )
                )

    async def _process_result_message(
        self, message: ResultMessage, all_assistant_messages: List[str]
    ) -> tuple[Optional[str], Optional[str]]:
        """Process the final result message with beautiful, user-friendly logging."""

        # Log completion status
        if message.is_error:
            self._log_user_friendly("❌", "Error", "Query completed with errors")
        else:
            self._log_user_friendly("📋", "Processing", "Finalizing response...")

        # Log performance metrics in a user-friendly way
        if message.duration_ms:
            duration_s = message.duration_ms / 1000
            self._log_indented("Duration", f"{duration_s:.2f}s total")

        if message.num_turns and message.num_turns > 1:
            self._log_indented("Turns", f"{message.num_turns} conversation turns")

        # Log token usage if available (user-friendly format)
        if message.usage and isinstance(message.usage, dict):
            usage = message.usage
            input_tokens = usage.get("input_tokens", 0)
            output_tokens = usage.get("output_tokens", 0)
            total_tokens = input_tokens + output_tokens

            if total_tokens > 0:
                self._log_indented(
                    "Tokens",
                    f"{total_tokens:,} total ({input_tokens:,} in, {output_tokens:,} out)",
                )

                # Emit token usage event
                await emit_event(
                    TokenUsageEvent(
                        message=f"Token usage: {total_tokens:,} total",
                        session_id=message.session_id,
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
                        total_tokens=total_tokens,
                        cost_usd=message.total_cost_usd,
                    )
                )

                # Show cost if available and reasonable
                if message.total_cost_usd and message.total_cost_usd > 0.0001:
                    self._log_indented("Cost", f"${message.total_cost_usd:.4f}")

        # Determine response text
        response_text = None
        if message.result:
            response_text = message.result
        elif all_assistant_messages:
            response_text = "\n\n".join(all_assistant_messages)

        return response_text, message.session_id

    def _log_query_summary(
        self,
        message_count: int,
        tool_uses: List[Dict[str, Any]],
        response_text: Optional[str],
        duration: float,
    ) -> None:
        """Log a beautiful, comprehensive summary of the query execution."""

        logger.info("\n" + "=" * 80)
        # Beautiful completion message
        self._log_user_friendly("✅", "Complete", f"Query processed in {duration:.2f}s")
        logger.info("=" * 80)

        # Summary statistics
        if self.todos_extracted:
            self._log_indented(
                "TODOs", f"Identified {len(self.todos_extracted)} action items"
            )

        if tool_uses:
            # Count TodoWrite separately
            todo_writes = sum(1 for tool in tool_uses if tool["name"] == "TodoWrite")
            other_tools = [
                tool["name"] for tool in tool_uses if tool["name"] != "TodoWrite"
            ]

            if todo_writes > 0:
                self._log_indented("Tasks", f"{todo_writes} todo list updates")

            if other_tools:
                unique_tools = set(other_tools)
                tools_text = ", ".join(unique_tools)
                self._log_indented(
                    "Tools", f"Used {len(other_tools)} tools: {tools_text}"
                )

        if response_text:
            word_count = len(response_text.split())
            self._log_indented(
                "Response",
                f"Generated {word_count} words, {len(response_text)} characters",
            )
        else:
            self._log_user_friendly("⚠️", "Warning", "No response text generated")

        logger.info("=" * 80 + "\n")

        # Reset state for next query
        self._reset_state()


# Dependency injection function
_service_instance = None


def get_claude_service() -> ClaudeService:
    """Get or create Claude service instance."""
    global _service_instance
    if _service_instance is None:
        _service_instance = ClaudeService()
    return _service_instance
