#!/usr/bin/env python3
"""
Complex query testing script for Claude SDK Server frontend.
Tests various query types to ensure all features work correctly.
"""

import asyncio
import json
import time
from typing import Dict, List, Optional

import httpx
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

console = Console()

# API Configuration
API_BASE = "http://localhost:8000/api/v1"
SSE_URL = f"{API_BASE}/stream/sse"
QUERY_URL = f"{API_BASE}/query"

# Test queries covering different scenarios
TEST_QUERIES = [
    {
        "name": "Simple Question",
        "query": "What is the capital of France?",
        "expected_events": [
            "query_start",
            "session_init",
            "assistant_message",
            "token_usage",
            "query_complete",
        ],
        "category": "basic",
    },
    {
        "name": "Code Analysis with Tool Use",
        "query": "Analyze the file src/claude_sdk_server/main.py and tell me what it does",
        "expected_events": [
            "query_start",
            "session_init",
            "tool_use",
            "tool_result",
            "assistant_message",
            "token_usage",
            "query_complete",
        ],
        "category": "tools",
    },
    {
        "name": "File Creation and Execution",
        "query": "Create a Python file called test_math.py with a function that calculates fibonacci numbers, then run it to show the first 10 numbers",
        "expected_events": [
            "query_start",
            "tool_use",
            "tool_result",
            "assistant_message",
            "performance_metric",
        ],
        "category": "complex",
    },
    {
        "name": "Multi-Step Task with TODOs",
        "query": "Help me create a simple REST API endpoint. First, analyze the current FastAPI setup, then add a new /api/v1/status endpoint that returns server status",
        "expected_events": [
            "query_start",
            "thinking_start",
            "thinking_insight",
            "todo_identified",
            "tool_use",
            "decision_made",
        ],
        "category": "reasoning",
    },
    {
        "name": "Error Handling Test",
        "query": "Try to read a file that doesn't exist: /nonexistent/file.txt",
        "expected_events": [
            "query_start",
            "tool_use",
            "tool_error",
            "assistant_message",
        ],
        "category": "errors",
    },
    {
        "name": "Performance Test - Large Response",
        "query": "List all Python files in the src directory and provide a brief summary of each",
        "expected_events": [
            "query_start",
            "tool_use",
            "performance_metric",
            "token_usage",
        ],
        "category": "performance",
    },
    {
        "name": "Session Continuity Test",
        "query": "Remember this number: 42. I'll ask about it in the next query.",
        "expected_events": ["query_start", "assistant_message", "query_complete"],
        "category": "session",
        "follow_up": "What number did I ask you to remember?",
    },
]


class EventCollector:
    """Collects and analyzes events from SSE stream."""

    def __init__(self):
        self.events: List[Dict] = []
        self.event_types: set = set()
        self.start_time = None
        self.end_time = None

    def add_event(self, event: Dict):
        """Add an event to the collection."""
        self.events.append(event)
        if "type" in event:
            self.event_types.add(event["type"])

        # Track timing
        if event.get("type") == "query_start":
            self.start_time = time.time()
        elif event.get("type") == "query_complete":
            self.end_time = time.time()

    def get_summary(self) -> Dict:
        """Get summary of collected events."""
        duration = None
        if self.start_time and self.end_time:
            duration = self.end_time - self.start_time

        return {
            "total_events": len(self.events),
            "unique_types": len(self.event_types),
            "event_types": list(self.event_types),
            "duration": duration,
            "has_errors": any(
                e.get("type", "").endswith("_error") for e in self.events
            ),
            "token_usage": self._get_token_usage(),
            "tools_used": self._get_tools_used(),
        }

    def _get_token_usage(self) -> Optional[Dict]:
        """Extract token usage from events."""
        for event in self.events:
            if event.get("type") == "token_usage" and "data" in event:
                return event["data"]
        return None

    def _get_tools_used(self) -> List[str]:
        """Extract tools used from events."""
        tools = []
        for event in self.events:
            if event.get("type") == "tool_use" and "data" in event:
                tool_name = event["data"].get("tool_name")
                if tool_name and tool_name not in tools:
                    tools.append(tool_name)
        return tools


