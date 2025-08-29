#!/usr/bin/env python3
"""Simple script to test Claude's native reasoning/thinking visibility without tools."""

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

    # Use a math problem to encourage thinking
    prompt = "Think step by step: What is 47 * 83? Show your reasoning process."

    # Configure options with max_thinking_tokens to enable deep thinking
    # Use a model that supports thinking
    options = ClaudeCodeOptions(
        model="claude-3-5-sonnet-20241022",  # Try different models
        max_thinking_tokens=20000,  # Enable deep thinking
        permission_mode="bypassPermissions",
        max_turns=1,  # Single turn to avoid tool use
    )

    print(f"🤔 Query: {prompt}\n")
    print("=" * 80)
    print("Streaming response from Claude...\n")

    message_count = 0
    thinking_found = False

    try:
        async for message in query(prompt=prompt, options=options):
            message_count += 1
            message_type = type(message).__name__

            if isinstance(message, SystemMessage):
                print(f"📋 System Message (#{message_count}): {message.subtype}")

            elif isinstance(message, AssistantMessage):
                print(
                    f"\n🤖 Assistant Message (#{message_count}): {len(message.content)} blocks"
                )

                for i, block in enumerate(message.content):
                    block_type = type(block).__name__

                    # Check all block attributes
                    print(f"\n   Block #{i+1} - Type: {block_type}")

                    # Try to access different attributes
                    if hasattr(block, "__dict__"):
                        attrs = block.__dict__
                        print(f"   Attributes available: {list(attrs.keys())}")

                        # Check for thinking attribute specifically
                        if "thinking" in attrs:
                            thinking_found = True
                            thinking = attrs["thinking"]
                            print("\n   💭💭💭 THINKING FOUND! 💭💭💭")
                            print(f"   Length: {len(thinking)} characters")
                            print("   Content preview:")
                            print("   " + "-" * 40)
                            print(f"   {thinking[:500]}")
                            if len(thinking) > 500:
                                print(f"   ... ({len(thinking) - 500} more characters)")
                            print("   " + "-" * 40)

                        # Check for text attribute
                        if "text" in attrs:
                            text = attrs["text"]
                            print(f"\n   📝 Text content ({len(text)} chars):")
                            print(f"   {text[:300]}")
                            if len(text) > 300:
                                print(f"   ... ({len(text) - 300} more characters)")

                    # Alternative check using getattr
                    if hasattr(block, "thinking"):
                        thinking = getattr(block, "thinking", "")
                        if thinking:
                            thinking_found = True
                            print(
                                f"\n   🧠 Thinking via getattr: {len(thinking)} chars"
                            )

            elif isinstance(message, ResultMessage):
                print(f"\n✅ Result Message (#{message_count}):")
                print(f"   Session ID: {message.session_id}")
                if message.duration_ms:
                    print(f"   Duration: {message.duration_ms/1000:.2f}s")
                if message.usage:
                    usage = message.usage
                    print(f"   Tokens: {usage}")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()

    # Summary
    print("\n" + "=" * 80)
    print("📊 SUMMARY:")
    print(f"   Total messages: {message_count}")
    print(f"   Thinking blocks found: {'✅ YES' if thinking_found else '❌ NO'}")

    if not thinking_found:
        print("\n⚠️  No thinking blocks detected!")
        print("   Possible reasons:")
        print("   - The model might not expose thinking through the SDK")
        print("   - Thinking might be internal only")
        print("   - Different model or parameters might be needed")


if __name__ == "__main__":
    asyncio.run(main())
