# Makefile for Claude SDK Server
# Docker-based API server for Claude Code SDK

# Variables
# Override with: make DOCKER_COMPOSE="docker-compose" up
DOCKER_COMPOSE := docker compose
PORT := 8000

# Colors for output
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

.PHONY: help up down logs test clean restart test-stream test-sse test-ws test-events stream-status stream-clients query

# Default target
help:
	@echo "$(GREEN)Claude SDK Server - Docker Commands$(NC)"
	@echo ""
	@echo "$(YELLOW)Basic Commands:$(NC)"
	@echo "  make up          - Build and start the server"
	@echo "  make down        - Stop the server"
	@echo "  make restart     - Restart the server"
	@echo "  make logs        - View server logs"
	@echo "  make clean       - Clean up everything"
	@echo ""
	@echo "$(YELLOW)Testing Commands:$(NC)"
	@echo "  make test        - Test basic API endpoints"
	@echo "  make test-stream - Test all streaming endpoints"
	@echo "  make test-sse    - Test Server-Sent Events streaming"
	@echo "  make test-ws     - Test WebSocket streaming"
	@echo "  make test-events - Test event system"
	@echo ""
	@echo "$(YELLOW)API Commands:$(NC)"
	@echo "  make query       - Send a test query to Claude"
	@echo "  make stream-status - Check streaming system status"
	@echo "  make stream-clients - List active streaming clients"
	@echo ""
	@echo "$(YELLOW)Frontend Commands:$(NC)"
	@echo "  make frontend    - Start the frontend dashboard"
	@echo "  make frontend-3002 - Start React frontend on port 3002"
	@echo "  make open-frontend - Open dashboard in browser"
	@echo "  make start-all   - Start backend and frontend together"

# Build and start server
up:
	@echo "$(GREEN)Building and starting Claude SDK Server...$(NC)"
	@$(DOCKER_COMPOSE) up --build -d
	@echo "$(GREEN)Server started at http://localhost:$(PORT)$(NC)"
	@echo "$(YELLOW)Use 'make logs' to view logs or 'make down' to stop$(NC)"

# Stop server
down:
	@echo "$(YELLOW)Stopping server...$(NC)"
	@$(DOCKER_COMPOSE) down
	@echo "$(GREEN)Server stopped$(NC)"

# View logs
logs:
	@echo "$(GREEN)Server logs (Ctrl+C to exit):$(NC)"
	@$(DOCKER_COMPOSE) logs -f

# Test API endpoints
test:
	@echo "$(GREEN)Testing health endpoint...$(NC)"
	@curl -s http://localhost:$(PORT)/api/v1/health | python3 -m json.tool || echo "$(RED)Server is not responding$(NC)"
	@echo ""
	@echo "$(GREEN)Testing query endpoint...$(NC)"
	@response=$$(curl -s -X POST http://localhost:$(PORT)/api/v1/query \
		-H "Content-Type: application/json" \
		-d '{"prompt": "Hello, this is a test!"}'); \
	if echo "$$response" | python3 -c "import sys, json; data=json.load(sys.stdin); print('✓ Response received'); print('Session ID:', data.get('session_id', 'No session')[:8]+'...')" 2>/dev/null; then \
		echo "$(GREEN)✓ API test successful$(NC)"; \
	else \
		echo "$(RED)✗ API test failed$(NC)"; \
	fi

# Restart server
restart: down up
	@echo "$(GREEN)Server restarted successfully$(NC)"

