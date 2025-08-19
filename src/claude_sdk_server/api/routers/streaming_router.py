"""FastAPI router for real-time event streaming endpoints.

This router provides multiple streaming endpoints:
- Server-Sent Events (SSE) for web browsers
- WebSocket connections for bidirectional communication
- JSON Lines streaming for API clients
- Stream management and status endpoints

All endpoints support event filtering, session-based streaming,
and proper error handling with client cleanup.
"""

import asyncio
import json
from typing import List, Optional
from uuid import uuid4

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Request,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.responses import StreamingResponse

# Import SSE response - fallback if sse-starlette not available
try:
    from sse_starlette import EventSourceResponse
except ImportError:
    # Fallback implementation if sse-starlette not available
    from fastapi.responses import StreamingResponse

    class EventSourceResponse(StreamingResponse):
        """Fallback SSE implementation using StreamingResponse."""

        def __init__(self, generator, headers=None):
            final_headers = {
                "Content-Type": "text/event-stream",
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            }
            if headers:
                final_headers.update(headers)

            super().__init__(
                generator, media_type="text/event-stream", headers=final_headers
            )


from ...models.events import (
    EventSeverity,
    EventStreamStatus,
    EventSubscription,
    EventType,
)
from ...streaming import (
    EventStreamManager,
    get_event_manager,
    websocket_connection,
)
from ...utils.logging_config import get_logger

# Configure logger
router_logger = get_logger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/stream", tags=["streaming"])


def create_subscription(
    client_id: Optional[str] = Query(None, description="Unique client identifier"),
    event_types: Optional[List[EventType]] = Query(
        None, description="Filter by event types"
    ),
    session_id: Optional[str] = Query(None, description="Filter by session ID"),
    severity_filter: Optional[List[EventSeverity]] = Query(
        None, description="Filter by severity"
    ),
    include_system: bool = Query(True, description="Include system events"),
    include_performance: bool = Query(False, description="Include performance events"),
) -> EventSubscription:
    """Create an event subscription from query parameters."""
    if not client_id:
        client_id = str(uuid4())

    return EventSubscription(
        client_id=client_id,
        event_types=event_types,
        session_id=session_id,
        severity_filter=severity_filter,
        include_system_events=include_system,
        include_performance_events=include_performance,
    )


