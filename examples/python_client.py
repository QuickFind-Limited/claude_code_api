#!/usr/bin/env python3
"""
Python Client Library for Claude SDK Server

This module provides a comprehensive Python client for interacting with
the Claude SDK Server, including streaming capabilities and event handling.
"""

import asyncio
import json
import threading
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union

import aiohttp
import requests
import sseclient
import websockets


class EventType(str, Enum):
    """Event types emitted by the Claude SDK Server."""

    QUERY_START = "query_start"
    QUERY_COMPLETE = "query_complete"
    QUERY_ERROR = "query_error"
    SESSION_INIT = "session_init"
    THINKING_START = "thinking_start"
    THINKING_INSIGHT = "thinking_insight"
    TOOL_USE = "tool_use"
    TOOL_RESULT = "tool_result"
    TOOL_ERROR = "tool_error"
    TODO_IDENTIFIED = "todo_identified"
    DECISION_MADE = "decision_made"
    STEP_PROGRESS = "step_progress"
    SYSTEM_MESSAGE = "system_message"
    ASSISTANT_MESSAGE = "assistant_message"
    PERFORMANCE_METRIC = "performance_metric"
    TOKEN_USAGE = "token_usage"


@dataclass
class StreamEvent:
    """Represents a streaming event from the server."""

    id: str
    type: str
    timestamp: str
    session_id: Optional[str]
    severity: str
    message: str
    data: Optional[Dict[str, Any]]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StreamEvent":
        """Create a StreamEvent from a dictionary."""
        return cls(
            id=data.get("id", ""),
            type=data.get("type", ""),
            timestamp=data.get("timestamp", ""),
            session_id=data.get("session_id"),
            severity=data.get("severity", "info"),
            message=data.get("message", ""),
            data=data.get("data"),
        )


@dataclass
class QueryResponse:
    """Response from a Claude query."""

    response: str
    session_id: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "QueryResponse":
        """Create a QueryResponse from a dictionary."""
        return cls(
            response=data.get("response", ""),
            session_id=data.get("session_id", ""),
        )