# Clean everything
clean:
	@echo "$(YELLOW)Cleaning up...$(NC)"
	@$(DOCKER_COMPOSE) down -v
	@docker rmi claude-sdk-server:latest 2>/dev/null || true
	@rm -rf __pycache__ .pytest_cache logs/*.log
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "$(GREEN)Cleanup complete!$(NC)"

# ============================================================================
# STREAMING ENDPOINTS TESTING
# ============================================================================

# Test all streaming endpoints
test-stream: test-events test-sse
	@echo "$(GREEN)✓ All streaming tests completed$(NC)"

# Test Server-Sent Events streaming
test-sse:
	@echo "$(YELLOW)Testing SSE streaming...$(NC)"
	@echo "Starting SSE connection..."
	@timeout 5 curl -N "http://localhost:$(PORT)/api/v1/stream/sse" 2>/dev/null | head -5 || true
	@echo ""
	@echo "$(GREEN)✓ SSE endpoint is responding$(NC)"

# Test WebSocket streaming (requires wscat or similar)
test-ws:
	@echo "$(YELLOW)Testing WebSocket streaming...$(NC)"
	@echo "Note: Install wscat with 'npm install -g wscat' for interactive testing"
	@echo "WebSocket endpoint: ws://localhost:$(PORT)/api/v1/stream/ws"
	@echo ""
	@echo "Example wscat command:"
	@echo "  wscat -c ws://localhost:$(PORT)/api/v1/stream/ws"
	@echo ""
	@echo "$(GREEN)WebSocket endpoint available at ws://localhost:$(PORT)/api/v1/stream/ws$(NC)"

# Test event system
test-events:
	@echo "$(YELLOW)Testing event system...$(NC)"
	@echo "Checking streaming status..."
	@curl -s http://localhost:$(PORT)/api/v1/stream/status | python3 -m json.tool
	@echo ""
	@echo "Fetching recent events..."
	@curl -s "http://localhost:$(PORT)/api/v1/stream/events/recent?count=3" | python3 -m json.tool | head -50
	@echo ""
	@echo "$(GREEN)✓ Event system is working$(NC)"

# ============================================================================
# API INTERACTION COMMANDS
# ============================================================================

# Send a test query to Claude
query:
	@echo "$(YELLOW)Sending query to Claude...$(NC)"
	@response=$$(curl -s -X POST http://localhost:$(PORT)/api/v1/query \
		-H "Content-Type: application/json" \
		-d '{"prompt": "What is 2+2? Just give me the number.", "max_thinking_tokens": 1000}'); \
	echo "$$response" | python3 -c "import sys, json; data=json.load(sys.stdin); print('Response:', data.get('response', 'No response')); print('Session ID:', data.get('session_id', 'No session')[:8]+'...')" 2>/dev/null || echo "$(RED)Query failed$(NC)"

# Check streaming system status
stream-status:
	@echo "$(YELLOW)Streaming System Status:$(NC)"
	@curl -s http://localhost:$(PORT)/api/v1/stream/status | python3 -m json.tool

# List active streaming clients
stream-clients:
	@echo "$(YELLOW)Active Streaming Clients:$(NC)"
	@curl -s http://localhost:$(PORT)/api/v1/stream/clients | python3 -m json.tool

# ============================================================================
# FRONTEND COMMANDS
# ============================================================================

# Start the frontend dashboard
frontend:
	@echo "$(GREEN)Starting frontend dashboard...$(NC)"
	@cd frontend && python3 serve.py

# Open frontend in browser
open-frontend:
	@echo "$(GREEN)Opening frontend dashboard...$(NC)"
	@open http://localhost:3000 || xdg-open http://localhost:3000 || echo "Please open http://localhost:3000 in your browser"

# Start the chatbot interface
chatbot:
	@echo "$(GREEN)💬 Starting chatbot interface...$(NC)"
	@cd frontend && python3 -m http.server 3001 --bind 0.0.0.0 > /dev/null 2>&1 &
	@sleep 1
	@echo "$(GREEN)✅ Chatbot available at http://localhost:3001/chatbot.html$(NC)"
	@open http://localhost:3001/chatbot.html || xdg-open http://localhost:3001/chatbot.html || echo "Please open http://localhost:3001/chatbot.html in your browser"

# Start React frontend on port 3002
frontend-3002:
	@echo "$(GREEN)Starting React frontend on port 3002...$(NC)"
	@cd chatbot-frontend && npm start -- --port 3002
	@echo "$(GREEN)✅ React frontend available at http://localhost:3002$(NC)"

# Start both backend and frontend
start-all: up
	@echo "$(GREEN)Starting frontend dashboard...$(NC)"
	@cd frontend && python3 serve.py &
	@sleep 2
	@open http://localhost:3000 || xdg-open http://localhost:3000 || echo "Please open http://localhost:3000 in your browser"

# ============================================================================
# DEVELOPMENT COMMANDS

# Run server locally without Docker
run-local:
	@echo "$(GREEN)Starting Claude SDK Server locally on port $(PORT)...$(NC)"
	@uv run --env-file .env uvicorn src.claude_sdk_server.main:app --reload --host 0.0.0.0 --port $(PORT)
# ============================================================================

# Watch logs with beautiful formatting
logs-pretty:
	@echo "$(GREEN)Beautiful logs (Ctrl+C to exit):$(NC)"
	@$(DOCKER_COMPOSE) logs -f | grep -E "🚀|🛠️|🤔|📝|✅|💡|⚡|📊|⏱️" --color=always

# Test streaming with a live query
demo-stream:
	@echo "$(YELLOW)Starting streaming demo...$(NC)"
	@echo "1. Opening SSE connection in background..."
	@curl -N "http://localhost:$(PORT)/api/v1/stream/sse?include_performance=true" 2>/dev/null | head -20 & \
	SSE_PID=$$!; \
	sleep 2; \
	echo "2. Sending query to generate events..."; \
	curl -s -X POST http://localhost:$(PORT)/api/v1/query \
		-H "Content-Type: application/json" \
		-d '{"prompt": "Create a simple TODO list for learning Python", "max_thinking_tokens": 5000}' > /dev/null; \
	sleep 5; \
	kill $$SSE_PID 2>/dev/null || true; \
	echo ""; \
	echo "$(GREEN)✓ Streaming demo completed$(NC)"

# Test with thinking mode
test-thinking:
	@echo "$(YELLOW)Testing with thinking mode enabled...$(NC)"
	@response=$$(curl -s -X POST http://localhost:$(PORT)/api/v1/query \
		-H "Content-Type: application/json" \
		-d '{"prompt": "Explain step by step how to calculate 15% of 80", "max_thinking_tokens": 8000}'); \
	echo "$$response" | python3 -m json.tool | head -50

# Monitor events in real-time
monitor-events:
	@echo "$(GREEN)Monitoring events (send queries in another terminal):$(NC)"
	@while true; do \
		clear; \
		echo "$(YELLOW)=== Event Stream Status ===$(NC)"; \
		curl -s http://localhost:$(PORT)/api/v1/stream/status | python3 -m json.tool; \
		echo ""; \
		echo "$(YELLOW)=== Recent Events (Last 5) ===$(NC)"; \
		curl -s "http://localhost:$(PORT)/api/v1/stream/events/recent?count=5" | python3 -m json.tool | head -80; \
		sleep 2; \
	done