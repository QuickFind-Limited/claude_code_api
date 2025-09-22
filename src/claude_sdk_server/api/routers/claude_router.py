"""Minimal Claude API router."""

import asyncio
import json
from datetime import datetime
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from src.claude_sdk_server.models.dto import QueryRequest, QueryResponse
from src.claude_sdk_server.services.claude_service import (
    ClaudeService,
    get_claude_service,
)
from src.claude_sdk_server.streaming import get_event_manager

# Import SSE response
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


router = APIRouter(prefix="/api/v1", tags=["claude"])


def json_serializer(obj):
    """Custom JSON serializer for datetime objects."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


@router.post("/query")
async def query_claude(
    request: QueryRequest, service: ClaudeService = Depends(get_claude_service)
) -> QueryResponse:
    """Send a query to Claude Code."""
    try:
        response = await service.query(request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query/stream")
async def query_claude_stream(
    request: QueryRequest, service: ClaudeService = Depends(get_claude_service)
):
    """
    Send a query to Claude Code with live SSE streaming of formatted logs.
    
    This endpoint streams:
    - Session initialization
    - Query processing steps
    - Todo list updates with status
    - Tool usage and results
    - Assistant responses
    - Performance metrics
    
    Example usage:
        curl -X POST http://localhost:8000/api/v1/query/stream \
             -H "Content-Type: application/json" \
             -d '{"prompt": "Your query here", "model": "claude-3-opus-20240229"}'
    """

    async def generate_sse_events() -> AsyncGenerator[str, None]:
        """Generate SSE events with formatted logging."""
        event_manager = get_event_manager()

        # Create a unique client for this request
        from uuid import uuid4

        client_id = str(uuid4())

        # Subscribe to events for this session
        from src.claude_sdk_server.models.events import EventSubscription

        subscription = EventSubscription(
            client_id=client_id,
            session_id=request.session_id,
            include_system_events=True,
            include_performance_events=True,
        )

        # Connect client
        client = await event_manager.connect_client(subscription, connection_type="sse")

        try:
            # Send initial event as dict for sse-starlette
            yield {
                "event": "connection",
                "data": json.dumps({"status": "connected", "client_id": client_id}, default=json_serializer),
            }

            # Small delay to ensure SSE connection is fully established
            await asyncio.sleep(0.1)

            # Start the query in background
            query_task = asyncio.create_task(service.query(request))

            # Stream events in parallel with query execution
            response = None
            seen_events = set()  # Track event IDs to prevent duplicates

            # Create a queue for immediate event streaming
            event_queue = asyncio.Queue()

            async def stream_events_task():
                """Background task to stream events immediately."""
                client = event_manager.clients.get(client_id)
                if not client:
                    return

                try:
                    while client.is_active:
                        try:
                            # Get event immediately without timeout
                            event = await client.get_event(timeout=0.001)
                            if (
                                event
                                and hasattr(event, "id")
                                and event.id not in seen_events
                            ):
                                seen_events.add(event.id)
                                formatted_event = await format_event_for_sse(event)
                                if formatted_event:
                                    # Put event in queue immediately
                                    await event_queue.put(formatted_event)
                        except asyncio.TimeoutError:
                            # No event available, yield immediately to prevent batching
                            await asyncio.sleep(0)  # Yield control immediately
                        except Exception as e:
                            if client.is_active:
                                print(f"Event error: {e}")
                            break
                except Exception as e:
                    print(f"Event streaming error: {e}")

            # Start event streaming task
            event_stream_task = asyncio.create_task(stream_events_task())

            # Stream events immediately as they arrive with explicit flushing
            last_yield_time = asyncio.get_event_loop().time()

            while not query_task.done() or not event_queue.empty():
                try:
                    # Wait for event without timeout to prevent batching
                    event = await event_queue.get()
                    # Event is already a dict from format_event_for_sse
                    yield event
                    last_yield_time = asyncio.get_event_loop().time()
                except Exception as e:
                    print(f"Event streaming error: {e}")
                    break

            # Query is done, get result
            try:
                response = await query_task

                # Wait a bit for any remaining events and send them immediately
                end_time = asyncio.get_event_loop().time() + 0.5
                while asyncio.get_event_loop().time() < end_time:
                    try:
                        event = await asyncio.wait_for(event_queue.get(), timeout=0.01)
                        # Event is already a dict from format_event_for_sse
                        yield event
                    except asyncio.TimeoutError:
                        if event_queue.empty():
                            await asyncio.sleep(0.01)

                # Send final response event as dict with file changes
                yield {
                    "event": "response",
                    "data": json.dumps(
                        {
                            "response": response.response,
                            "session_id": response.session_id,
                            "attachments": [attachment.model_dump() for attachment in response.attachments],
                            "new_files": response.new_files,
                            "updated_files": response.updated_files,
                            "file_changes_summary": {
                                "total_files": len(response.attachments),
                                "new_count": len(response.new_files),
                                "updated_count": len(response.updated_files)
                            }
                        },
                        default=json_serializer
                    ),
                }

                # Send completion event as dict with file summary
                yield {
                    "event": "complete",
                    "data": json.dumps(
                        {
                            "status": "completed", 
                            "session_id": response.session_id,
                            "files_changed": len(response.new_files) + len(response.updated_files) > 0,
                            "summary": f"{len(response.new_files)} nouveaux fichiers, {len(response.updated_files)} modifiés"
                        },
                        default=json_serializer
                    ),
                }

            except Exception as e:
                # Send error event as dict
                yield {"event": "error", "data": json.dumps({"error": str(e)}, default=json_serializer)}

            # Cleanup event stream task
            if event_stream_task and not event_stream_task.done():
                event_stream_task.cancel()

        finally:
            # Disconnect client
            await event_manager.disconnect_client(client_id)

    return EventSourceResponse(generate_sse_events())


async def format_event_for_sse(event) -> str:
    """Format events for pretty SSE display."""
    event_type = event.type.value if hasattr(event, "type") else "unknown"

    # Format based on event type
    formatted_data = {
        "type": event_type,
        "timestamp": event.timestamp.isoformat()
        if hasattr(event, "timestamp")
        else None,
    }

    # Add custom formatting based on event type
    if event_type == "session_init":
        formatted_data["display"] = "🔧 Session: Initializing Claude session"
        formatted_data["details"] = {
            "tools": getattr(event, "tools_available", 0),
            "mcp_servers": getattr(event, "mcp_servers", 0),
        }

    elif event_type == "query_start":
        formatted_data["display"] = "🚀 Query: Processing request"
        formatted_data["details"] = {
            "words": getattr(event, "word_count", 0),
            "model": getattr(event, "model", "unknown"),
        }

    elif event_type == "thinking_start":
        formatted_data["display"] = "🤔 Thinking: Analyzing your request..."

    elif event_type == "todo_identified":
        todo_content = getattr(event, "todo_content", "")
        formatted_data["display"] = f"📝 TODO: {todo_content}"

    elif event_type == "tool_use":
        tool_name = getattr(event, "tool_name", "unknown")
        if tool_name == "TodoWrite":
            formatted_data["display"] = "📋 Todo Update: Managing task list"
        elif "perplexity" in tool_name.lower():
            formatted_data["display"] = "🔍 Perplexity: Searching web for current info"
        elif "firecrawl" in tool_name.lower():
            formatted_data["display"] = "🕷️ Firecrawl: Web scraping"
        else:
            formatted_data["display"] = f"🛠️ Tool: {tool_name}"
        formatted_data["details"] = getattr(event, "input_summary", "")

    elif event_type == "tool_result":
        tool_name = getattr(event, "tool_name", "unknown")
        success = getattr(event, "success", False)
        status = "✅" if success else "❌"
        if "perplexity" in tool_name.lower():
            formatted_data["display"] = f"{status} Perplexity search completed"
        elif "firecrawl" in tool_name.lower():
            formatted_data["display"] = f"{status} Web scraping completed"
        else:
            formatted_data["display"] = f"{status} Result: {tool_name} completed"

    elif event_type == "assistant_message":
        formatted_data["display"] = "💬 Assistant: Response block"
        formatted_data["details"] = {
            "has_text": getattr(event, "has_text", False),
            "has_thinking": getattr(event, "has_thinking", False),
            "has_tools": getattr(event, "has_tools", False),
        }
        # Include full content for frontend display
        full_content = getattr(event, "full_content", None)
        if full_content:
            formatted_data["full_content"] = full_content

    elif event_type == "query_complete":
        duration = getattr(event, "duration_seconds", 0)
        formatted_data["display"] = f"✅ Complete: Query processed in {duration:.2f}s"

    elif event_type == "performance_metric":
        operation = getattr(event, "operation", "unknown")
        duration = getattr(event, "duration", 0)
        formatted_data["display"] = f"📊 Performance: {operation} took {duration:.2f}s"

    else:
        # Generic event
        formatted_data["display"] = f"📌 {event_type}: {getattr(event, 'message', '')}"

    # Add raw event data if available
    if hasattr(event, "data") and event.data:
        formatted_data["data"] = event.data

    # Return as dict for sse-starlette
    return {"event": "log", "data": json.dumps(formatted_data, default=json_serializer)}


@router.get("/health")
async def health_check():
    """Simple health check endpoint."""
    return {"status": "healthy"}
