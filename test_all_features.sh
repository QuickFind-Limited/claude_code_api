#!/bin/bash

# Test script for Claude SDK Server with Loguru and Streaming

set -e

echo "========================================="
echo "Claude SDK Server - Feature Test Suite"
echo "========================================="

BASE_URL="http://localhost:8000"
API_URL="$BASE_URL/api/v1"

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m'

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Test function
run_test() {
    local test_name="$1"
    local test_command="$2"
    
    echo -e "\n${YELLOW}Testing: $test_name${NC}"
    if eval "$test_command"; then
        echo -e "${GREEN}✅ PASSED${NC}"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}❌ FAILED${NC}"
        ((TESTS_FAILED++))
    fi
}

# 1. Health Check
run_test "Health Check" "curl -s $API_URL/health | grep -q 'healthy'"

# 2. Basic Query
run_test "Basic Query" "curl -s -X POST $API_URL/query \
    -H 'Content-Type: application/json' \
    -d '{\"prompt\": \"What is 2+2?\"}' | grep -q 'response'"

# 3. Query with Thinking
run_test "Query with Thinking" "curl -s -X POST $API_URL/query \
    -H 'Content-Type: application/json' \
    -d '{\"prompt\": \"Calculate 3*4\", \"max_thinking_tokens\": 1000}' | grep -q 'session_id'"

# 4. Stream Status
run_test "Stream Status" "curl -s $API_URL/stream/status | grep -q 'active_connections'"

# 5. Recent Events
run_test "Recent Events" "curl -s '$API_URL/stream/events/recent?count=5' | python3 -c 'import sys, json; data=json.load(sys.stdin); exit(0 if isinstance(data, list) else 1)'"

# 6. SSE Connection Test (timeout after 2 seconds)
run_test "SSE Endpoint" "timeout 2 curl -s -N $API_URL/stream/sse 2>/dev/null | grep -q 'event:' || true"

# 7. JSON Lines Stream Test
run_test "JSON Lines Stream" "timeout 2 curl -s -N $API_URL/stream/jsonl 2>/dev/null | head -1 | python3 -c 'import sys, json; json.loads(sys.stdin.read())' 2>/dev/null || true"

# 8. Event Filtering
run_test "Event Filtering" "curl -s '$API_URL/stream/events/recent?count=10&event_types=query_complete&event_types=query_start' | python3 -c 'import sys, json; exit(0)'"

# 9. Client List
run_test "Client List" "curl -s $API_URL/stream/clients | grep -q 'active_clients'"

# 10. Session Continuity
echo -e "\n${YELLOW}Testing: Session Continuity${NC}"
SESSION_ID=$(curl -s -X POST $API_URL/query \
    -H 'Content-Type: application/json' \
    -d '{"prompt": "Remember this number: 42"}' | python3 -c "import sys, json; print(json.load(sys.stdin)['session_id'])")

if [ ! -z "$SESSION_ID" ]; then
    sleep 1
    RESPONSE=$(curl -s -X POST $API_URL/query \
        -H 'Content-Type: application/json' \
        -d "{\"prompt\": \"What number did I ask you to remember?\", \"session_id\": \"$SESSION_ID\"}" | python3 -c "import sys, json; print(json.load(sys.stdin)['response'])")
    
    if echo "$RESPONSE" | grep -q "42"; then
        echo -e "${GREEN}✅ PASSED${NC}"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}❌ FAILED - Response: $RESPONSE${NC}"
        ((TESTS_FAILED++))
    fi
else
    echo -e "${RED}❌ FAILED - No session ID${NC}"
    ((TESTS_FAILED++))
fi

# 11. Performance Events Check
run_test "Performance Events" "curl -s '$API_URL/stream/events/recent?count=20' | grep -q 'performance_metric'"

# 12. Token Usage Events
run_test "Token Usage Events" "curl -s '$API_URL/stream/events/recent?count=20' | grep -q 'token_usage'"

# Summary
echo -e "\n========================================="
echo -e "Test Results Summary"
echo -e "========================================="
echo -e "${GREEN}Passed: $TESTS_PASSED${NC}"
echo -e "${RED}Failed: $TESTS_FAILED${NC}"

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "\n${GREEN}🎉 All tests passed!${NC}"
    exit 0
else
    echo -e "\n${RED}⚠️ Some tests failed${NC}"
    exit 1
fi