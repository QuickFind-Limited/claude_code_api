#!/usr/bin/env python3
"""Simple test to verify API and event streaming are working."""

import asyncio
import json

import httpx


async def test_simple_query():
    """Test a simple query and print events."""

    # Test basic query
    async with httpx.AsyncClient() as client:
        # Send simple query
        print("Sending query: What is 2+2?")
        response = await client.post(
            "http://localhost:8000/api/v1/query",
            json={"prompt": "What is 2+2?"},
            timeout=30.0,
        )

        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success! Response: {data.get('response', '')[:100]}")
            print(f"   Session ID: {data.get('session_id')}")
            print(f"   Token usage: {data.get('token_usage', {})}")
        else:
            print(f"❌ Failed with status {response.status_code}")
            print(f"   Response: {response.text}")


async def test_sse_stream():
    """Test SSE streaming."""
    print("\n\nTesting SSE stream...")

    session_id = "test-session-123"

    # Start SSE connection in background
    async def collect_events():
        events = []
        async with httpx.AsyncClient() as client:
            url = f"http://localhost:8000/api/v1/stream/sse?session_id={session_id}"

            try:
                async with client.stream("GET", url, timeout=10.0) as response:
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            try:
                                event = json.loads(line[6:])
                                events.append(event["type"])
                                if event["type"] == "query_complete":
                                    break
                            except Exception:
                                pass
            except asyncio.TimeoutError:
                pass
        return events

    # Start event collection
    event_task = asyncio.create_task(collect_events())

    # Wait a bit for SSE to connect
    await asyncio.sleep(0.5)

    # Send query
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/v1/query",
            json={"prompt": "What is the capital of France?", "session_id": session_id},
            timeout=30.0,
        )

        if response.status_code == 200:
            print("✅ Query sent successfully")
        else:
            print(f"❌ Query failed: {response.status_code}")

    # Get collected events
    events = await event_task

    if events:
        print(f"✅ Collected {len(events)} events:")
        for event in events:
            print(f"   - {event}")
    else:
        print("❌ No events collected")


async def main():
    print("🧪 Testing Claude SDK Server API\n")

    # Check health
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get("http://localhost:8000/api/v1/health")
            if response.status_code == 200:
                print("✅ Server is healthy")
            else:
                print("❌ Server health check failed")
                return
        except Exception:
            print("❌ Cannot connect to server")
            return

    await test_simple_query()
    await test_sse_stream()

    print("\n✅ All basic tests completed!")


if __name__ == "__main__":
    asyncio.run(main())
