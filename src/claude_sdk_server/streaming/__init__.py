"""Real-time event streaming package for Claude SDK Server.

This package provides comprehensive streaming capabilities for delivering Claude processing
events in real-time to web clients, API consumers, and other applications.

Key Features:
- Server-Sent Events (SSE) for web browsers
- WebSocket support for bidirectional communication
- JSON Lines streaming for API clients
- Event filtering and subscription management
- Production-ready with proper error handling and cleanup

Usage:
    from claude_sdk_server.streaming import get_event_manager, emit_event

    # Emit an event
    await emit_event(QueryStartEvent(...))

    # Get streaming manager
    manager = get_event_manager()

    # Connect a client
    client = await manager.connect_client(subscription)
"""

# Re-export event models for convenience
from ..models.events import (
    AssistantMessageEvent,
    # Event models
    BaseEvent,
    DecisionMadeEvent,
    EventSeverity,
    EventStreamStatus,
    # Subscription and status models
    EventSubscription,
    # Event types
    EventType,
    PerformanceMetricEvent,
    QueryCompleteEvent,
    QueryErrorEvent,
    QueryStartEvent,
    SessionInitEvent,
    StepProgressEvent,
    StreamingEvent,
    SystemMessageEvent,
    ThinkingInsightEvent,
    ThinkingStartEvent,
    TodoIdentifiedEvent,
    TokenUsageEvent,
    ToolErrorEvent,
    ToolResultEvent,
    ToolUseEvent,
    UserMessageEvent,
)
from .event_stream import (
    ClientConnection,
    EventQueue,
    EventStreamManager,
    emit_event,
    get_event_manager,
    websocket_connection,
)

__version__ = "1.0.0"

__all__ = [
    # Core streaming functionality
    "EventQueue",
    "ClientConnection",
    "EventStreamManager",
    "get_event_manager",
    "emit_event",
    "websocket_connection",
    # Event system
    "EventType",
    "EventSeverity",
    "BaseEvent",
    "StreamingEvent",
    # Lifecycle events
    "QueryStartEvent",
    "QueryCompleteEvent",
    "QueryErrorEvent",
    # Processing events
    "SessionInitEvent",
    "ThinkingStartEvent",
    "ThinkingInsightEvent",
    "SystemMessageEvent",
    "AssistantMessageEvent",
    "UserMessageEvent",
    # Tool events
    "ToolUseEvent",
    "ToolResultEvent",
    "ToolErrorEvent",
    # Progress events
    "TodoIdentifiedEvent",
    "DecisionMadeEvent",
    "StepProgressEvent",
    # Performance events
    "PerformanceMetricEvent",
    "TokenUsageEvent",
    # Subscription and status
    "EventSubscription",
    "EventStreamStatus",
]
