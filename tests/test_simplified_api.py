#!/usr/bin/env python3
"""Test script for the simplified Claude SDK API."""

import asyncio

import httpx


async def test_api():
    """Test the simplified API endpoints."""
    base_url = "http://localhost:8000"

    async with httpx.AsyncClient() as client:
        # Test health endpoint
        print("Testing /api/v1/health...")
        response = await client.get(f"{base_url}/api/v1/health")
        print(f"Health check: {response.json()}\n")

        # Test query endpoint - new conversation
        print("Testing /api/v1/query (new conversation)...")
        query_data = {"prompt": "Hello, can you help me with Python?"}
        response = await client.post(f"{base_url}/api/v1/query", json=query_data)
        result = response.json()
        print(f"Response: {result['response'][:100]}...")
        print(f"Session ID: {result['session_id']}\n")

        # Test query endpoint - continue conversation
        print("Testing /api/v1/query (continue conversation)...")
        query_data = {
            "prompt": "What about async programming?",
            "session_id": result["session_id"],
        }
        response = await client.post(f"{base_url}/api/v1/query", json=query_data)
        result = response.json()
        print(f"Response: {result['response'][:100]}...")
        print(f"Session ID: {result['session_id']}")


if __name__ == "__main__":
    print("Simplified Claude SDK API Test\n")
    print("Make sure the server is running with:")
    print("  uv run python -m src.claude_sdk_server.main")
    print("  or")
    print("  uv run uvicorn src.claude_sdk_server.main:app --reload\n")

    asyncio.run(test_api())
