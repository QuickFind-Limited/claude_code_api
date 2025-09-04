"""Event data models for streaming real-time events from Claude SDK Server.

This module defines structured event models that capture all the beautiful log events
generated during Claude query processing, making them available for real-time streaming
to web clients, WebSocket connections, and API consumers.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Union
from uuid import uuid4

from pydantic import BaseModel, Field


class EventType(str, Enum):
    """Types of events that can be streamed."""

    # Query lifecycle events
    QUERY_START = "query_start"
    QUERY_COMPLETE = "query_complete"
    QUERY_ERROR = "query_error"

    # Processing events
    SESSION_INIT = "session_init"
    THINKING_START = "thinking_start"
    THINKING_INSIGHT = "thinking_insight"

    # Tool events
    TOOL_USE = "tool_use"
    TOOL_RESULT = "tool_result"
    TOOL_ERROR = "tool_error"

    # Progress events
    TODO_IDENTIFIED = "todo_identified"
    DECISION_MADE = "decision_made"
    STEP_PROGRESS = "step_progress"

    # System events
    SYSTEM_MESSAGE = "system_message"
    ASSISTANT_MESSAGE = "assistant_message"
    USER_MESSAGE = "user_message"

    # Performance events
    PERFORMANCE_METRIC = "performance_metric"
    TOKEN_USAGE = "token_usage"


class EventSeverity(str, Enum):
    """Severity levels for events."""

    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class BaseEvent(BaseModel):
    """Base event model with common fields."""

    id: str = Field(
        default_factory=lambda: str(uuid4()), description="Unique event identifier"
    )
    type: EventType = Field(..., description="Type of event")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Event timestamp"
    )
    session_id: Optional[str] = Field(None, description="Associated session ID")
    severity: EventSeverity = Field(EventSeverity.INFO, description="Event severity")
    message: str = Field(..., description="Human-readable event message")
    data: Optional[Dict[str, Any]] = Field(None, description="Additional event data")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }

    def dict(self, **kwargs):
        """Override dict method to handle datetime serialization."""
        data = super().dict(**kwargs)
        # Convert datetime to ISO format string
        if "timestamp" in data and isinstance(data["timestamp"], datetime):
            data["timestamp"] = data["timestamp"].isoformat()
        return data


class QueryStartEvent(BaseEvent):
    """Event fired when a Claude query starts processing."""

    type: Literal[EventType.QUERY_START] = EventType.QUERY_START
    prompt_length: int = Field(
        ..., description="Length of the input prompt in characters"
    )
    word_count: int = Field(..., description="Number of words in the prompt")
    model: str = Field(..., description="Claude model being used")
    max_thinking_tokens: Optional[int] = Field(
        None, description="Maximum thinking tokens allowed"
    )
    session_resumed: bool = Field(
        False, description="Whether this continues an existing session"
    )


class QueryCompleteEvent(BaseEvent):
    """Event fired when a Claude query completes successfully."""

    type: Literal[EventType.QUERY_COMPLETE] = EventType.QUERY_COMPLETE
    severity: Literal[EventSeverity.SUCCESS] = EventSeverity.SUCCESS
    duration_ms: Optional[int] = Field(
        None, description="Total processing duration in milliseconds"
    )
    duration_seconds: float = Field(
        ..., description="Total processing duration in seconds"
    )
    response_length: int = Field(
        ..., description="Length of the response in characters"
    )
    response_words: int = Field(..., description="Number of words in the response")
    num_turns: Optional[int] = Field(None, description="Number of conversation turns")
    total_cost_usd: Optional[float] = Field(None, description="Total cost in USD")


class QueryErrorEvent(BaseEvent):
    """Event fired when a Claude query encounters an error."""

    type: Literal[EventType.QUERY_ERROR] = EventType.QUERY_ERROR
    severity: Literal[EventSeverity.ERROR] = EventSeverity.ERROR
    error_type: str = Field(..., description="Type of error")
    error_details: Optional[str] = Field(None, description="Detailed error information")
    stack_trace: Optional[str] = Field(None, description="Stack trace if available")


class SessionInitEvent(BaseEvent):
    """Event fired when a Claude session is initialized."""

    type: Literal[EventType.SESSION_INIT] = EventType.SESSION_INIT
    tools_available: int = Field(0, description="Number of tools available")
    tool_names: List[str] = Field(
        default_factory=list, description="Names of available tools"
    )
    mcp_servers: int = Field(0, description="Number of MCP servers connected")
    server_names: List[str] = Field(
        default_factory=list, description="Names of MCP servers"
    )


class ThinkingStartEvent(BaseEvent):
    """Event fired when Claude starts thinking/reasoning."""

    type: Literal[EventType.THINKING_START] = EventType.THINKING_START
    signature: Optional[str] = Field(None, description="Thinking block signature")


class ThinkingInsightEvent(BaseEvent):
    """Event fired for insights extracted from thinking blocks."""

    type: Literal[EventType.THINKING_INSIGHT] = EventType.THINKING_INSIGHT
    insight_type: str = Field(
        ..., description="Type of insight: todo, insight, or decision"
    )
    content: str = Field(..., description="The insight content")
    priority: int = Field(1, description="Priority of the insight (1-5)")


class ToolUseEvent(BaseEvent):
    """Event fired when Claude uses a tool."""

    type: Literal[EventType.TOOL_USE] = EventType.TOOL_USE
    tool_name: str = Field(..., description="Name of the tool being used")
    tool_id: str = Field(..., description="Unique ID for this tool use")
    input_summary: str = Field(..., description="Formatted summary of tool input")
    step_number: int = Field(..., description="Current step in the process")


class ToolResultEvent(BaseEvent):
    """Event fired when a tool returns a result."""

    type: Literal[EventType.TOOL_RESULT] = EventType.TOOL_RESULT
    tool_id: str = Field(..., description="ID of the tool that produced this result")
    tool_name: str = Field(..., description="Name of the tool")
    success: bool = Field(..., description="Whether the tool executed successfully")
    result_summary: str = Field(..., description="Formatted summary of the result")
    result_size: Optional[int] = Field(
        None, description="Size of the result in characters"
    )


class ToolErrorEvent(BaseEvent):
    """Event fired when a tool encounters an error."""

    type: Literal[EventType.TOOL_ERROR] = EventType.TOOL_ERROR
    severity: Literal[EventSeverity.ERROR] = EventSeverity.ERROR
    tool_id: str = Field(..., description="ID of the tool that failed")
    tool_name: str = Field(..., description="Name of the tool")
    error_message: str = Field(..., description="Error message")


class TodoIdentifiedEvent(BaseEvent):
    """Event fired when a TODO/action item is identified."""

    type: Literal[EventType.TODO_IDENTIFIED] = EventType.TODO_IDENTIFIED
    todo_content: str = Field(..., description="The TODO content")
    priority: int = Field(1, description="Priority level (1-5)")
    sequence_number: int = Field(..., description="Sequence number of this TODO")


class DecisionMadeEvent(BaseEvent):
    """Event fired when Claude makes a key decision."""

    type: Literal[EventType.DECISION_MADE] = EventType.DECISION_MADE
    decision_content: str = Field(..., description="The decision content")
    confidence: Optional[float] = Field(None, description="Confidence level (0.0-1.0)")


class StepProgressEvent(BaseEvent):
    """Event fired to indicate progress through processing steps."""

    type: Literal[EventType.STEP_PROGRESS] = EventType.STEP_PROGRESS
    step_number: int = Field(..., description="Current step number")
    total_steps: Optional[int] = Field(None, description="Total expected steps")
    step_description: str = Field(..., description="Description of current step")
    progress_percent: Optional[float] = Field(
        None, description="Progress percentage (0.0-100.0)"
    )


class SystemMessageEvent(BaseEvent):
    """Event fired for system messages."""

    type: Literal[EventType.SYSTEM_MESSAGE] = EventType.SYSTEM_MESSAGE
    subtype: str = Field(..., description="System message subtype")
    system_data: Optional[Dict[str, Any]] = Field(
        None, description="System message data"
    )


class AssistantMessageEvent(BaseEvent):
    """Event fired for assistant messages."""

    type: Literal[EventType.ASSISTANT_MESSAGE] = EventType.ASSISTANT_MESSAGE
    content_length: int = Field(..., description="Length of assistant content")
    block_count: int = Field(..., description="Number of content blocks")
    has_text: bool = Field(False, description="Whether message contains text")
    has_thinking: bool = Field(False, description="Whether message contains thinking")
    has_tools: bool = Field(False, description="Whether message contains tool usage")
    full_content: Optional[str] = Field(None, description="Complete assistant message content")


class UserMessageEvent(BaseEvent):
    """Event fired for user messages."""

    type: Literal[EventType.USER_MESSAGE] = EventType.USER_MESSAGE
    content_length: int = Field(..., description="Length of user content")
    word_count: int = Field(..., description="Number of words in user message")
    full_content: Optional[str] = Field(None, description="Complete user message content")


class PerformanceMetricEvent(BaseEvent):
    """Event fired for performance metrics."""

    type: Literal[EventType.PERFORMANCE_METRIC] = EventType.PERFORMANCE_METRIC
    operation: str = Field(..., description="Name of the operation measured")
    duration: float = Field(..., description="Duration in seconds")
    metric_type: str = Field("duration", description="Type of metric")
    unit: str = Field("seconds", description="Unit of measurement")


class TokenUsageEvent(BaseEvent):
    """Event fired for token usage information."""

    type: Literal[EventType.TOKEN_USAGE] = EventType.TOKEN_USAGE
    input_tokens: int = Field(..., description="Number of input tokens")
    output_tokens: int = Field(..., description="Number of output tokens")
    total_tokens: int = Field(..., description="Total tokens used")
    cost_usd: Optional[float] = Field(None, description="Cost in USD")


# Union type for all possible events
StreamingEvent = Union[
    QueryStartEvent,
    QueryCompleteEvent,
    QueryErrorEvent,
    SessionInitEvent,
    ThinkingStartEvent,
    ThinkingInsightEvent,
    ToolUseEvent,
    ToolResultEvent,
    ToolErrorEvent,
    TodoIdentifiedEvent,
    DecisionMadeEvent,
    StepProgressEvent,
    SystemMessageEvent,
    AssistantMessageEvent,
    UserMessageEvent,
    PerformanceMetricEvent,
    TokenUsageEvent,
]


class EventSubscription(BaseModel):
    """Model for event subscription parameters."""

    client_id: str = Field(..., description="Unique client identifier")
    event_types: Optional[List[EventType]] = Field(
        None, description="Filter by specific event types"
    )
    session_id: Optional[str] = Field(None, description="Filter by specific session ID")
    severity_filter: Optional[List[EventSeverity]] = Field(
        None, description="Filter by severity levels"
    )
    include_system_events: bool = Field(
        True, description="Whether to include system events"
    )
    include_performance_events: bool = Field(
        False, description="Whether to include performance events"
    )


class EventStreamStatus(BaseModel):
    """Status information for event streams."""

    active_connections: int = Field(..., description="Number of active connections")
    events_queued: int = Field(..., description="Number of events in queue")
    total_events_sent: int = Field(..., description="Total events sent since startup")
    uptime_seconds: float = Field(..., description="Stream uptime in seconds")
    memory_usage_mb: Optional[float] = Field(None, description="Memory usage in MB")


# Export all event classes for easy imports
__all__ = [
    "EventType",
    "EventSeverity",
    "BaseEvent",
    "QueryStartEvent",
    "QueryCompleteEvent",
    "QueryErrorEvent",
    "SessionInitEvent",
    "ThinkingStartEvent",
    "ThinkingInsightEvent",
    "ToolUseEvent",
    "ToolResultEvent",
    "ToolErrorEvent",
    "TodoIdentifiedEvent",
    "DecisionMadeEvent",
    "StepProgressEvent",
    "SystemMessageEvent",
    "AssistantMessageEvent",
    "UserMessageEvent",
    "PerformanceMetricEvent",
    "TokenUsageEvent",
    "StreamingEvent",
    "EventSubscription",
    "EventStreamStatus",
]
