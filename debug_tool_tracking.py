#!/usr/bin/env python
"""
Debug script to understand the message format from Claude Code SDK
"""

import asyncio
import os
from claude_code_sdk import ClaudeSDKClient, ClaudeCodeOptions
import json

async def debug_messages():
    """Debug the message format from Claude Code SDK."""
    
    # Set up client with MCP tools enabled
    options = ClaudeCodeOptions(
        model="claude-sonnet-4-20250514",
        system_prompt="You are a helpful assistant. Use tools as much as possible.",
        max_turns=100,
        allowed_tools=[
            # Basic tools
            "Read", "Write", "WebSearch", "WebFetch",
            # MCP tools
            "mcp__perplexity-ask",
            "mcp__context7",
            "mcp__Firecrawl"
        ]
    )
    
    client = ClaudeSDKClient(options=options)
    
    print("🔍 Starting debug session...")
    print("=" * 60)
    
    async with client:
        # Send a query that should use tools
        prompt = "Use Perplexity to search for information about Python 3.12 features"
        print(f"📤 Sending: {prompt}")
        print("=" * 60)
        
        await client.query(prompt)
        
        message_count = 0
        async for message in client.receive_response():
            message_count += 1
            print(f"\n📨 Message #{message_count}")
            print(f"Type: {type(message).__name__}")
            print(f"Module: {type(message).__module__}")
            
            # Print all attributes
            print("\nAttributes:")
            for attr in dir(message):
                if not attr.startswith('_'):
                    try:
                        value = getattr(message, attr)
                        if not callable(value):
                            value_str = str(value)[:200]
                            print(f"  {attr}: {value_str}")
                    except:
                        pass
            
            # Special handling for common message types
            if hasattr(message, '__dict__'):
                print("\nDirect attributes (__dict__):")
                print(json.dumps(message.__dict__, indent=2, default=str)[:500])
            
            print("-" * 40)
            
            # Stop after a few messages to avoid spam
            if message_count > 10:
                print("\n... (stopping after 10 messages)")
                break
    
    print(f"\n✅ Debug complete. Total messages received: {message_count}")

if __name__ == "__main__":
    asyncio.run(debug_messages())
