"""Core event streaming system for real-time event delivery.

This module provides a comprehensive streaming solution for delivering Claude SDK events
in real-time to multiple clients through various protocols (SSE, WebSocket, JSON Lines).

Features:
- Thread-safe event queue management
- Multiple concurrent client support
- Event filtering and subscription management
- Automatic client cleanup and error handling
- Production-ready with proper resource management
"""

import asyncio
import json
import time
from collections import deque
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import AsyncGenerator, Dict, List, Optional, Set
from weakref import WeakSet

from fastapi import WebSocket, WebSocketDisconnect

from ..models.events import (
    BaseEvent,
    EventStreamStatus,
    EventSubscription,
    EventType,
    StreamingEvent,
)
from ..utils.logging_config import get_logger

# Configure logger for this module
stream_logger = get_logger(__name__)


class EventQueue:
    """Thread-safe event queue with size limits and cleanup."""

    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self._queue: deque = deque(maxlen=max_size)
        self._lock = asyncio.Lock()
        self._subscribers: Set[asyncio.Queue] = set()
        self._creation_time = time.time()

    async def put(self, event: StreamingEvent) -> None:
        """Add an event to the queue and notify all subscribers."""
        async with self._lock:
            self._queue.append(event)

            # Notify all active subscribers
            dead_queues = set()
            for subscriber_queue in self._subscribers.copy():
                try:
                    if not subscriber_queue.full():
                        await subscriber_queue.put(event)
                    else:
                        # Queue is full, skip this subscriber but keep them registered
                        stream_logger.warning(
                            f"Subscriber queue full, skipping event {event.id}"
                        )
                except Exception as e:
                    stream_logger.warning(f"Failed to notify subscriber: {e}")
                    dead_queues.add(subscriber_queue)

            # Clean up dead queues
            self._subscribers -= dead_queues

    async def subscribe(self, subscriber_queue: asyncio.Queue) -> None:
        """Subscribe a queue to receive events."""
        async with self._lock:
            self._subscribers.add(subscriber_queue)
            stream_logger.debug(
                f"New subscriber added, total: {len(self._subscribers)}"
            )

    async def unsubscribe(self, subscriber_queue: asyncio.Queue) -> None:
        """Unsubscribe a queue from receiving events."""
        async with self._lock:
            self._subscribers.discard(subscriber_queue)
            stream_logger.debug(f"Subscriber removed, total: {len(self._subscribers)}")

    async def get_recent(self, count: int = 100) -> List[StreamingEvent]:
        """Get recent events from the queue."""
        async with self._lock:
            return list(self._queue)[-count:] if count > 0 else []

    def size(self) -> int:
        """Get current queue size."""
        return len(self._queue)

    def subscriber_count(self) -> int:
        """Get number of active subscribers."""
        return len(self._subscribers)

    def uptime(self) -> float:
        """Get uptime in seconds."""
        return time.time() - self._creation_time


class ClientConnection:
    """Represents a client connection with filtering and state management."""

    def __init__(
        self,
        client_id: str,
        subscription: EventSubscription,
        connection_type: str = "unknown",
    ):
        self.client_id = client_id
        self.subscription = subscription
        self.connection_type = connection_type
        self.connected_at = datetime.utcnow()
        self.last_activity = datetime.utcnow()
        self.events_sent = 0
        self.queue: asyncio.Queue = asyncio.Queue(maxsize=100)
        self.is_active = True

    def matches_filter(self, event: StreamingEvent) -> bool:
        """Check if event matches client's subscription filters."""
        # Session filter
        if (
            self.subscription.session_id
            and event.session_id != self.subscription.session_id
        ):
            return False

        # Event type filter
        if (
            self.subscription.event_types
            and event.type not in self.subscription.event_types
        ):
            return False

        # Severity filter
        if (
            self.subscription.severity_filter
            and event.severity not in self.subscription.severity_filter
        ):
            return False

        # System events filter
        if not self.subscription.include_system_events and event.type in [
            EventType.SYSTEM_MESSAGE,
            EventType.ASSISTANT_MESSAGE,
        ]:
            return False

        # Performance events filter
        if not self.subscription.include_performance_events and event.type in [
            EventType.PERFORMANCE_METRIC,
            EventType.TOKEN_USAGE,
        ]:
            return False

        return True

    async def send_event(self, event: StreamingEvent) -> bool:
        """Send event to client if it matches filters."""
        if not self.is_active or not self.matches_filter(event):
            return False

        try:
            if not self.queue.full():
                await self.queue.put(event)
                self.events_sent += 1
                self.last_activity = datetime.utcnow()
                return True
            else:
                stream_logger.warning(
                    f"Client {self.client_id} queue full, dropping event"
                )
                return False
        except Exception as e:
            stream_logger.error(f"Failed to send event to client {self.client_id}: {e}")
            self.is_active = False
            return False

    async def get_event(self, timeout: float = 30.0) -> Optional[StreamingEvent]:
        """Get next event for this client with timeout."""
        try:
            return await asyncio.wait_for(self.queue.get(), timeout=timeout)
        except asyncio.TimeoutError:
            return None
        except Exception as e:
            stream_logger.error(f"Error getting event for client {self.client_id}: {e}")
            return None

    def disconnect(self):
        """Mark client as disconnected."""
        self.is_active = False
        # Clear the queue to free memory
        while not self.queue.empty():
            try:
                self.queue.get_nowait()
            except asyncio.QueueEmpty:
                break