class ClaudeSDKClient:
    """
    Synchronous client for Claude SDK Server.

    Example:
        client = ClaudeSDKClient("http://localhost:8000")
        response = client.query("What is 2+2?")
        print(response.response)
    """

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api/v1"
        self.session = requests.Session()

    def query(
        self,
        prompt: str,
        session_id: Optional[str] = None,
        max_turns: int = 30,
        model: str = "claude-3-5-sonnet-20241022",
        max_thinking_tokens: int = 8000,
    ) -> QueryResponse:
        """
        Send a query to Claude.

        Args:
            prompt: The prompt to send to Claude
            session_id: Optional session ID for conversation continuity
            max_turns: Maximum number of conversation turns
            model: Claude model to use
            max_thinking_tokens: Maximum tokens for thinking/reasoning

        Returns:
            QueryResponse with the response and session ID
        """
        response = self.session.post(
            f"{self.api_url}/query",
            json={
                "prompt": prompt,
                "session_id": session_id,
                "max_turns": max_turns,
                "model": model,
                "max_thinking_tokens": max_thinking_tokens,
            },
        )
        response.raise_for_status()
        return QueryResponse.from_dict(response.json())

    def stream_sse(
        self,
        event_handler: Callable[[StreamEvent], None],
        event_types: Optional[List[str]] = None,
        session_id: Optional[str] = None,
        include_performance: bool = False,
        include_system: bool = True,
    ) -> None:
        """
        Stream events using Server-Sent Events.

        Args:
            event_handler: Function to call for each event
            event_types: Optional list of event types to filter
            session_id: Optional session ID to filter events
            include_performance: Whether to include performance events
            include_system: Whether to include system events
        """
        params = {}
        if event_types:
            params["event_types"] = ",".join(event_types)
        if session_id:
            params["session_id"] = session_id
        if include_performance is not None:
            params["include_performance"] = str(include_performance).lower()
        if include_system is not None:
            params["include_system"] = str(include_system).lower()

        response = self.session.get(
            f"{self.api_url}/stream/sse",
            params=params,
            stream=True,
        )
        response.raise_for_status()

        client = sseclient.SSEClient(response)
        for event in client.events():
            try:
                data = json.loads(event.data)
                stream_event = StreamEvent.from_dict(data)
                event_handler(stream_event)
            except json.JSONDecodeError:
                print(f"Failed to parse event: {event.data}")
            except Exception as e:
                print(f"Error handling event: {e}")

    def stream_jsonl(
        self,
        event_handler: Callable[[StreamEvent], None],
        event_types: Optional[List[str]] = None,
        session_id: Optional[str] = None,
    ) -> None:
        """
        Stream events using JSON Lines format.

        Args:
            event_handler: Function to call for each event
            event_types: Optional list of event types to filter
            session_id: Optional session ID to filter events
        """
        params = {}
        if event_types:
            params["event_types"] = ",".join(event_types)
        if session_id:
            params["session_id"] = session_id

        response = self.session.get(
            f"{self.api_url}/stream/jsonl",
            params=params,
            stream=True,
        )
        response.raise_for_status()

        for line in response.iter_lines():
            if line:
                try:
                    data = json.loads(line)
                    stream_event = StreamEvent.from_dict(data)
                    event_handler(stream_event)
                except json.JSONDecodeError:
                    print(f"Failed to parse JSON line: {line}")
                except Exception as e:
                    print(f"Error handling event: {e}")

    def get_stream_status(self) -> Dict[str, Any]:
        """Get the current streaming status."""
        response = self.session.get(f"{self.api_url}/stream/status")
        response.raise_for_status()
        return response.json()

    def get_recent_events(
        self,
        count: int = 100,
        event_types: Optional[List[str]] = None,
        session_id: Optional[str] = None,
    ) -> List[StreamEvent]:
        """
        Get recent events from the server.

        Args:
            count: Number of events to retrieve
            event_types: Optional list of event types to filter
            session_id: Optional session ID to filter events

        Returns:
            List of recent StreamEvent objects
        """
        params = {"count": count}
        if event_types:
            params["event_types"] = ",".join(event_types)
        if session_id:
            params["session_id"] = session_id

        response = self.session.get(
            f"{self.api_url}/stream/events/recent",
            params=params,
        )
        response.raise_for_status()

        events = []
        for event_data in response.json():
            events.append(StreamEvent.from_dict(event_data))
        return events

    def health_check(self) -> bool:
        """Check if the server is healthy."""
        try:
            response = self.session.get(f"{self.api_url}/health")
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False

    def close(self):
        """Close the session."""
        self.session.close()


class AsyncClaudeSDKClient:
    """
    Asynchronous client for Claude SDK Server.

    Example:
        async with AsyncClaudeSDKClient() as client:
            response = await client.query("What is 2+2?")
            print(response.response)
    """

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api/v1"
        self.ws_url = base_url.replace("http://", "ws://").replace("https://", "wss://")
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def query(
        self,
        prompt: str,
        session_id: Optional[str] = None,
        max_turns: int = 30,
        model: str = "claude-3-5-sonnet-20241022",
        max_thinking_tokens: int = 8000,
    ) -> QueryResponse:
        """Send an async query to Claude."""
        if not self.session:
            raise RuntimeError("Session not initialized. Use async with statement.")

        async with self.session.post(
            f"{self.api_url}/query",
            json={
                "prompt": prompt,
                "session_id": session_id,
                "max_turns": max_turns,
                "model": model,
                "max_thinking_tokens": max_thinking_tokens,
            },
        ) as response:
            response.raise_for_status()
            data = await response.json()
            return QueryResponse.from_dict(data)

    async def stream_websocket(
        self,
        event_handler: Callable[[StreamEvent], None],
        event_types: Optional[List[str]] = None,
    ):
        """
        Stream events using WebSocket.

        Args:
            event_handler: Function to call for each event
            event_types: Optional list of event types to subscribe to
        """
        uri = f"{self.ws_url}/api/v1/stream/ws"

        async with websockets.connect(uri) as websocket:
            # Subscribe to specific event types if provided
            if event_types:
                await websocket.send(
                    json.dumps(
                        {
                            "action": "subscribe",
                            "event_types": event_types,
                        }
                    )
                )

            # Listen for events
            async for message in websocket:
                try:
                    data = json.loads(message)
                    stream_event = StreamEvent.from_dict(data)
                    event_handler(stream_event)
                except json.JSONDecodeError:
                    print(f"Failed to parse WebSocket message: {message}")
                except Exception as e:
                    print(f"Error handling WebSocket event: {e}")


