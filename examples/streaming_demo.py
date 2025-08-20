#!/usr/bin/env python3
"""
Complete streaming demo for Claude SDK Server.

This script demonstrates all streaming capabilities including:
- Server-Sent Events (SSE) streaming
- WebSocket connections
- JSON Lines streaming
- Event filtering and subscriptions
- Performance monitoring
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Optional

import requests
import sseclient
import websockets


class ClaudeStreamingDemo:
    """Comprehensive demo of Claude SDK Server streaming features."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api/v1"
        self.ws_url = base_url.replace("http://", "ws://").replace("https://", "wss://")

    def test_basic_query(self) -> dict:
        """Test basic query endpoint."""
        print("\n🚀 Testing Basic Query Endpoint")
        print("-" * 50)

        response = requests.post(
            f"{self.api_url}/query",
            json={
                "prompt": "What is 2+2? Explain your reasoning step by step.",
                "max_thinking_tokens": 2000,
            },
        )

        if response.status_code == 200:
            data = response.json()
            print(f"✅ Response: {data['response'][:100]}...")
            print(f"📋 Session ID: {data.get('session_id', 'N/A')}")
            return data
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
            return {}

    def test_sse_streaming(self, duration: int = 10):
        """Test Server-Sent Events streaming."""
        print("\n📡 Testing Server-Sent Events (SSE)")
        print("-" * 50)

        # Start SSE connection
        response = requests.get(
            f"{self.api_url}/stream/sse?include_performance=true",
            stream=True,
            headers={"Accept": "text/event-stream"},
        )

        client = sseclient.SSEClient(response)

        print(f"Listening for events for {duration} seconds...")
        start_time = time.time()

        event_counts = {}
        try:
            for event in client.events():
                if time.time() - start_time > duration:
                    break

                data = json.loads(event.data)
                event_type = data.get("type", "unknown")
                event_counts[event_type] = event_counts.get(event_type, 0) + 1

                # Print formatted event
                self._print_event(data)

        except KeyboardInterrupt:
            print("\n⏸️  Streaming interrupted")
        finally:
            response.close()

        print("\n📊 Event Summary:")
        for event_type, count in event_counts.items():
            print(f"  - {event_type}: {count}")

    async def test_websocket_streaming(self, duration: int = 10):
        """Test WebSocket streaming."""
        print("\n🔌 Testing WebSocket Streaming")
        print("-" * 50)

        uri = f"{self.ws_url}/api/v1/stream/ws"

        try:
            async with websockets.connect(uri) as websocket:
                print(f"Connected to WebSocket at {uri}")

                # Subscribe to specific events
                await websocket.send(
                    json.dumps(
                        {
                            "action": "subscribe",
                            "event_types": [
                                "query_start",
                                "thinking_insight",
                                "tool_use",
                                "query_complete",
                            ],
                        }
                    )
                )

                print(f"Listening for events for {duration} seconds...")
                start_time = time.time()

                while time.time() - start_time < duration:
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                        data = json.loads(message)
                        self._print_event(data)
                    except asyncio.TimeoutError:
                        # Send ping to keep connection alive
                        await websocket.send(json.dumps({"action": "ping"}))
                    except websockets.exceptions.ConnectionClosed:
                        print("❌ WebSocket connection closed")
                        break

                print("✅ WebSocket test completed")

        except Exception as e:
            print(f"❌ WebSocket error: {e}")

    def test_jsonl_streaming(self, duration: int = 10):
        """Test JSON Lines streaming."""
        print("\n📋 Testing JSON Lines Streaming")
        print("-" * 50)

        response = requests.get(
            f"{self.api_url}/stream/jsonl",
            stream=True,
        )

        print(f"Listening for events for {duration} seconds...")
        start_time = time.time()

        try:
            for line in response.iter_lines():
                if time.time() - start_time > duration:
                    break

                if line:
                    data = json.loads(line)
                    self._print_event(data)

        except KeyboardInterrupt:
            print("\n⏸️  Streaming interrupted")
        finally:
            response.close()

        print("✅ JSON Lines test completed")

    def test_filtered_streaming(self, session_id: Optional[str] = None):
        """Test streaming with filters."""
        print("\n🔍 Testing Filtered Streaming")
        print("-" * 50)

        # Get or use provided session ID
        if not session_id:
            query_result = self.test_basic_query()
            session_id = query_result.get("session_id")

        if not session_id:
            print("❌ No session ID available")
            return

        print(f"📋 Filtering events for session: {session_id[:8]}...")

        # Stream with filters
        response = requests.get(
            f"{self.api_url}/stream/sse",
            params={
                "session_id": session_id,
                "event_types": "tool_use,tool_result,thinking_insight",
                "include_performance": "false",
            },
            stream=True,
        )

        client = sseclient.SSEClient(response)

        print("Listening for filtered events...")
        event_count = 0

        try:
            for event in client.events():
                if event_count >= 5:  # Limit to 5 events
                    break

                data = json.loads(event.data)
                self._print_event(data)
                event_count += 1

        finally:
            response.close()

        print(f"✅ Received {event_count} filtered events")

    def test_concurrent_streams(self):
        """Test multiple concurrent streams."""
        print("\n🔀 Testing Concurrent Streams")
        print("-" * 50)

        # Start multiple streams
        streams = []
        for i in range(3):
            response = requests.get(
                f"{self.api_url}/stream/jsonl",
                stream=True,
            )
            streams.append((i, response))
            print(f"✅ Started stream {i+1}")

        print("Reading from all streams concurrently...")
        time.sleep(2)

        # Read one event from each stream
        for stream_id, response in streams:
            try:
                line = next(response.iter_lines())
                if line:
                    data = json.loads(line)
                    print(f"Stream {stream_id+1}: {data.get('type', 'unknown')}")
            except StopIteration:
                print(f"Stream {stream_id+1}: No events")
            finally:
                response.close()

        print("✅ Concurrent streams test completed")

    def test_stream_status(self):
        """Test stream status endpoint."""
        print("\n📊 Testing Stream Status")
        print("-" * 50)

        response = requests.get(f"{self.api_url}/stream/status")

        if response.status_code == 200:
            status = response.json()
            print("Stream Status:")
            print(f"  - Active Connections: {status['active_connections']}")
            print(f"  - Events Queued: {status['events_queued']}")
            print(f"  - Total Events Sent: {status['total_events_sent']}")
            print(f"  - Uptime: {status['uptime_seconds']:.1f} seconds")
        else:
            print(f"❌ Error: {response.status_code}")

    def test_recent_events(self, count: int = 5):
        """Test recent events endpoint."""
        print("\n📜 Testing Recent Events")
        print("-" * 50)

        response = requests.get(
            f"{self.api_url}/stream/events/recent",
            params={"count": count},
        )

        if response.status_code == 200:
            events = response.json()
            print(f"Retrieved {len(events)} recent events:")
            for event in events:
                print(
                    f"  - {event['type']}: {event['message'][:50]}..."
                    if len(event["message"]) > 50
                    else f"  - {event['type']}: {event['message']}"
                )
        else:
            print(f"❌ Error: {response.status_code}")

    def test_performance_monitoring(self):
        """Test performance monitoring with streaming."""
        print("\n⚡ Testing Performance Monitoring")
        print("-" * 50)

        # Send a query and monitor performance events
        print("Sending query and monitoring performance...")

        # Start SSE with performance events
        stream_response = requests.get(
            f"{self.api_url}/stream/sse?include_performance=true",
            stream=True,
        )

        client = sseclient.SSEClient(stream_response)

        # Send query in parallel
        requests.post(
            f"{self.api_url}/query",
            json={
                "prompt": "Calculate the first 10 Fibonacci numbers",
                "max_thinking_tokens": 3000,
            },
        )

        # Collect performance events
        performance_events = []
        start_time = time.time()

        try:
            for event in client.events():
                if time.time() - start_time > 10:  # Max 10 seconds
                    break

                data = json.loads(event.data)
                if data.get("type") in ["performance_metric", "token_usage"]:
                    performance_events.append(data)
                    self._print_event(data)

                if data.get("type") == "query_complete":
                    break

        finally:
            stream_response.close()

        print("\n📊 Performance Summary:")
        print(f"  - Total performance events: {len(performance_events)}")

        # Calculate totals
        total_duration = sum(
            e.get("duration", 0)
            for e in performance_events
            if e.get("type") == "performance_metric"
        )
        total_tokens = sum(
            e.get("total_tokens", 0)
            for e in performance_events
            if e.get("type") == "token_usage"
        )

        print(f"  - Total measured duration: {total_duration:.2f}s")
        print(f"  - Total tokens used: {total_tokens}")

    def _print_event(self, event: dict):
        """Pretty print an event."""
        event_type = event.get("type", "unknown")
        message = event.get("message", "")
        timestamp = event.get("timestamp", "")

        # Format timestamp
        if timestamp:
            try:
                dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                timestamp = dt.strftime("%H:%M:%S")
            except Exception:
                timestamp = timestamp[:19]  # Just take the time part

        # Choose emoji based on event type
        emoji_map = {
            "query_start": "🚀",
            "query_complete": "✅",
            "thinking_start": "🤔",
            "thinking_insight": "💡",
            "tool_use": "🛠️",
            "tool_result": "📦",
            "todo_identified": "📝",
            "performance_metric": "⚡",
            "token_usage": "📊",
            "system_message": "ℹ️",
            "query_error": "❌",
        }

        emoji = emoji_map.get(event_type, "📌")

        # Print formatted event
        print(f"[{timestamp}] {emoji} {event_type}: {message[:100]}")

        # Print additional data for specific events
        if event_type == "tool_use" and "input_summary" in event:
            print(f"    └─ Input: {event['input_summary'][:80]}")
        elif event_type == "tool_result" and "result_summary" in event:
            print(f"    └─ Result: {event['result_summary'][:80]}")
        elif event_type == "token_usage":
            print(
                f"    └─ Tokens: {event.get('input_tokens', 0)} in, "
                f"{event.get('output_tokens', 0)} out"
            )

    def run_all_tests(self):
        """Run all streaming tests."""
        print("\n" + "=" * 60)
        print("🎯 Claude SDK Server - Complete Streaming Demo")
        print("=" * 60)

        # Check server health first
        try:
            response = requests.get(f"{self.api_url}/health")
            if response.status_code != 200:
                print("❌ Server is not healthy. Please start the server first.")
                return
        except requests.exceptions.ConnectionError:
            print("❌ Cannot connect to server. Please start it with 'make up'")
            return

        print("✅ Server is healthy. Starting tests...")

        # Run all tests
        tests = [
            ("Basic Query", self.test_basic_query),
            ("Stream Status", self.test_stream_status),
            ("Recent Events", lambda: self.test_recent_events(5)),
            ("SSE Streaming", lambda: self.test_sse_streaming(5)),
            ("JSON Lines Streaming", lambda: self.test_jsonl_streaming(5)),
            ("Filtered Streaming", self.test_filtered_streaming),
            ("Concurrent Streams", self.test_concurrent_streams),
            ("Performance Monitoring", self.test_performance_monitoring),
        ]

        for test_name, test_func in tests:
            try:
                if asyncio.iscoroutinefunction(test_func):
                    asyncio.run(test_func())
                else:
                    test_func()
            except Exception as e:
                print(f"❌ Test '{test_name}' failed: {e}")

        # WebSocket test (async)
        try:
            print("\n🔌 Running WebSocket test...")
            asyncio.run(self.test_websocket_streaming(5))
        except Exception as e:
            print(f"❌ WebSocket test failed: {e}")

        print("\n" + "=" * 60)
        print("✅ All streaming tests completed!")
        print("=" * 60)


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Claude SDK Server Streaming Demo")
    parser.add_argument(
        "--url",
        default="http://localhost:8000",
        help="Base URL of the Claude SDK Server",
    )
    parser.add_argument(
        "--test",
        choices=[
            "all",
            "query",
            "sse",
            "websocket",
            "jsonl",
            "filtered",
            "concurrent",
            "status",
            "recent",
            "performance",
        ],
        default="all",
        help="Which test to run",
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=10,
        help="Duration for streaming tests in seconds",
    )

    args = parser.parse_args()

    demo = ClaudeStreamingDemo(args.url)

    if args.test == "all":
        demo.run_all_tests()
    elif args.test == "query":
        demo.test_basic_query()
    elif args.test == "sse":
        demo.test_sse_streaming(args.duration)
    elif args.test == "websocket":
        asyncio.run(demo.test_websocket_streaming(args.duration))
    elif args.test == "jsonl":
        demo.test_jsonl_streaming(args.duration)
    elif args.test == "filtered":
        demo.test_filtered_streaming()
    elif args.test == "concurrent":
        demo.test_concurrent_streams()
    elif args.test == "status":
        demo.test_stream_status()
    elif args.test == "recent":
        demo.test_recent_events()
    elif args.test == "performance":
        demo.test_performance_monitoring()


if __name__ == "__main__":
    main()
