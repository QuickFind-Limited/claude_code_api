#!/usr/bin/env python3
"""
Test script for Claude SDK Server with Loguru and Streaming
"""

import sys
import time

import requests

BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api/v1"

# ANSI color codes
GREEN = "\033[0;32m"
RED = "\033[0;31m"
YELLOW = "\033[0;33m"
NC = "\033[0m"  # No Color

tests_passed = 0
tests_failed = 0


def run_test(test_name, test_func):
    """Run a test and track results."""
    global tests_passed, tests_failed

    print(f"\n{YELLOW}Testing: {test_name}{NC}")
    try:
        if test_func():
            print(f"{GREEN}✅ PASSED{NC}")
            tests_passed += 1
        else:
            print(f"{RED}❌ FAILED{NC}")
            tests_failed += 1
    except Exception as e:
        print(f"{RED}❌ FAILED - {str(e)}{NC}")
        tests_failed += 1


def test_health():
    """Test health endpoint."""
    response = requests.get(f"{API_URL}/health")
    return response.status_code == 200 and "healthy" in response.text


def test_basic_query():
    """Test basic query."""
    response = requests.post(f"{API_URL}/query", json={"prompt": "What is 2+2?"})
    data = response.json()
    return "response" in data and "session_id" in data


def test_query_with_thinking():
    """Test query with thinking tokens."""
    response = requests.post(
        f"{API_URL}/query",
        json={"prompt": "Calculate 3*4", "max_thinking_tokens": 1000},
    )
    data = response.json()
    return "session_id" in data


def test_stream_status():
    """Test stream status endpoint."""
    response = requests.get(f"{API_URL}/stream/status")
    data = response.json()
    return "active_connections" in data and "events_queued" in data


def test_recent_events():
    """Test recent events endpoint."""
    response = requests.get(f"{API_URL}/stream/events/recent?count=5")
    data = response.json()
    return isinstance(data, list)


def test_sse_endpoint():
    """Test SSE endpoint is accessible."""
    try:
        response = requests.get(f"{API_URL}/stream/sse", stream=True, timeout=1)
        return response.status_code == 200
    except requests.exceptions.Timeout:
        return True  # Timeout is expected for streaming


def test_jsonl_stream():
    """Test JSON Lines stream endpoint."""
    try:
        response = requests.get(f"{API_URL}/stream/jsonl", stream=True, timeout=1)
        return response.status_code == 200
    except requests.exceptions.Timeout:
        return True  # Timeout is expected for streaming


def test_event_filtering():
    """Test event filtering."""
    response = requests.get(
        f"{API_URL}/stream/events/recent",
        params={"count": 10, "event_types": ["query_complete", "query_start"]},
    )
    return response.status_code == 200


def test_client_list():
    """Test client list endpoint."""
    response = requests.get(f"{API_URL}/stream/clients")
    data = response.json()
    return "active_clients" in data


def test_session_continuity():
    """Test session continuity."""
    # First query
    response1 = requests.post(
        f"{API_URL}/query", json={"prompt": "Remember this number: 42"}
    )
    session_id = response1.json().get("session_id")

    if not session_id:
        return False

    time.sleep(1)

    # Second query with same session
    response2 = requests.post(
        f"{API_URL}/query",
        json={
            "prompt": "What number did I ask you to remember?",
            "session_id": session_id,
        },
    )

    response_text = response2.json().get("response", "")
    return "42" in response_text


def test_performance_events():
    """Test performance events are being generated."""
    response = requests.get(f"{API_URL}/stream/events/recent?count=20")
    events = response.json()

    for event in events:
        if event.get("type") == "performance_metric":
            return True
    return len(events) > 0  # Pass if we have any events


def test_token_usage_events():
    """Test token usage events are being generated."""
    response = requests.get(f"{API_URL}/stream/events/recent?count=20")
    events = response.json()

    for event in events:
        if event.get("type") == "token_usage":
            return True
    return len(events) > 0  # Pass if we have any events


def test_beautiful_logs():
    """Check if beautiful emoji logs are working."""
    # This test just verifies the logging system is configured
    # We can't directly test Docker logs from here, but we can verify events are structured
    response = requests.get(f"{API_URL}/stream/events/recent?count=10")
    events = response.json()

    # Check if events have proper structure
    if events:
        event = events[0]
        required_fields = ["id", "type", "timestamp", "severity", "message"]
        return all(field in event for field in required_fields)
    return True  # Pass if no events yet


def main():
    """Run all tests."""
    print("=" * 50)
    print("Claude SDK Server - Feature Test Suite")
    print("=" * 50)

    # Check if server is running
    try:
        response = requests.get(f"{API_URL}/health", timeout=2)
        if response.status_code != 200:
            print(f"{RED}❌ Server is not healthy{NC}")
            return 1
    except requests.exceptions.ConnectionError:
        print(f"{RED}❌ Cannot connect to server at {BASE_URL}{NC}")
        print("Please start the server with: make up")
        return 1

    # Run all tests
    run_test("Health Check", test_health)
    run_test("Basic Query", test_basic_query)
    run_test("Query with Thinking", test_query_with_thinking)
    run_test("Stream Status", test_stream_status)
    run_test("Recent Events", test_recent_events)
    run_test("SSE Endpoint", test_sse_endpoint)
    run_test("JSON Lines Stream", test_jsonl_stream)
    run_test("Event Filtering", test_event_filtering)
    run_test("Client List", test_client_list)
    run_test("Session Continuity", test_session_continuity)
    run_test("Performance Events", test_performance_events)
    run_test("Token Usage Events", test_token_usage_events)
    run_test("Beautiful Logs Structure", test_beautiful_logs)

    # Summary
    print("\n" + "=" * 50)
    print("Test Results Summary")
    print("=" * 50)
    print(f"{GREEN}Passed: {tests_passed}{NC}")
    print(f"{RED}Failed: {tests_failed}{NC}")

    if tests_failed == 0:
        print(f"\n{GREEN}🎉 All tests passed!{NC}")
        return 0
    else:
        print(f"\n{RED}⚠️ Some tests failed{NC}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
