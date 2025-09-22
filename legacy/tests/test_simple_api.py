#!/usr/bin/env python3
"""
Test script for the simple Claude Code API
"""

import requests

API_URL = "http://localhost:8000"


def test_api():
    # Test 1: New conversation
    print("Test 1: Starting new conversation...")
    response = requests.post(f"{API_URL}/query", json={"prompt": "What is 2 + 2?"})

    if response.status_code == 200:
        data = response.json()
        print(f"Response: {data['response']}")
        print(f"Session ID: {data['session_id']}")
        session_id = data["session_id"]
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return

    # Test 2: Continue conversation with session_id
    print("\nTest 2: Continuing conversation with session_id...")
    response = requests.post(
        f"{API_URL}/query",
        json={"prompt": "What was my previous question?", "session_id": session_id},
    )

    if response.status_code == 200:
        data = response.json()
        print(f"Response: {data['response']}")
        print(f"Session ID: {data['session_id']}")
    else:
        print(f"Error: {response.status_code} - {response.text}")


if __name__ == "__main__":
    # Check if server is running
    try:
        response = requests.get(f"{API_URL}/health")
        if response.status_code == 200:
            print("Server is healthy!\n")
            test_api()
        else:
            print("Server health check failed")
    except requests.exceptions.ConnectionError:
        print("Cannot connect to server. Make sure it's running with:")
        print("python simple_api.py")
