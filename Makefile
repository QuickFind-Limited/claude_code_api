# Makefile for Claude SDK Server
# Docker-based API server for Claude Code SDK

# Variables
PORT := 8000

# Colors for output
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

.PHONY: help up down logs test clean

# Default target
help:
	@echo "$(GREEN)Claude SDK Server - Docker Commands$(NC)"
	@echo ""
	@echo "$(YELLOW)Commands:$(NC)"
	@echo "  make up     - Build and start the server"
	@echo "  make down   - Stop the server"
	@echo "  make logs   - View server logs"
	@echo "  make test   - Test API endpoints"
	@echo "  make clean  - Clean up everything"

# Build and start server
up:
	@echo "$(GREEN)Building and starting Claude SDK Server...$(NC)"
	@docker-compose up --build -d
	@echo "$(GREEN)Server started at http://localhost:$(PORT)$(NC)"
	@echo "$(YELLOW)Use 'make logs' to view logs or 'make down' to stop$(NC)"

# Stop server
down:
	@echo "$(YELLOW)Stopping server...$(NC)"
	@docker-compose down
	@echo "$(GREEN)Server stopped$(NC)"

# View logs
logs:
	@echo "$(GREEN)Server logs (Ctrl+C to exit):$(NC)"
	@docker-compose logs -f

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

# Clean everything
clean:
	@echo "$(YELLOW)Cleaning up...$(NC)"
	@docker-compose down -v
	@docker rmi claude-sdk-server:latest 2>/dev/null || true
	@rm -rf __pycache__ .pytest_cache logs/*.log
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "$(GREEN)Cleanup complete!$(NC)"