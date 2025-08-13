#!/usr/bin/env python
"""
Comprehensive test script for Claude SDK Server tool tracking functionality.
Tests MCP tools integration and proper tool usage tracking.
"""

import asyncio
import aiohttp
import json
import sys
from typing import Dict, Any, List
from datetime import datetime

# Server configuration
SERVER_URL = "http://localhost:8008"
API_BASE = f"{SERVER_URL}/api/v1"

# Test cases configuration
TEST_CASES = [
    {
        "name": "Test 1: List Available Tools",
        "description": "Check if Claude can see all tools including MCP tools",
        "request": {
            "prompt": "Can you list all the tools you have access to? Please check if you can use MCP tools like perplexity, context7, Firecrawl, and odoo_mcp.",
            "model": "sonnet",
            "max_tokens": 1000
        },
        "expected_tools": [],  # Should not use tools, just list them
        "validate_response": lambda r: all(tool in r.lower() for tool in ["perplexity", "context7", "firecrawl", "odoo"])
    },
    {
        "name": "Test 2: Use Perplexity for Web Search",
        "description": "Test if Claude can use Perplexity MCP tool for web search",
        "request": {
            "prompt": "Use Perplexity to search for the latest news about AI developments in 2025. Please provide a brief summary.",
            "model": "sonnet",
            "max_tokens": 2000
        },
        "expected_tools": ["mcp__perplexity-ask__perplexity_ask"],
        "validate_response": lambda r: len(r) > 100  # Should have substantial response
    },
    {
        "name": "Test 3: Use Context7 for Documentation",
        "description": "Test if Claude can use Context7 for library documentation",
        "request": {
            "prompt": "Use Context7 to find documentation about React hooks, specifically useState and useEffect.",
            "model": "sonnet",
            "max_tokens": 2000
        },
        "expected_tools": ["mcp__context7__resolve-library-id", "mcp__context7__get-library-docs"],
        "validate_response": lambda r: "usestate" in r.lower() or "useeffect" in r.lower()
    },
    {
        "name": "Test 4: Multiple MCP Tools",
        "description": "Test using multiple MCP tools in one request",
        "request": {
            "prompt": "First, use Perplexity to find the latest Python 3.12 features, then use Context7 to get detailed documentation about any new syntax features.",
            "model": "sonnet",
            "max_tokens": 3000
        },
        "expected_tools": ["mcp__perplexity-ask__perplexity_ask", "mcp__context7"],
        "validate_response": lambda r: "python" in r.lower()
    },
    {
        "name": "Test 5: Conversation Context with Tools",
        "description": "Test if tool usage is tracked across conversation context",
        "conversation": True,
        "messages": [
            {
                "prompt": "My name is Alice and I'm interested in web development.",
                "expected_tools": []
            },
            {
                "prompt": "Based on what you know about me, use Perplexity to find the best web development resources for 2025.",
                "expected_tools": ["mcp__perplexity-ask__perplexity_ask"]
            }
        ]
    }
]