class StreamingClaudeClient:
    """
    High-level client with automatic streaming and event handling.

    Example:
        client = StreamingClaudeClient()

        # Register event handlers
        client.on_thinking(lambda event: print(f"Thinking: {event.message}"))
        client.on_tool_use(lambda event: print(f"Tool: {event.data['tool_name']}"))

        # Start streaming
        client.start_streaming()

        # Send query
        response = client.query("Explain quantum computing")

        # Stop streaming
        client.stop_streaming()
    """

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.client = ClaudeSDKClient(base_url)
        self.event_handlers: Dict[str, List[Callable]] = {}
        self.streaming_thread: Optional[threading.Thread] = None
        self.stop_streaming_flag = threading.Event()
        self.current_session_id: Optional[str] = None

    def on(
        self, event_type: Union[EventType, str], handler: Callable[[StreamEvent], None]
    ):
        """Register an event handler for a specific event type."""
        event_type_str = (
            event_type.value if isinstance(event_type, EventType) else event_type
        )
        if event_type_str not in self.event_handlers:
            self.event_handlers[event_type_str] = []
        self.event_handlers[event_type_str].append(handler)

    def on_thinking(self, handler: Callable[[StreamEvent], None]):
        """Register handler for thinking insights."""
        self.on(EventType.THINKING_INSIGHT, handler)

    def on_tool_use(self, handler: Callable[[StreamEvent], None]):
        """Register handler for tool usage."""
        self.on(EventType.TOOL_USE, handler)

    def on_tool_result(self, handler: Callable[[StreamEvent], None]):
        """Register handler for tool results."""
        self.on(EventType.TOOL_RESULT, handler)

    def on_complete(self, handler: Callable[[StreamEvent], None]):
        """Register handler for query completion."""
        self.on(EventType.QUERY_COMPLETE, handler)

    def on_error(self, handler: Callable[[StreamEvent], None]):
        """Register handler for errors."""
        self.on(EventType.QUERY_ERROR, handler)

    def _handle_event(self, event: StreamEvent):
        """Internal event handler that dispatches to registered handlers."""
        # Update session ID if present
        if event.session_id:
            self.current_session_id = event.session_id

        # Call registered handlers for this event type
        if event.type in self.event_handlers:
            for handler in self.event_handlers[event.type]:
                try:
                    handler(event)
                except Exception as e:
                    print(f"Error in event handler: {e}")

        # Call wildcard handlers (registered with "*")
        if "*" in self.event_handlers:
            for handler in self.event_handlers["*"]:
                try:
                    handler(event)
                except Exception as e:
                    print(f"Error in wildcard handler: {e}")

    def _streaming_worker(self):
        """Background thread for streaming events."""
        while not self.stop_streaming_flag.is_set():
            try:
                self.client.stream_sse(
                    event_handler=self._handle_event,
                    session_id=self.current_session_id,
                    include_performance=True,
                )
            except Exception as e:
                print(f"Streaming error: {e}")
                time.sleep(5)  # Wait before reconnecting

    def start_streaming(self):
        """Start streaming events in the background."""
        if self.streaming_thread and self.streaming_thread.is_alive():
            print("Streaming already active")
            return

        self.stop_streaming_flag.clear()
        self.streaming_thread = threading.Thread(target=self._streaming_worker)
        self.streaming_thread.daemon = True
        self.streaming_thread.start()
        print("Streaming started")

    def stop_streaming(self):
        """Stop streaming events."""
        self.stop_streaming_flag.set()
        if self.streaming_thread:
            self.streaming_thread.join(timeout=5)
        print("Streaming stopped")

    def query(
        self,
        prompt: str,
        max_thinking_tokens: int = 8000,
        wait_for_completion: bool = True,
        timeout: float = 60.0,
    ) -> QueryResponse:
        """
        Send a query to Claude with automatic event streaming.

        Args:
            prompt: The prompt to send
            max_thinking_tokens: Maximum thinking tokens
            wait_for_completion: Whether to wait for query completion event
            timeout: Timeout in seconds when waiting for completion

        Returns:
            QueryResponse object
        """
        # Create completion event if waiting
        completion_event = threading.Event() if wait_for_completion else None

        def on_completion(event: StreamEvent):
            if completion_event:
                completion_event.set()

        if wait_for_completion:
            self.on_complete(on_completion)

        # Send query
        response = self.client.query(
            prompt=prompt,
            session_id=self.current_session_id,
            max_thinking_tokens=max_thinking_tokens,
        )

        # Update session ID
        self.current_session_id = response.session_id

        # Wait for completion if requested
        if completion_event:
            completion_event.wait(timeout=timeout)

        return response

    def get_status(self) -> Dict[str, Any]:
        """Get streaming status."""
        return self.client.get_stream_status()

    def close(self):
        """Clean up resources."""
        self.stop_streaming()
        self.client.close()


