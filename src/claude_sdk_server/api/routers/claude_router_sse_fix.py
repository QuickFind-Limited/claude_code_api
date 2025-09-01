"""Fixed SSE implementation for claude_router.py"""


async def generate_sse_events():
    """Generate SSE events with proper sse-starlette format."""
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
            "data": json.dumps({"status": "connected", "client_id": client_id}),
        }

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
                        # Get event with very short timeout for immediate streaming
                        event = await asyncio.wait_for(
                            client.get_event(timeout=0.01), timeout=0.05
                        )
                        if (
                            event
                            and hasattr(event, "id")
                            and event.id not in seen_events
                        ):
                            seen_events.add(event.id)
                            formatted_event = await format_event_for_sse_dict(event)
                            if formatted_event:
                                # Put event in queue immediately
                                await event_queue.put(formatted_event)
                    except asyncio.TimeoutError:
                        # No event available, continue immediately
                        await asyncio.sleep(0.001)  # Minimal sleep
                    except Exception as e:
                        if client.is_active:
                            print(f"Event error: {e}")
                        break
            except Exception as e:
                print(f"Event streaming error: {e}")

        # Start event streaming task
        event_stream_task = asyncio.create_task(stream_events_task())

        # Stream events immediately as they arrive
        while not query_task.done() or not event_queue.empty():
            try:
                # Get event with very short timeout to check query status frequently
                event_dict = await asyncio.wait_for(event_queue.get(), timeout=0.01)
                yield event_dict  # Yield dict directly for sse-starlette
            except asyncio.TimeoutError:
                # Send keep-alive to prevent connection timeout
                yield {"comment": "keepalive"}
                await asyncio.sleep(0.01)  # Very short sleep

        # Query is done, get result
        try:
            response = await query_task

            # Wait a bit for any remaining events and send them immediately
            end_time = asyncio.get_event_loop().time() + 0.5
            while asyncio.get_event_loop().time() < end_time:
                try:
                    event_dict = await asyncio.wait_for(event_queue.get(), timeout=0.01)
                    yield event_dict
                except asyncio.TimeoutError:
                    if event_queue.empty():
                        await asyncio.sleep(0.01)

            # Send final response event as dict
            yield {
                "event": "response",
                "data": json.dumps(
                    {"response": response.response, "session_id": response.session_id}
                ),
            }

            # Send completion event as dict
            yield {
                "event": "complete",
                "data": json.dumps(
                    {"status": "completed", "session_id": response.session_id}
                ),
            }

        except Exception as e:
            # Send error event as dict
            yield {"event": "error", "data": json.dumps({"error": str(e)})}

        # Cleanup event stream task
        if event_stream_task and not event_stream_task.done():
            event_stream_task.cancel()

    finally:
        # Disconnect client
        await event_manager.disconnect_client(client_id)


async def format_event_for_sse_dict(event) -> dict:
    """Format events for SSE as dictionary for sse-starlette."""
    event_type = event.type.value if hasattr(event, "type") else "unknown"

    # Format based on event type
    formatted_data = {
        "type": event_type,
        "timestamp": event.timestamp.isoformat()
        if hasattr(event, "timestamp")
        else None,
    }

    # Add display and details based on event type
    if event_type == "session_init":
        formatted_data["display"] = "🔧 Session: Initialized"
        formatted_data["details"] = {
            "tools": getattr(event, "tools_available", 0),
            "mcp": getattr(event, "mcp_servers", 0),
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
    return {"event": "log", "data": json.dumps(formatted_data)}
