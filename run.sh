#!/bin/bash

# Claude SDK Server Run Script

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting Claude SDK Server${NC}"

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  .env file not found. Creating from .env.example...${NC}"
    cp .env.example .env
    echo -e "${RED}❗ Please update .env with your Claude API key${NC}"
    exit 1
fi

# Install dependencies if needed
if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}📦 Creating virtual environment...${NC}"
    python -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
echo -e "${YELLOW}📦 Installing dependencies...${NC}"
pip install -e .

# Create logs directory
mkdir -p logs

# Run the server
echo -e "${GREEN}🚀 Starting server on http://localhost:8000${NC}"
echo -e "${GREEN}📚 API Documentation: http://localhost:8000/docs${NC}"
echo -e "${GREEN}❤️  Health Check: http://localhost:8000/health${NC}"

# Run with uvicorn
uvicorn src.claude_sdk_server.main:app --host 0.0.0.0 --port 8000 --reload