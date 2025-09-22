# Makefile for Claude SDK Server
# Docker-based API server for Claude Code SDK

# Variables
# Override with: make DOCKER_COMPOSE="docker-compose" up
DOCKER_COMPOSE := docker compose
PORT := 8000

# Colors for output
GREEN := \033[0;32m
YELLOW := \033[0;33m
NC := \033[0m # No Color

.PHONY: help up down logs clean restart logs-pretty frontend-3002

# Default target
help:
	@echo "$(GREEN)Claude SDK Server - Docker Commands$(NC)"
	@echo ""
	@echo "$(YELLOW)Core Commands:$(NC)"
	@echo "  make up          - Build and start the server"
	@echo "  make down        - Stop the server"
	@echo "  make restart     - Restart the server"
	@echo "  make logs        - Tail server logs"
	@echo "  make clean       - Remove containers, image, and caches"
	@echo ""
	@echo "$(YELLOW)Developer Utilities:$(NC)"
	@echo "  make logs-pretty - Tail logs with emoji-based filtering"
	@echo "  make frontend-3002 - Start the React frontend (chatbot-frontend)"

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
# DEVELOPMENT COMMANDS

# Watch logs with emoji-based filtering
logs-pretty:
	@echo "$(GREEN)Beautiful logs (Ctrl+C to exit):$(NC)"
	@$(DOCKER_COMPOSE) logs -f | grep -E "🚀|🛠️|🤔|📝|✅|💡|⚡|📊|⏱️" --color=always

# Start React frontend on port 3002
frontend-3002:
	@echo "$(GREEN)Starting React frontend on port 3002...$(NC)"
	@cd chatbot-frontend && npm start -- --port 3002
	@echo "$(GREEN)✅ React frontend available at http://localhost:3002$(NC)"
