#!/usr/bin/env python3
"""Simple script to test Claude's reasoning/thinking visibility."""

import asyncio

from claude_code_sdk import (
    AssistantMessage,
    ClaudeCodeOptions,
    ResultMessage,
    SystemMessage,
    query,
)


async def main():
    """Main function to query Claude with deep thinking enabled."""

    prompt = "Have a deep think on how a startup in procurement could revolutionize the field thanks to AI."

    # Configure options with max_thinking_tokens to enable deep thinking
    options = ClaudeCodeOptions(
        # model="claude-sonnet-4-20250514",
        model="claude-opus-4-1-20250805",
        max_thinking_tokens=50000,  # Enable deep thinking
        permission_mode="bypassPermissions",
    )

    print(f"🤔 Query: {prompt}\n")
    print("=" * 80)
    print("Streaming response from Claude...\n")

    message_count = 0
    thinking_content = []
    text_content = []

    try:
        async for message in query(prompt=prompt, options=options):
            print(message)
            print("\n" + "=" * 60)
            continue
            message_count += 1
            message_type = type(message).__name__

            if isinstance(message, SystemMessage):
                print(f"📋 System Message (#{message_count}): {message.subtype}")
                if hasattr(message, "data"):
                    print(f"   Data: {message.data}\n")

            elif isinstance(message, AssistantMessage):
                print(
                    f"🤖 Assistant Message (#{message_count}): {len(message.content)} blocks"
                )

                for i, block in enumerate(message.content):
                    block_type = type(block).__name__

                    # Debug: print all attributes
                    print(f"\n🔍 Block #{i+1} Type: {block_type}")
                    if hasattr(block, "__dict__"):
                        attrs = block.__dict__
                        print(f"   Attributes: {list(attrs.keys())}")

                        # Check for specific attributes
                        for attr_name in [
                            "thinking",
                            "text",
                            "name",
                            "input",
                            "content",
                            "result",
                        ]:
                            if attr_name in attrs:
                                value = attrs[attr_name]
                                if isinstance(value, str):
                                    print(f"   {attr_name}: {value[:200]}...")
                                else:
                                    print(f"   {attr_name}: {str(value)[:200]}...")

                    # Check for thinking blocks
                    if block_type == "ThinkingBlock" or hasattr(block, "thinking"):
                        thinking = getattr(block, "thinking", "")
                        signature = getattr(block, "signature", "")
                        print("\n💭 THINKING BLOCK FOUND!")
                        print(f"   Signature: {signature}")
                        print(f"   Thinking content ({len(thinking)} chars):")
                        print("-" * 40)
                        print(thinking[:1000])  # Print first 1000 chars
                        if len(thinking) > 1000:
                            print(f"... (truncated, {len(thinking) - 1000} more chars)")
                        print("-" * 40)
                        thinking_content.append(thinking)

                    # Check for text blocks
                    elif block_type == "TextBlock" or hasattr(block, "text"):
                        text = getattr(block, "text", str(block))
                        print(f"\n📝 Text Block ({len(text)} chars):")
                        print(text[:500])  # Print first 500 chars
                        if len(text) > 500:
                            print(f"... (truncated, {len(text) - 500} more chars)")
                        text_content.append(text)

                    # Check for tool use blocks
                    elif block_type == "ToolUseBlock" or hasattr(block, "name"):
                        tool_name = getattr(block, "name", "unknown")
                        tool_input = getattr(block, "input", {})
                        print(f"\n🛠️ Tool Use: {tool_name}")
                        print(f"   Input: {str(tool_input)[:500]}...")

                    # Check for other block types
                    else:
                        print(f"\n❓ Other Block Type: {block_type}")

            elif isinstance(message, ResultMessage):
                print(f"\n✅ Result Message (#{message_count}):")
                print(f"   Session ID: {message.session_id}")
                print(f"   Is Error: {message.is_error}")
                if message.duration_ms:
                    print(f"   Duration: {message.duration_ms/1000:.2f}s")
                if message.usage:
                    print(f"   Token Usage: {message.usage}")
                if message.total_cost_usd:
                    print(f"   Cost: ${message.total_cost_usd:.4f}")
                if message.result:
                    print(f"\n📊 Final Result ({len(message.result)} chars):")
                    print(message.result[:1000])
                    if len(message.result) > 1000:
                        print(
                            f"... (truncated, {len(message.result) - 1000} more chars)"
                        )

            else:
                print(f"\n🔷 Other Message Type: {message_type}")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()

    # Summary
    print("\n" + "=" * 80)
    print("📊 SUMMARY:")
    print(f"   Total messages: {message_count}")
    print(f"   Thinking blocks found: {len(thinking_content)}")
    print(f"   Text blocks found: {len(text_content)}")

    if thinking_content:
        total_thinking_chars = sum(len(t) for t in thinking_content)
        print(f"   Total thinking content: {total_thinking_chars} characters")

    if text_content:
        total_text_chars = sum(len(t) for t in text_content)
        print(f"   Total text content: {total_text_chars} characters")


if __name__ == "__main__":
    asyncio.run(main())