async def collect_sse_events(session_id: str, timeout: float = 30) -> EventCollector:
    """Collect events from SSE stream for a session."""
    collector = EventCollector()

    async with httpx.AsyncClient() as client:
        url = f"{SSE_URL}?session_id={session_id}"

        try:
            async with client.stream("GET", url, timeout=timeout) as response:
                start_time = time.time()

                async for line in response.aiter_lines():
                    # Check timeout
                    if time.time() - start_time > timeout:
                        break

                    # Parse SSE data
                    if line.startswith("data: "):
                        try:
                            event_data = json.loads(line[6:])
                            collector.add_event(event_data)

                            # Stop on query_complete
                            if event_data.get("type") == "query_complete":
                                break
                        except json.JSONDecodeError:
                            continue

        except (httpx.TimeoutException, httpx.ConnectError) as e:
            console.print(f"[red]SSE connection error: {e}[/red]")

    return collector


async def send_query(query: str, session_id: Optional[str] = None) -> Dict:
    """Send a query to the Claude API."""
    async with httpx.AsyncClient(timeout=60.0) as client:
        payload = {"prompt": query}
        if session_id:
            payload["session_id"] = session_id

        response = await client.post(QUERY_URL, json=payload)
        response.raise_for_status()
        return response.json()


async def test_query(test_case: Dict, session_id: Optional[str] = None) -> Dict:
    """Run a single test query and collect results."""
    console.print(f"\n[cyan]Testing: {test_case['name']}[/cyan]")
    console.print(f"[dim]Query: {test_case['query'][:100]}...[/dim]")

    # Start event collection in background
    if not session_id:
        session_id = f"test-{int(time.time())}"

    # Start collecting events
    event_task = asyncio.create_task(collect_sse_events(session_id, timeout=60))

    # Small delay to ensure SSE connection is established
    await asyncio.sleep(0.5)

    # Send query
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            task = progress.add_task("Sending query...", total=None)

            response = await send_query(test_case["query"], session_id)

            progress.update(task, description="Collecting events...")

            # Wait for events
            collector = await event_task

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        return {"test_case": test_case["name"], "success": False, "error": str(e)}

    # Analyze results
    summary = collector.get_summary()

    # Check expected events
    missing_events = []
    for expected in test_case.get("expected_events", []):
        if expected not in summary["event_types"]:
            missing_events.append(expected)

    result = {
        "test_case": test_case["name"],
        "category": test_case["category"],
        "success": len(missing_events) == 0 and not summary["has_errors"],
        "total_events": summary["total_events"],
        "event_types": summary["event_types"],
        "missing_events": missing_events,
        "has_errors": summary["has_errors"],
        "duration": summary["duration"],
        "token_usage": summary["token_usage"],
        "tools_used": summary["tools_used"],
        "response_preview": response.get("response", "")[:100] + "..."
        if response.get("response")
        else None,
    }

    # Handle follow-up query if present
    if "follow_up" in test_case and result["success"]:
        console.print(f"[dim]Follow-up: {test_case['follow_up']}[/dim]")
        follow_up_result = await test_query(
            {
                "name": f"{test_case['name']} - Follow-up",
                "query": test_case["follow_up"],
                "expected_events": ["query_start", "assistant_message"],
                "category": "session",
            },
            session_id=session_id,
        )
        result["follow_up_success"] = follow_up_result["success"]

    return result