async def make_request(session: aiohttp.ClientSession, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Make an async HTTP request to the API."""
    url = f"{API_BASE}/{endpoint}"
    async with session.post(url, json=data) as response:
        return await response.json()


async def test_single_query(session: aiohttp.ClientSession, test_case: Dict[str, Any]) -> Dict[str, Any]:
    """Test a single query and validate the response."""
    print(f"\n{'='*60}")
    print(f"🧪 {test_case['name']}")
    print(f"📝 {test_case['description']}")
    print(f"{'='*60}")
    
    # Make the request
    print(f"\n📤 Sending request...")
    print(f"   Prompt: {test_case['request']['prompt'][:100]}...")
    
    start_time = datetime.now()
    response = await make_request(session, "claude/query", test_case['request'])
    duration = (datetime.now() - start_time).total_seconds()
    
    # Extract response details
    tools_used = response.get('metadata', {}).get('tools_used', [])
    tool_details = response.get('metadata', {}).get('tool_details', [])
    response_text = response.get('response', '')
    
    # Print results
    print(f"\n📥 Response received in {duration:.2f} seconds")
    print(f"   Response length: {len(response_text)} characters")
    print(f"   Tools used: {tools_used}")
    
    if tool_details:
        print(f"\n🔧 Tool Details:")
        for detail in tool_details:
            print(f"   - {detail['tool']} at {detail['timestamp']}")
            if 'input' in detail and detail['input']:
                input_str = json.dumps(detail['input'], indent=6)[:200]
                print(f"     Input: {input_str}...")
    
    # Validate response
    validation_results = []
    
    # Check if expected tools were used
    if 'expected_tools' in test_case:
        expected = set(test_case['expected_tools'])
        actual = set(tools_used)
        
        if expected:
            # We expect specific tools to be used
            missing_tools = expected - actual
            if missing_tools:
                validation_results.append(f"❌ Missing expected tools: {missing_tools}")
            else:
                validation_results.append(f"✅ All expected tools were used")
        else:
            # We expect no tools to be used
            if actual:
                validation_results.append(f"⚠️  Tools were used but none expected: {actual}")
            else:
                validation_results.append(f"✅ No tools used as expected")
    
    # Custom validation
    if 'validate_response' in test_case:
        if test_case['validate_response'](response_text):
            validation_results.append(f"✅ Response validation passed")
        else:
            validation_results.append(f"❌ Response validation failed")
            print(f"\n📄 Response excerpt: {response_text[:500]}...")
    
    # Print validation results
    print(f"\n📊 Validation Results:")
    for result in validation_results:
        print(f"   {result}")
    
    return {
        "test_name": test_case['name'],
        "success": all("✅" in r for r in validation_results),
        "tools_used": tools_used,
        "duration": duration,
        "validation_results": validation_results
    }


async def test_conversation(session: aiohttp.ClientSession, test_case: Dict[str, Any]) -> Dict[str, Any]:
    """Test a conversation with multiple messages."""
    print(f"\n{'='*60}")
    print(f"🧪 {test_case['name']}")
    print(f"📝 {test_case['description']}")
    print(f"{'='*60}")
    
    conversation_id = f"test-conversation-{datetime.now().timestamp()}"
    results = []
    
    for i, message in enumerate(test_case['messages'], 1):
        print(f"\n📨 Message {i}/{len(test_case['messages'])}")
        print(f"   Prompt: {message['prompt'][:100]}...")
        
        request_data = {
            "prompt": message['prompt'],
            "model": "sonnet",
            "max_tokens": 1000,
            "conversation_id": conversation_id
        }
        
        response = await make_request(session, "claude/query", request_data)
        tools_used = response.get('metadata', {}).get('tools_used', [])
        
        print(f"   Tools used: {tools_used}")
        
        # Validate tools
        expected = set(message.get('expected_tools', []))
        actual = set(tools_used)
        
        if expected:
            missing = expected - actual
            if missing:
                print(f"   ❌ Missing expected tools: {missing}")
                results.append(False)
            else:
                print(f"   ✅ Expected tools were used")
                results.append(True)
        else:
            if actual:
                print(f"   ⚠️  Tools used but none expected: {actual}")
            else:
                print(f"   ✅ No tools used as expected")
            results.append(True)
    
    return {
        "test_name": test_case['name'],
        "success": all(results),
        "conversation_id": conversation_id
    }


async def run_all_tests():
    """Run all test cases."""
    print(f"\n{'🚀'*30}")
    print(f"    CLAUDE SDK SERVER TOOL TRACKING TEST SUITE")
    print(f"{'🚀'*30}")
    print(f"\nServer: {SERVER_URL}")
    print(f"Time: {datetime.now().isoformat()}")
    
    # Check server health first
    print(f"\n🏥 Checking server health...")
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{SERVER_URL}/health") as response:
                if response.status == 200:
                    health_data = await response.json()
                    print(f"   ✅ Server is healthy: {health_data}")
                else:
                    print(f"   ❌ Server returned status {response.status}")
                    return
        except Exception as e:
            print(f"   ❌ Failed to connect to server: {e}")
            print(f"   Make sure the server is running on {SERVER_URL}")
            return
        
        # Run all tests
        results = []
        
        for test_case in TEST_CASES:
            try:
                if test_case.get('conversation'):
                    result = await test_conversation(session, test_case)
                else:
                    result = await test_single_query(session, test_case)
                results.append(result)
            except Exception as e:
                print(f"\n❌ Test failed with error: {e}")
                results.append({
                    "test_name": test_case.get('name', 'Unknown'),
                    "success": False,
                    "error": str(e)
                })
        
        # Print summary
        print(f"\n{'='*60}")
        print(f"📊 TEST SUMMARY")
        print(f"{'='*60}")
        
        total_tests = len(results)
        passed_tests = sum(1 for r in results if r.get('success'))
        
        print(f"\nTotal Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        print(f"\n📋 Individual Results:")
        for result in results:
            status = "✅ PASS" if result.get('success') else "❌ FAIL"
            print(f"   {status} - {result['test_name']}")
            if 'error' in result:
                print(f"        Error: {result['error']}")
        
        # Overall result
        print(f"\n{'='*60}")
        if passed_tests == total_tests:
            print(f"🎉 ALL TESTS PASSED! The tool tracking system is working correctly.")
        else:
            print(f"⚠️  Some tests failed. Please review the results above.")
        print(f"{'='*60}\n")


if __name__ == "__main__":
    # Run the async test suite
    asyncio.run(run_all_tests())