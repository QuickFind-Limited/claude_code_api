# Makefile for Claude SDK Server
# Minimal API server for Claude Code SDK

# Variables
PYTHON := uv run python
UVICORN := uv run uvicorn
HOST := 0.0.0.0
PORT := 8000
APP := src.claude_sdk_server.main:app

# Colors for output
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

.PHONY: help install clean run dev test docker-build docker-up docker-down docker-logs

# Default target
help:
	@echo "$(GREEN)Claude SDK Server - Available Commands$(NC)"
	@echo ""
	@echo "$(YELLOW)Setup:$(NC)"
	@echo "  make install    - Install dependencies using uv"
	@echo "  make clean      - Clean up generated files and cache"
	@echo ""
	@echo "$(YELLOW)Development:$(NC)"
	@echo "  make run        - Run server in foreground"
	@echo "  make dev        - Run server with auto-reload"
	@echo "  make test       - Test API endpoints"
	@echo ""
	@echo "$(YELLOW)Docker:$(NC)"
	@echo "  make docker-build - Build Docker image"
	@echo "  make docker-up    - Start services with Docker Compose"
	@echo "  make docker-down  - Stop Docker Compose services"
	@echo "  make docker-logs  - View Docker container logs"

# Install dependencies
install:
	@echo "$(GREEN)Installing dependencies...$(NC)"
	@uv sync
	@mkdir -p logs
	@echo "$(GREEN)Dependencies installed successfully!$(NC)"

# Clean up generated files
clean:
	@echo "$(YELLOW)Cleaning up...$(NC)"
	@rm -rf __pycache__ .pytest_cache
	@rm -rf src/**/__pycache__
	@rm -rf src/**/**/__pycache__
	@rm -f logs/*.log
	@find . -type f -name "*.pyc" -delete
	@find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	@echo "$(GREEN)Cleanup complete!$(NC)"

# Run server in foreground
run:
	@echo "$(GREEN)Starting server on http://$(HOST):$(PORT)$(NC)"
	@echo "$(YELLOW)Press Ctrl+C to stop$(NC)"
	@$(UVICORN) $(APP) --host $(HOST) --port $(PORT)

# Run server in development mode with auto-reload
dev:
	@echo "$(GREEN)Starting development server on http://$(HOST):$(PORT)$(NC)"
	@echo "$(YELLOW)Auto-reload enabled. Press Ctrl+C to stop$(NC)"
	@$(UVICORN) $(APP) --host $(HOST) --port $(PORT) --reload

# Test API endpoints
test:
	@echo "$(GREEN)Testing health endpoint...$(NC)"
	@curl -s http://localhost:$(PORT)/api/v1/health | python3 -m json.tool || echo "$(RED)Server is not responding$(NC)"
	@echo ""
	@echo "$(GREEN)Testing query endpoint...$(NC)"
	@response=$$(curl -s -X POST http://localhost:$(PORT)/api/v1/query \
		-H "Content-Type: application/json" \
		-d '{"prompt": "Hello from Makefile test!"}'); \
	if echo "$$response" | python3 -c "import sys, json; data=json.load(sys.stdin); print('Response:', data.get('response', 'No response')[:100]+'...'); print('Session ID:', data.get('session_id', 'No session'))" 2>/dev/null; then \
		echo "$(GREEN)✓ API test successful$(NC)"; \
	else \
		echo "$(RED)✗ API test failed$(NC)"; \
		echo "$$response"; \
	fi

# Build Docker image
docker-build:
	@echo "$(GREEN)Building Docker image...$(NC)"
	@docker build -t claude-sdk-server:latest .
	@echo "$(GREEN)Docker image built successfully!$(NC)"

# Start services with Docker Compose
docker-up:
	@echo "$(GREEN)Starting services with Docker Compose...$(NC)"
	@docker-compose up -d
	@echo "$(GREEN)Services started at http://$(HOST):$(PORT)$(NC)"

# Stop Docker Compose services
docker-down:
	@echo "$(YELLOW)Stopping services...$(NC)"
	@docker-compose down
	@echo "$(GREEN)Services stopped$(NC)"

# View Docker logs
docker-logs:
	@echo "$(GREEN)Docker container logs:$(NC)"
	@docker-compose logs -f