@router.get("/sse")
async def stream_events_sse(
    request: Request,
    subscription: EventSubscription = Depends(create_subscription),
    manager: EventStreamManager = Depends(get_event_manager),
):
    """
    Stream events via Server-Sent Events (SSE).

    Perfect for web browsers and applications that need real-time updates
    with automatic reconnection support.

    Query Parameters:
    - client_id: Unique identifier for the client (auto-generated if not provided)
    - event_types: Filter by specific event types (comma-separated)
    - session_id: Only receive events for a specific Claude session
    - severity_filter: Filter by severity levels (info, success, warning, error, critical)
    - include_system: Include system events (default: true)
    - include_performance: Include performance metrics (default: false)

    Example:
        /api/v1/stream/sse?event_types=query_start,tool_use&session_id=abc123
    """

    # Connect client
    client = await manager.connect_client(subscription, connection_type="sse")

    async def event_generator():
        """Generate SSE formatted events."""
        try:
            router_logger.info(f"Starting SSE stream for client {client.client_id}")

            # Send initial connection event
            yield f"id: {uuid4()}\n"
            yield "event: connection\n"
            yield f"data: {json.dumps({'status': 'connected', 'client_id': client.client_id})}\n\n"

            # Stream events
            async for sse_data in manager.get_sse_stream(client.client_id):
                if await request.is_disconnected():
                    router_logger.info(f"SSE client {client.client_id} disconnected")
                    break
                yield sse_data

        except Exception as e:
            router_logger.error(f"SSE stream error for client {client.client_id}: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
        finally:
            await manager.disconnect_client(client.client_id)

    return EventSourceResponse(
        event_generator(),
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )


@router.websocket("/ws")
async def websocket_events(
    websocket: WebSocket,
    client_id: Optional[str] = Query(None),
    event_types: Optional[str] = Query(None),
    session_id: Optional[str] = Query(None),
    include_system: bool = Query(True),
    include_performance: bool = Query(False),
):
    """
    Stream events via WebSocket connection.

    Provides bidirectional communication for interactive applications.
    Clients can send subscription updates and receive real-time events.

    Query Parameters:
    - client_id: Unique identifier for the client
    - event_types: Comma-separated list of event types to filter
    - session_id: Only receive events for a specific Claude session
    - include_system: Include system events (default: true)
    - include_performance: Include performance metrics (default: false)

    WebSocket Messages:
    - Send: {"action": "subscribe", "event_types": ["query_start", "tool_use"]}
    - Send: {"action": "unsubscribe"}
    - Send: {"action": "ping"}
    - Receive: Event objects as JSON
    """

    await websocket.accept()
    manager = get_event_manager()

    # Parse event types from query string
    parsed_event_types = None
    if event_types:
        try:
            parsed_event_types = [EventType(t.strip()) for t in event_types.split(",")]
        except ValueError as e:
            await websocket.send_json({"error": f"Invalid event type: {e}"})
            await websocket.close()
            return

    # Create initial subscription
    subscription = EventSubscription(
        client_id=client_id or str(uuid4()),
        event_types=parsed_event_types,
        session_id=session_id,
        include_system_events=include_system,
        include_performance_events=include_performance,
    )

    client = None

    async with websocket_connection(websocket):
        try:
            # Connect client
            client = await manager.connect_client(
                subscription, connection_type="websocket"
            )

            router_logger.info(f"WebSocket connected for client {client.client_id}")

            # Send connection confirmation
            await websocket.send_json(
                {
                    "type": "connection",
                    "status": "connected",
                    "client_id": client.client_id,
                    "subscription": subscription.dict(),
                }
            )

            # Start event streaming task
            event_task = asyncio.create_task(
                stream_events_to_websocket(websocket, manager, client)
            )

            # Handle incoming messages
            while True:
                try:
                    # Wait for either incoming message or task completion
                    done, pending = await asyncio.wait(
                        [asyncio.create_task(websocket.receive_json()), event_task],
                        return_when=asyncio.FIRST_COMPLETED,
                    )

                    # Cancel pending tasks
                    for task in pending:
                        task.cancel()

                    # Process completed tasks
                    for task in done:
                        if task == event_task:
                            # Event streaming task completed (probably due to error)
                            break
                        else:
                            # Received message from client
                            try:
                                message = await task
                                await handle_websocket_message(
                                    websocket, client, message, manager
                                )
                            except Exception as e:
                                router_logger.error(
                                    f"Error processing WebSocket message: {e}"
                                )
                                await websocket.send_json({"error": str(e)})

                    # If event task completed, break the loop
                    if event_task.done():
                        break

                except WebSocketDisconnect:
                    router_logger.info(
                        f"WebSocket client {client.client_id} disconnected"
                    )
                    break
                except Exception as e:
                    router_logger.error(
                        f"WebSocket error for client {client.client_id}: {e}"
                    )
                    try:
                        await websocket.send_json({"error": str(e)})
                    except Exception:
                        pass
                    break

        except Exception as e:
            router_logger.error(f"WebSocket connection error: {e}")
        finally:
            if client:
                await manager.disconnect_client(client.client_id)


async def stream_events_to_websocket(
    websocket: WebSocket, manager: EventStreamManager, client
):
    """Stream events to WebSocket client."""
    try:
        async for event in manager.get_client_stream(client.client_id):
            await websocket.send_json(event.dict())
    except WebSocketDisconnect:
        pass
    except Exception as e:
        router_logger.error(
            f"Error streaming to WebSocket client {client.client_id}: {e}"
        )


async def handle_websocket_message(
    websocket: WebSocket, client, message: dict, manager: EventStreamManager
):
    """Handle incoming WebSocket messages from client."""
    action = message.get("action")

    if action == "ping":
        await websocket.send_json(
            {"type": "pong", "timestamp": asyncio.get_event_loop().time()}
        )

    elif action == "subscribe":
        # Update subscription
        event_types = message.get("event_types")
        if event_types:
            try:
                client.subscription.event_types = [EventType(t) for t in event_types]
                await websocket.send_json(
                    {"status": "subscription_updated", "event_types": event_types}
                )
            except ValueError as e:
                await websocket.send_json({"error": f"Invalid event types: {e}"})

    elif action == "get_recent":
        # Send recent events
        count = message.get("count", 10)
        recent_events = await manager.get_recent_events(count=count)
        await websocket.send_json(
            {
                "type": "recent_events",
                "events": [event.dict() for event in recent_events],
            }
        )

    else:
        await websocket.send_json({"error": f"Unknown action: {action}"})


@router.get("/jsonl")
async def stream_events_jsonl(
    subscription: EventSubscription = Depends(create_subscription),
    manager: EventStreamManager = Depends(get_event_manager),
):
    """
    Stream events as JSON Lines (JSONL).

    Each event is sent as a single JSON object followed by a newline.
    Perfect for programmatic consumption and log processing.

    Query Parameters: Same as SSE endpoint

    Example:
        /api/v1/stream/jsonl?session_id=abc123&event_types=tool_use,tool_result
    """

    # Connect client
    client = await manager.connect_client(subscription, connection_type="jsonl")

    async def jsonl_generator():
        """Generate JSON Lines formatted events."""
        try:
            router_logger.info(f"Starting JSONL stream for client {client.client_id}")

            # Send initial connection line
            yield (
                json.dumps(
                    {
                        "type": "connection",
                        "status": "connected",
                        "client_id": client.client_id,
                    }
                )
                + "\n"
            )

            # Stream events as JSON Lines
            async for line in manager.get_jsonl_stream(client.client_id):
                yield line

        except Exception as e:
            router_logger.error(
                f"JSONL stream error for client {client.client_id}: {e}"
            )
            yield json.dumps({"error": str(e)}) + "\n"
        finally:
            await manager.disconnect_client(client.client_id)

    return StreamingResponse(
        jsonl_generator(),
        media_type="application/x-ndjson",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/status")
async def get_stream_status(
    manager: EventStreamManager = Depends(get_event_manager),
) -> EventStreamStatus:
    """
    Get current streaming system status.

    Returns information about active connections, queued events,
    total events sent, and system uptime.
    """
    return manager.get_status()


@router.get("/events/recent")
async def get_recent_events(
    count: int = Query(
        100, ge=1, le=1000, description="Number of recent events to return"
    ),
    event_types: Optional[List[EventType]] = Query(
        None, description="Filter by event types"
    ),
    session_id: Optional[str] = Query(None, description="Filter by session ID"),
    manager: EventStreamManager = Depends(get_event_manager),
) -> List[dict]:
    """
    Get recent events from the stream.

    Useful for initializing clients or debugging stream issues.

    Parameters:
    - count: Number of events to return (1-1000, default: 100)
    - event_types: Filter by specific event types
    - session_id: Filter by specific session ID
    """
    events = await manager.get_recent_events(
        count=count, event_types=event_types, session_id=session_id
    )

    return [event.dict() for event in events]


@router.delete("/clients/{client_id}")
async def disconnect_client(
    client_id: str, manager: EventStreamManager = Depends(get_event_manager)
):
    """
    Manually disconnect a client.

    Useful for administrative purposes or cleaning up stuck connections.
    """
    if client_id not in manager.clients:
        raise HTTPException(status_code=404, detail="Client not found")

    await manager.disconnect_client(client_id)
    return {"status": "disconnected", "client_id": client_id}


@router.get("/clients")
async def list_active_clients(manager: EventStreamManager = Depends(get_event_manager)):
    """
    List all active streaming clients.

    Returns client information including connection time, event counts,
    and subscription details.
    """
    clients_info = []

    for client_id, client in manager.clients.items():
        clients_info.append(
            {
                "client_id": client_id,
                "connection_type": client.connection_type,
                "connected_at": client.connected_at.isoformat(),
                "last_activity": client.last_activity.isoformat(),
                "events_sent": client.events_sent,
                "is_active": client.is_active,
                "subscription": {
                    "event_types": client.subscription.event_types,
                    "session_id": client.subscription.session_id,
                    "severity_filter": client.subscription.severity_filter,
                    "include_system_events": client.subscription.include_system_events,
                    "include_performance_events": client.subscription.include_performance_events,
                },
            }
        )

    return {
        "active_clients": len(clients_info),
        "websocket_connections": len(manager.websocket_connections),
        "clients": clients_info,
    }


@router.post("/test-event")
async def emit_test_event(
    message: str = Query(..., description="Test message to send"),
    event_type: EventType = Query(
        EventType.SYSTEM_MESSAGE, description="Type of test event"
    ),
    session_id: Optional[str] = Query(
        None, description="Session ID for the test event"
    ),
    manager: EventStreamManager = Depends(get_event_manager),
):
    """
    Emit a test event for debugging streaming functionality.

    Useful for testing client connections and event filtering.
    """
    from ...streaming import BaseEvent

    test_event = BaseEvent(
        type=event_type,
        message=f"Test event: {message}",
        session_id=session_id,
        data={"test": True, "source": "streaming_router"},
    )

    await manager.emit_event(test_event)

    return {
        "status": "sent",
        "event_id": test_event.id,
        "message": message,
        "active_clients": len(manager.clients),
    }
