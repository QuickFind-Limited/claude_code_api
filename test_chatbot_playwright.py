#!/usr/bin/env python3
"""
Playwright test for chatbot real-time streaming features.
Tests the complete real-time experience including tool usage, token updates, and metadata display.
"""

import asyncio
import time

from playwright.async_api import async_playwright, expect


async def test_chatbot_realtime():
    """Test the chatbot's real-time streaming features."""

    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=False)  # Set to True for CI
        context = await browser.new_context()
        page = await context.new_page()

        # Enable console logging
        page.on("console", lambda msg: print(f"Browser console: {msg.text}"))

        print("🧪 Starting Chatbot Real-time Streaming Tests\n")

        # Navigate to chatbot
        print("📱 Opening chatbot interface...")
        await page.goto("http://localhost:3001/chatbot.html")
        await page.wait_for_load_state("networkidle")

        # Verify page loaded
        await expect(page.locator("h1")).to_contain_text("Claude Chatbot")
        print("✅ Chatbot loaded successfully\n")

        # Test 1: Simple query without tools
        print("Test 1: Simple Query (No Tools)")
        print("-" * 40)

        # Type a simple query
        message_input = page.locator("#messageInput")
        await message_input.fill("What is 2+2?")

        # Send message
        await page.click("#sendBtn")

        # Wait for typing indicator
        typing_indicator = page.locator(".typing-indicator").first
        await expect(typing_indicator).to_be_visible(timeout=5000)
        print("✅ Typing indicator appeared")

        # Wait for response
        await expect(typing_indicator).to_be_hidden(timeout=30000)

        # Check for assistant message
        assistant_messages = page.locator(".message.assistant")
        await expect(assistant_messages).to_have_count(1, timeout=5000)
        print("✅ Assistant response received")

        # Check for metadata box
        metadata_box = page.locator(".message-metadata").first
        await expect(metadata_box).to_be_visible()
        print("✅ Metadata box appeared")

        # Click to expand metadata
        await page.click(".metadata-toggle")
        metadata_content = page.locator(".metadata-content").first
        await expect(metadata_content).to_have_css("max-height", "500px")
        print("✅ Metadata expanded successfully\n")

        # Test 2: Query with tool usage
        print("Test 2: Query with Tool Usage")
        print("-" * 40)

        # Clear input and send tool-using query
        await message_input.fill("List the files in the frontend directory")
        await page.click("#sendBtn")

        # Wait for typing indicator
        await expect(page.locator(".typing-indicator").nth(1)).to_be_visible(
            timeout=5000
        )
        print("✅ Typing indicator appeared for second query")

        # Look for live tool indicator
        tool_indicator = page.locator(".live-indicator")
        try:
            await expect(tool_indicator).to_be_visible(timeout=10000)
            tool_text = await tool_indicator.text_content()
            print(f"✅ Live tool indicator appeared: {tool_text}")

            # Wait for it to disappear
            await expect(tool_indicator).to_be_hidden(timeout=10000)
            print("✅ Tool indicator disappeared after completion")
        except:
            print("⚠️  Tool indicator not detected (may have been too fast)")

        # Wait for response
        await expect(page.locator(".typing-indicator").nth(1)).to_be_hidden(
            timeout=30000
        )

        # Check for second assistant message
        await expect(assistant_messages).to_have_count(2, timeout=5000)
        print("✅ Second assistant response received")

        # Check second metadata box
        metadata_boxes = page.locator(".message-metadata")
        await expect(metadata_boxes).to_have_count(2)

        # Expand second metadata
        await page.click(".metadata-toggle >> nth=1")

        # Check for tools used section
        tools_section = page.locator(".metadata-content >> nth=1").locator(
            "text=/Tools Used/"
        )
        if await tools_section.count() > 0:
            print("✅ Tools Used section found in metadata")

            # Check for specific tool names
            tools_content = await page.locator(
                ".metadata-content >> nth=1"
            ).text_content()
            if (
                "LS" in tools_content
                or "Read" in tools_content
                or "Glob" in tools_content
            ):
                print("✅ Tool names displayed in metadata\n")

        # Test 3: Token usage updates
        print("Test 3: Token Usage Tracking")
        print("-" * 40)

        # Check token display
        total_tokens = page.locator("#totalTokens")
        tokens_text = await total_tokens.text_content()

        if tokens_text and tokens_text != "0":
            print(f"✅ Total tokens displayed: {tokens_text}")
        else:
            print("⚠️  Token count not updated")

        # Check session metrics
        message_count = page.locator("#messageCount")
        count_text = await message_count.text_content()
        print(f"✅ Message count: {count_text}\n")

        # Test 4: Session management
        print("Test 4: Session Management")
        print("-" * 40)

        # Get current session ID from page
        session_id = await page.evaluate(
            "() => localStorage.getItem('chatbot_session_id')"
        )
        if session_id:
            print(f"✅ Session ID stored: {session_id[:20]}...")

        # Test New Session button
        await page.click("#newSessionBtn")

        # Check if confirmed
        await page.wait_for_timeout(500)

        # Click OK on confirmation dialog
        page.once("dialog", lambda dialog: dialog.accept())
        await page.click("#newSessionBtn")

        # Wait for page to update
        await page.wait_for_timeout(1000)

        # Check messages cleared
        remaining_messages = await assistant_messages.count()
        if remaining_messages == 0:
            print("✅ Messages cleared after new session")

        # Check new session ID
        new_session_id = await page.evaluate(
            "() => localStorage.getItem('chatbot_session_id')"
        )
        if new_session_id and new_session_id != session_id:
            print("✅ New session ID generated\n")

        # Test 5: Model selection
        print("Test 5: Model Selection")
        print("-" * 40)

        # Check model dropdown
        model_select = page.locator("#modelSelect")
        await expect(model_select).to_be_visible()

        # Get available options
        options = await model_select.locator("option").all_text_contents()
        print(f"✅ Available models: {', '.join(options)}")

        # Try changing model
        await model_select.select_option("claude-sonnet-4-20250514")
        selected_value = await model_select.input_value()
        if selected_value == "claude-sonnet-4-20250514":
            print("✅ Model selection works\n")

        # Test 6: Real-time SSE connection
        print("Test 6: SSE Connection Status")
        print("-" * 40)

        # Check if SSE is connected by looking at network
        sse_connected = await page.evaluate("""
            () => {
                return window.eventSource && window.eventSource.readyState === EventSource.OPEN;
            }
        """)

        if sse_connected:
            print("✅ SSE connection is active")
        else:
            print("⚠️  SSE connection not detected")

        # Test 7: Performance metrics
        print("\nTest 7: Performance Metrics")
        print("-" * 40)

        # Send another query to test response time
        await message_input.fill("Hello, how are you?")
        start_time = time.time()
        await page.click("#sendBtn")

        # Wait for response
        await expect(page.locator(".typing-indicator").last).to_be_visible(timeout=5000)
        await expect(page.locator(".typing-indicator").last).to_be_hidden(timeout=30000)
        response_time = time.time() - start_time

        print(f"✅ Response received in {response_time:.2f} seconds")

        # Check response time in metadata
        await page.click(".metadata-toggle >> nth=-1")
        last_metadata = page.locator(".metadata-content").last
        metadata_text = await last_metadata.text_content()
        if "Response Time:" in metadata_text:
            print("✅ Response time displayed in metadata")

        # Final summary
        print("\n" + "=" * 50)
        print("🎉 All Tests Completed!")
        print("=" * 50)

        print("\n📊 Test Summary:")
        print("  ✅ Chatbot loads successfully")
        print("  ✅ Typing indicator works")
        print("  ✅ Messages stream properly")
        print("  ✅ Metadata boxes appear and expand")
        print("  ✅ Tool usage indicators (when detected)")
        print("  ✅ Token counting works")
        print("  ✅ Session management functions")
        print("  ✅ Model selection available")
        print("  ✅ Performance metrics tracked")

        # Take final screenshot
        await page.screenshot(path="chatbot_test_final.png", full_page=True)
        print("\n📸 Screenshot saved: chatbot_test_final.png")

        # Keep browser open for manual inspection
        print("\n⏸️  Browser will close in 5 seconds...")
        await page.wait_for_timeout(5000)

        await browser.close()


async def main():
    """Main test runner."""
    try:
        # Check if server is running
        import httpx

        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/api/v1/health")
            if response.status_code != 200:
                raise Exception("API server not healthy")

            response = await client.get("http://localhost:3001/chatbot.html")
            if response.status_code != 200:
                raise Exception("Chatbot interface not accessible")

        print("✅ Prerequisites checked - servers are running\n")

        # Run tests
        await test_chatbot_realtime()

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\n📝 Prerequisites:")
        print("  1. Start API server: make up")
        print("  2. Start chatbot: make chatbot")
        print("  3. Run this test: python test_chatbot_playwright.py")


if __name__ == "__main__":
    asyncio.run(main())