async def run_all_tests():
    """Run all test queries and generate report."""
    console.print(
        "\n[bold cyan]🧪 Claude SDK Server - Complex Query Testing Suite[/bold cyan]\n"
    )

    results = []
    session_id = f"test-session-{int(time.time())}"

    # Group tests by category
    categories = {}
    for test in TEST_QUERIES:
        cat = test["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(test)

    # Run tests by category
    for category, tests in categories.items():
        console.print(f"\n[bold yellow]📁 Category: {category.upper()}[/bold yellow]")

        for test in tests:
            result = await test_query(test, session_id)
            results.append(result)

            # Quick result display
            if result["success"]:
                console.print(
                    f"[green]✅ PASSED[/green] - {result['total_events']} events collected"
                )
            else:
                console.print("[red]❌ FAILED[/red]")
                if result.get("missing_events"):
                    console.print(
                        f"  Missing events: {', '.join(result['missing_events'])}"
                    )
                if result.get("error"):
                    console.print(f"  Error: {result['error']}")

            # Small delay between tests
            await asyncio.sleep(1)

    # Generate summary report
    console.print("\n[bold cyan]📊 Test Results Summary[/bold cyan]\n")

    # Create results table
    table = Table(title="Test Results", show_header=True, header_style="bold magenta")
    table.add_column("Test Case", style="cyan", no_wrap=False)
    table.add_column("Category", style="yellow")
    table.add_column("Status", justify="center")
    table.add_column("Events", justify="right")
    table.add_column("Duration", justify="right")
    table.add_column("Tokens", justify="right")

    total_passed = 0
    total_failed = 0

    for result in results:
        status = "[green]✅ PASS[/green]" if result["success"] else "[red]❌ FAIL[/red]"
        if result["success"]:
            total_passed += 1
        else:
            total_failed += 1

        duration = (
            f"{result.get('duration', 0):.2f}s" if result.get("duration") else "N/A"
        )

        tokens = "N/A"
        if result["token_usage"]:
            total = result["token_usage"].get("total_tokens", 0)
            tokens = str(total)

        table.add_row(
            result["test_case"],
            result["category"],
            status,
            str(result["total_events"]),
            duration,
            tokens,
        )

    console.print(table)

    # Overall summary
    console.print("\n[bold]Overall Results:[/bold]")
    console.print(f"  [green]Passed: {total_passed}[/green]")
    console.print(f"  [red]Failed: {total_failed}[/red]")
    console.print(f"  Total: {len(results)}")
    console.print(f"  Success Rate: {(total_passed/len(results)*100):.1f}%")

    # Event type coverage
    all_event_types = set()
    for result in results:
        all_event_types.update(result["event_types"])

    console.print(f"\n[bold]Event Types Observed ({len(all_event_types)}):[/bold]")
    for event_type in sorted(all_event_types):
        emoji = get_event_emoji(event_type)
        console.print(f"  {emoji} {event_type}")

    # Tools usage
    all_tools = set()
    for result in results:
        all_tools.update(result.get("tools_used", []))

    if all_tools:
        console.print(f"\n[bold]Tools Used ({len(all_tools)}):[/bold]")
        for tool in sorted(all_tools):
            console.print(f"  🛠️ {tool}")

    return total_passed == len(results)


def get_event_emoji(event_type: str) -> str:
    """Get emoji for event type."""
    emoji_map = {
        "query_start": "🚀",
        "query_complete": "✅",
        "query_error": "❌",
        "session_init": "🔧",
        "thinking_start": "🤔",
        "thinking_insight": "💡",
        "tool_use": "🛠️",
        "tool_result": "📦",
        "tool_error": "⚠️",
        "todo_identified": "📝",
        "decision_made": "🎯",
        "step_progress": "📈",
        "system_message": "ℹ️",
        "assistant_message": "🤖",
        "performance_metric": "⚡",
        "token_usage": "📊",
    }
    return emoji_map.get(event_type, "📌")


async def test_event_filtering():
    """Test the event filtering functionality in the frontend."""
    console.print("\n[bold cyan]🔍 Testing Event Filtering[/bold cyan]\n")

    # Send a query that generates multiple event types
    session_id = f"filter-test-{int(time.time())}"
    query = "Create a file test.txt with 'Hello World', then read it back"

    console.print("Sending query to generate diverse events...")

    # Collect events
    event_task = asyncio.create_task(collect_sse_events(session_id, timeout=30))
    await asyncio.sleep(0.5)

    await send_query(query, session_id)
    collector = await event_task

    summary = collector.get_summary()

    console.print(
        f"\nGenerated {summary['total_events']} events of {len(summary['event_types'])} types"
    )
    console.print("\n[yellow]To test filtering in the frontend:[/yellow]")
    console.print("1. Open http://localhost:3000")
    console.print("2. Send the same query")
    console.print("3. Click on the filter pills to toggle event types:")

    for event_type in sorted(summary["event_types"]):
        emoji = get_event_emoji(event_type)
        console.print(f"   {emoji} {event_type}")

    console.print("\n4. Verify that:")
    console.print("   - Clicking a filter hides/shows those event types")
    console.print("   - Multiple filters can be active simultaneously")
    console.print("   - The 'All Events' filter shows everything")
    console.print("   - Filter states persist during the session")


async def main():
    """Main test runner."""
    try:
        # Check if server is running
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{API_BASE}/health")
            response.raise_for_status()
            console.print("[green]✅ Server is running[/green]")
    except Exception:
        console.print(
            "[red]❌ Server is not running. Please start it with 'make up'[/red]"
        )
        return

    # Run comprehensive tests
    success = await run_all_tests()

    # Test event filtering
    await test_event_filtering()

    if success:
        console.print("\n[bold green]🎉 All tests passed successfully![/bold green]")
        console.print("\n[cyan]Next steps:[/cyan]")
        console.print("1. Open http://localhost:3000 in your browser")
        console.print("2. Try the test queries manually")
        console.print("3. Observe real-time event streaming")
        console.print("4. Test event filtering and performance metrics")
    else:
        console.print(
            "\n[bold red]⚠️ Some tests failed. Please review the results above.[/bold red]"
        )


if __name__ == "__main__":
    asyncio.run(main())