class EventStreamManager:
    """Central manager for all event streaming operations."""

    def __init__(self):
        self.event_queue = EventQueue(max_size=10000)
        self.clients: Dict[str, ClientConnection] = {}
        self.websocket_connections: WeakSet[WebSocket] = WeakSet()
        self.total_events_sent = 0
        self.start_time = time.time()

        # Start background cleanup task
        self._cleanup_task = None
        # Will be started when first client connects

    def _start_cleanup_task(self):
        """Start background task for cleaning up inactive clients."""
        if self._cleanup_task is None:
            try:
                loop = asyncio.get_running_loop()
                self._cleanup_task = loop.create_task(self._cleanup_inactive_clients())
            except RuntimeError:
                # No running loop yet, will be started later
                pass

    async def _cleanup_inactive_clients(self):
        """Background task to clean up inactive clients."""
        while True:
            try:
                await asyncio.sleep(60)  # Run every minute

                current_time = datetime.utcnow()
                inactive_clients = []

                for client_id, client in self.clients.items():
                    # Remove clients inactive for more than 30 minutes
                    if (
                        not client.is_active
                        or current_time - client.last_activity > timedelta(minutes=30)
                    ):
                        inactive_clients.append(client_id)

                for client_id in inactive_clients:
                    await self.disconnect_client(client_id)
                    stream_logger.info(f"Cleaned up inactive client: {client_id}")

            except Exception as e:
                stream_logger.error(f"Error in cleanup task: {e}")
                await asyncio.sleep(10)  # Wait before retrying

    async def emit_event(self, event: StreamingEvent) -> None:
        """Emit an event to all subscribers."""
        # Add to main queue
        await self.event_queue.put(event)

        # Send to active clients
        disconnected_clients = []
        for client_id, client in self.clients.items():
            success = await client.send_event(event)
            if not success and not client.is_active:
                disconnected_clients.append(client_id)

        # Clean up disconnected clients
        for client_id in disconnected_clients:
            await self.disconnect_client(client_id)

        self.total_events_sent += len(self.clients)

        # Emit to WebSocket connections
        await self._emit_to_websockets(event)

    async def _emit_to_websockets(self, event: StreamingEvent) -> None:
        """Emit event to active WebSocket connections."""
        if not self.websocket_connections:
            return

        event_data = event.dict()
        message = json.dumps(event_data)

        # Use a copy of the set to avoid modification during iteration
        connections_copy = list(self.websocket_connections)

        for ws in connections_copy:
            try:
                if ws.application_state.CONNECTED:
                    await ws.send_text(message)
                else:
                    # WebSocket is no longer connected, it will be garbage collected
                    pass
            except Exception as e:
                stream_logger.warning(f"Failed to send to WebSocket: {e}")

    async def connect_client(
        self, subscription: EventSubscription, connection_type: str = "sse"
    ) -> ClientConnection:
        """Connect a new client with subscription parameters."""
        # Start cleanup task if not already running
        self._start_cleanup_task()

        client = ClientConnection(
            client_id=subscription.client_id,
            subscription=subscription,
            connection_type=connection_type,
        )

        self.clients[client.client_id] = client

        # Subscribe to event queue
        await self.event_queue.subscribe(client.queue)

        stream_logger.info(
            f"Client {client.client_id} connected via {connection_type}, "
            f"total clients: {len(self.clients)}"
        )

        return client

    async def disconnect_client(self, client_id: str) -> None:
        """Disconnect a client and clean up resources."""
        client = self.clients.get(client_id)
        if client:
            await self.event_queue.unsubscribe(client.queue)
            client.disconnect()
            del self.clients[client_id]

            stream_logger.info(
                f"Client {client_id} disconnected, total clients: {len(self.clients)}"
            )

    def add_websocket(self, websocket: WebSocket) -> None:
        """Add a WebSocket connection to the manager."""
        self.websocket_connections.add(websocket)
        stream_logger.info(
            f"WebSocket connected, total: {len(self.websocket_connections)}"
        )

    def remove_websocket(self, websocket: WebSocket) -> None:
        """Remove a WebSocket connection from the manager."""
        self.websocket_connections.discard(websocket)
        stream_logger.info(
            f"WebSocket disconnected, total: {len(self.websocket_connections)}"
        )

    async def get_client_stream(
        self, client_id: str
    ) -> AsyncGenerator[StreamingEvent, None]:
        """Get an async generator for client events."""
        client = self.clients.get(client_id)
        if not client:
            stream_logger.error(f"Client {client_id} not found")
            return

        try:
            while client.is_active:
                event = await client.get_event(timeout=30.0)
                if event:
                    yield event
                else:
                    # Send heartbeat/keepalive
                    yield BaseEvent(
                        type=EventType.SYSTEM_MESSAGE,
                        message="heartbeat",
                        data={
                            "type": "heartbeat",
                            "timestamp": datetime.utcnow().isoformat(),
                        },
                    )
        except Exception as e:
            stream_logger.error(f"Error in client stream {client_id}: {e}")
        finally:
            await self.disconnect_client(client_id)

    async def get_sse_stream(self, client_id: str) -> AsyncGenerator[str, None]:
        """Get Server-Sent Events formatted stream."""
        async for event in self.get_client_stream(client_id):
            # Format as SSE
            event_data = event.dict()
            event_json = json.dumps(event_data)

            sse_data = f"id: {event.id}\n"
            sse_data += f"event: {event.type.value if hasattr(event.type, 'value') else event.type}\n"
            sse_data += f"data: {event_json}\n\n"

            yield sse_data

    async def get_jsonl_stream(self, client_id: str) -> AsyncGenerator[str, None]:
        """Get JSON Lines formatted stream."""
        async for event in self.get_client_stream(client_id):
            # Format as JSON Lines
            event_data = event.dict()
            yield json.dumps(event_data) + "\n"

    def get_status(self) -> EventStreamStatus:
        """Get current streaming status."""
        return EventStreamStatus(
            active_connections=len(self.clients) + len(self.websocket_connections),
            events_queued=self.event_queue.size(),
            total_events_sent=self.total_events_sent,
            uptime_seconds=time.time() - self.start_time,
        )

    async def get_recent_events(
        self,
        count: int = 100,
        event_types: Optional[List[EventType]] = None,
        session_id: Optional[str] = None,
    ) -> List[StreamingEvent]:
        """Get recent events with optional filtering."""
        events = await self.event_queue.get_recent(count)

        if event_types or session_id:
            filtered_events = []
            for event in events:
                if event_types and event.type not in event_types:
                    continue
                if session_id and event.session_id != session_id:
                    continue
                filtered_events.append(event)
            return filtered_events

        return events

    async def shutdown(self):
        """Gracefully shutdown the event stream manager."""
        stream_logger.info("Shutting down EventStreamManager...")

        # Cancel cleanup task
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        # Disconnect all clients
        client_ids = list(self.clients.keys())
        for client_id in client_ids:
            await self.disconnect_client(client_id)

        # Close WebSocket connections
        connections_copy = list(self.websocket_connections)
        for ws in connections_copy:
            try:
                if ws.application_state.CONNECTED:
                    await ws.close()
            except Exception:
                pass  # Connection might already be closed

        stream_logger.info("EventStreamManager shutdown complete")


# Global event stream manager instance
_event_manager: Optional[EventStreamManager] = None


def get_event_manager() -> EventStreamManager:
    """Get or create the global event stream manager."""
    global _event_manager
    if _event_manager is None:
        _event_manager = EventStreamManager()
    return _event_manager


async def emit_event(event: StreamingEvent) -> None:
    """Convenience function to emit an event through the global manager."""
    manager = get_event_manager()
    await manager.emit_event(event)


@asynccontextmanager
async def websocket_connection(websocket: WebSocket):
    """Context manager for WebSocket connections."""
    manager = get_event_manager()
    manager.add_websocket(websocket)

    try:
        yield
    except WebSocketDisconnect:
        pass
    except Exception as e:
        stream_logger.error(f"WebSocket error: {e}")
    finally:
        manager.remove_websocket(websocket)


# Export key functions and classes
__all__ = [
    "EventQueue",
    "ClientConnection",
    "EventStreamManager",
    "get_event_manager",
    "emit_event",
    "websocket_connection",
]