# Example usage functions
def example_basic_usage():
    """Example of basic client usage."""
    print("=== Basic Client Usage ===")

    client = ClaudeSDKClient()

    # Check health
    if client.health_check():
        print("✅ Server is healthy")
    else:
        print("❌ Server is not responding")
        return

    # Send a query
    response = client.query("What is the capital of France?")
    print(f"Response: {response.response}")
    print(f"Session ID: {response.session_id}")

    # Get recent events
    events = client.get_recent_events(count=5)
    print(f"\nRecent events: {len(events)}")
    for event in events:
        print(f"  - {event.type}: {event.message[:50]}...")

    client.close()


def example_streaming_usage():
    """Example of streaming client usage."""
    print("\n=== Streaming Client Usage ===")

    client = StreamingClaudeClient()

    # Register event handlers
    client.on_thinking(lambda e: print(f"💡 Thinking: {e.message}"))
    client.on_tool_use(
        lambda e: print(f"🛠️  Tool: {e.data.get('tool_name', 'unknown')}")
    )
    client.on_tool_result(lambda e: print(f"📦 Result: {e.message[:50]}..."))
    client.on_complete(lambda e: print(f"✅ Complete: {e.message}"))

    # Start streaming
    client.start_streaming()

    # Send queries
    response1 = client.query("List 3 interesting facts about Python")
    print(f"\nResponse 1: {response1.response[:200]}...")

    time.sleep(2)  # Let events stream

    response2 = client.query("Now explain the first fact in more detail")
    print(f"\nResponse 2: {response2.response[:200]}...")

    time.sleep(2)  # Let events stream

    # Check status
    status = client.get_status()
    print(f"\nStream Status: {status}")

    # Stop streaming
    client.stop_streaming()
    client.close()


async def example_async_usage():
    """Example of async client usage."""
    print("\n=== Async Client Usage ===")

    async with AsyncClaudeSDKClient() as client:
        # Send async query
        response = await client.query("What are the benefits of async programming?")
        print(f"Response: {response.response[:200]}...")

        # Stream via WebSocket
        print("\nStreaming via WebSocket...")

        events_received = []

        def handle_event(event: StreamEvent):
            events_received.append(event)
            print(f"WS Event: {event.type} - {event.message[:50]}...")

        # Stream for a few seconds
        websocket_task = asyncio.create_task(
            client.stream_websocket(
                event_handler=handle_event,
                event_types=["thinking_insight", "tool_use", "query_complete"],
            )
        )

        # Let it run for 5 seconds
        await asyncio.sleep(5)
        websocket_task.cancel()

        print(f"\nReceived {len(events_received)} WebSocket events")


if __name__ == "__main__":
    # Run examples
    example_basic_usage()
    example_streaming_usage()

    # Run async example
    asyncio.run(example_async_usage())
