# Makefile for Claude SDK Server
# Minimal API server for Claude Code SDK

# Variables
PYTHON := uv run python
UVICORN := uv run uvicorn
PIP := uv pip
HOST := 0.0.0.0
PORT := 8000
APP := src.claude_sdk_server.main:app
PID_FILE := logs/server.pid
LOG_FILE := logs/app.log

# Colors for output
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

.PHONY: help install clean run start stop restart status test health query logs dev setup all

# Default target
help:
	@echo "$(GREEN)Claude SDK Server - Makefile Commands$(NC)"
	@echo ""
	@echo "$(YELLOW)Setup:$(NC)"
	@echo "  make install    - Install dependencies using uv"
	@echo "  make setup      - Full setup (install + create directories)"
	@echo ""
	@echo "$(YELLOW)Server Management:$(NC)"
	@echo "  make run        - Run server in foreground"
	@echo "  make start      - Start server in background"
	@echo "  make stop       - Stop background server"
	@echo "  make restart    - Restart server"
	@echo "  make status     - Check server status"
	@echo ""
	@echo "$(YELLOW)Development:$(NC)"
	@echo "  make dev        - Run server in development mode with reload"
	@echo "  make logs       - Tail server logs"
	@echo "  make test       - Test API endpoints"
	@echo "  make health     - Check health endpoint"
	@echo "  make query      - Send test query"
	@echo ""
	@echo "$(YELLOW)Maintenance:$(NC)"
	@echo "  make clean      - Clean up generated files and cache"
	@echo "  make all        - Setup and start server"

# Install dependencies
install:
	@echo "$(GREEN)Installing dependencies...$(NC)"
	@uv sync
	@echo "$(GREEN)Dependencies installed successfully!$(NC)"

# Create necessary directories
setup: install
	@echo "$(GREEN)Setting up project...$(NC)"
	@mkdir -p logs
	@touch logs/.gitkeep
	@echo "$(GREEN)Setup complete!$(NC)"

