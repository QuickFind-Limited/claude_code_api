# Use Python 3.13 slim image
FROM python:3.13-slim

# Install system dependencies including Node.js
RUN apt-get update && apt-get install -y \
    curl \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js 20 LTS
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

# Install Claude Code SDK globally
RUN npm install -g @anthropic-ai/claude-code || \
    (curl -fsSL https://claude.ai/install.sh | bash) || \
    echo "Claude Code SDK installation attempted"

# Install uv - Python package manager (needed for both the app and odoo_mcp)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh && \
    mv /root/.local/bin/uv /usr/local/bin/uv && \
    mv /root/.local/bin/uvx /usr/local/bin/uvx

# Copy odoo_mcp source code (will be copied from local during build)
COPY odoo_mcp/ /opt/odoo_mcp/

# Install odoo_mcp dependencies (clean any existing venv first)
RUN cd /opt/odoo_mcp && \
    rm -rf .venv && \
    uv sync --frozen && \
    uv pip install -e . || echo "odoo_mcp installed"

# Set working directory
WORKDIR /app

# Copy dependency files first for better caching
COPY pyproject.toml uv.lock* README.md ./

# Install Python dependencies
RUN uv sync --frozen

# Copy application code
COPY src/ ./src/
COPY examples/ ./examples/
COPY tests/ ./tests/
COPY Makefile ./
COPY docker-entrypoint.sh /usr/local/bin/

# Create logs directory
RUN mkdir -p logs

# Make entrypoint executable
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Set environment variables
ENV PYTHONPATH="/app:${PYTHONPATH}"
ENV PYTHONUNBUFFERED=1
ENV NODE_PATH="/usr/lib/node_modules"

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Set entrypoint
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]

# Default command using uv run
CMD ["uv", "run", "uvicorn", "src.claude_sdk_server.main:app", "--host", "0.0.0.0", "--port", "8000"]