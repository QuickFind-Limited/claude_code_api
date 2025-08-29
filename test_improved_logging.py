#!/usr/bin/env python
"""Test script to demonstrate improved logging for Claude SDK Server."""

import asyncio

from src.claude_sdk_server.models.dto import QueryRequest


async def test_improved_logging():
    """Test the improved logging with a sample query."""
    from src.claude_sdk_server.services.claude_service import get_claude_service

    service = get_claude_service()

    # Test query with deep thinking
    request = QueryRequest(
        prompt="Have a deep think on how a startup in procurement could revolutionize the field thanks to AI.",
        model="claude-opus-4-1-20250805",
        max_thinking_tokens=15000,
        max_turns=30,
    )

    print("\n" + "=" * 80)
    print("TESTING IMPROVED LOGGING FOR CLAUDE SDK SERVER")
    print("=" * 80 + "\n")

    response = await service.query(request)

    print("\n" + "=" * 80)
    print("FINAL RESPONSE:")
    print("=" * 80)
    print(
        response.response[:500] + "..."
        if len(response.response) > 500
        else response.response
    )
    print("\nSession ID:", response.session_id)
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_improved_logging())