# Clean up generated files
clean:
	@echo "$(YELLOW)Cleaning up...$(NC)"
	@rm -rf __pycache__ .pytest_cache
	@rm -rf src/**/__pycache__
	@rm -rf src/**/**/__pycache__
	@rm -rf src/**/**/**/__pycache__
	@rm -f logs/*.log
	@rm -f logs/*.pid
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

# Start server in background
start:
	@if [ -f $(PID_FILE) ] && kill -0 `cat $(PID_FILE)` 2>/dev/null; then \
		echo "$(YELLOW)Server is already running with PID $$(cat $(PID_FILE))$(NC)"; \
	else \
		echo "$(GREEN)Starting server in background...$(NC)"; \
		nohup $(UVICORN) $(APP) --host $(HOST) --port $(PORT) > $(LOG_FILE) 2>&1 & echo $$! > $(PID_FILE); \
		sleep 2; \
		if kill -0 `cat $(PID_FILE)` 2>/dev/null; then \
			echo "$(GREEN)Server started successfully with PID $$(cat $(PID_FILE))$(NC)"; \
			echo "$(GREEN)Server running at http://$(HOST):$(PORT)$(NC)"; \
			echo "Use 'make logs' to view logs or 'make stop' to stop the server"; \
		else \
			echo "$(RED)Failed to start server. Check logs at $(LOG_FILE)$(NC)"; \
			rm -f $(PID_FILE); \
			exit 1; \
		fi \
	fi

# Stop background server
stop:
	@if [ -f $(PID_FILE) ]; then \
		if kill -0 `cat $(PID_FILE)` 2>/dev/null; then \
			echo "$(YELLOW)Stopping server with PID $$(cat $(PID_FILE))...$(NC)"; \
			kill `cat $(PID_FILE)`; \
			rm -f $(PID_FILE); \
			echo "$(GREEN)Server stopped successfully$(NC)"; \
		else \
			echo "$(YELLOW)Server is not running (stale PID file)$(NC)"; \
			rm -f $(PID_FILE); \
		fi \
	else \
		echo "$(YELLOW)Server is not running$(NC)"; \
	fi

# Restart server
restart: stop
	@sleep 1
	@make start

# Check server status
status:
	@if [ -f $(PID_FILE) ] && kill -0 `cat $(PID_FILE)` 2>/dev/null; then \
		echo "$(GREEN)✓ Server is running$(NC)"; \
		echo "  PID: $$(cat $(PID_FILE))"; \
		echo "  URL: http://$(HOST):$(PORT)"; \
		echo "  Logs: $(LOG_FILE)"; \
	else \
		echo "$(RED)✗ Server is not running$(NC)"; \
		if [ -f $(PID_FILE) ]; then \
			rm -f $(PID_FILE); \
		fi \
	fi

# View logs
logs:
	@if [ -f $(LOG_FILE) ]; then \
		echo "$(GREEN)Tailing server logs (Ctrl+C to stop)...$(NC)"; \
		tail -f $(LOG_FILE); \
	else \
		echo "$(YELLOW)No log file found. Start the server first.$(NC)"; \
	fi

# Test health endpoint
health:
	@echo "$(GREEN)Testing health endpoint...$(NC)"
	@curl -s http://localhost:$(PORT)/api/v1/health | python3 -m json.tool || echo "$(RED)Server is not responding$(NC)"

# Send test query
query:
	@echo "$(GREEN)Sending test query...$(NC)"
	@curl -s -X POST http://localhost:$(PORT)/api/v1/query \
		-H "Content-Type: application/json" \
		-d '{"prompt": "Hello, this is a test message from Makefile!"}' \
		| python3 -m json.tool || echo "$(RED)Failed to send query. Is the server running?$(NC)"

# Test API endpoints
test: health
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

# Full setup and start
all: setup start

# Docker commands
.PHONY: docker-build docker-run docker-stop docker-logs docker-shell docker-clean docker-compose-up docker-compose-down

# Build Docker image
docker-build:
	@echo "$(GREEN)Building Docker image...$(NC)"
	@docker build -t claude-sdk-server:latest .
	@echo "$(GREEN)Docker image built successfully!$(NC)"

# Run Docker container
docker-run:
	@echo "$(GREEN)Starting Docker container...$(NC)"
	@docker run -d \
		--name claude-sdk-server \
		-p $(PORT):8000 \
		-e ANTHROPIC_API_KEY="$${ANTHROPIC_API_KEY}" \
		-v $(PWD)/logs:/app/logs \
		claude-sdk-server:latest
	@echo "$(GREEN)Container started at http://$(HOST):$(PORT)$(NC)"

# Stop Docker container
docker-stop:
	@echo "$(YELLOW)Stopping Docker container...$(NC)"
	@docker stop claude-sdk-server || true
	@docker rm claude-sdk-server || true
	@echo "$(GREEN)Container stopped$(NC)"

# View Docker logs
docker-logs:
	@echo "$(GREEN)Docker container logs:$(NC)"
	@docker logs -f claude-sdk-server

# Shell into Docker container
docker-shell:
	@echo "$(GREEN)Opening shell in Docker container...$(NC)"
	@docker exec -it claude-sdk-server /bin/bash

# Clean Docker images
docker-clean:
	@echo "$(YELLOW)Cleaning Docker resources...$(NC)"
	@docker stop claude-sdk-server 2>/dev/null || true
	@docker rm claude-sdk-server 2>/dev/null || true
	@docker rmi claude-sdk-server:latest 2>/dev/null || true
	@echo "$(GREEN)Docker resources cleaned$(NC)"

# Docker Compose commands
docker-compose-up:
	@echo "$(GREEN)Starting services with Docker Compose...$(NC)"
	@docker-compose up -d
	@echo "$(GREEN)Services started$(NC)"

docker-compose-down:
	@echo "$(YELLOW)Stopping services with Docker Compose...$(NC)"
	@docker-compose down
	@echo "$(GREEN)Services stopped$(NC)"

# Docker shortcuts
.PHONY: db dr ds dl dsh dc

db: docker-build     # Shortcut for docker-build
dr: docker-run       # Shortcut for docker-run
ds: docker-stop      # Shortcut for docker-stop
dl: docker-logs      # Shortcut for docker-logs
dsh: docker-shell    # Shortcut for docker-shell
dc: docker-clean     # Shortcut for docker-clean
	@echo ""
	@echo "$(GREEN)===========================================$(NC)"
	@echo "$(GREEN)Claude SDK Server is ready!$(NC)"
	@echo "$(GREEN)===========================================$(NC)"
	@echo ""
	@echo "API Endpoints:"
	@echo "  - Health: http://$(HOST):$(PORT)/api/v1/health"
	@echo "  - Query:  http://$(HOST):$(PORT)/api/v1/query"
	@echo "  - Docs:   http://$(HOST):$(PORT)/docs"
	@echo ""
	@echo "Commands:"
	@echo "  - View logs:    make logs"
	@echo "  - Check status: make status"
	@echo "  - Stop server:  make stop"
	@echo "  - Test API:     make test"
	@echo ""

# Development shortcuts
.PHONY: s st r d l h t

s: start      # Shortcut for start
st: stop      # Shortcut for stop
r: restart    # Shortcut for restart
d: dev        # Shortcut for dev
l: logs       # Shortcut for logs
h: health     # Shortcut for health
t: test       # Shortcut for test