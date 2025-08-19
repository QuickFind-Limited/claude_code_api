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

# Create non-root user and group
RUN groupadd -g 1001 app && \
    useradd -m -u 1001 -g app -s /bin/bash app

# Set working directory
WORKDIR /app

# Copy dependency files first for better caching
COPY pyproject.toml uv.lock* README.md ./

# Install Python dependencies
RUN uv sync --frozen

# Copy application code
COPY src/ ./src/
COPY tests/ ./tests/
COPY Makefile ./
COPY docker-entrypoint.sh /usr/local/bin/
COPY claude-config.json /app/

# Create logs directory
RUN mkdir -p logs

# Make entrypoint executable
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Ensure non-root user owns application files and writable dirs
RUN chown -R app:app /app && \
    mkdir -p /home/app/.config && \
    chown -R app:app /home/app/.config

# Set environment variables
ENV PYTHONPATH="/app:${PYTHONPATH}"
ENV PYTHONUNBUFFERED=1
ENV NODE_PATH="/usr/lib/node_modules"
ENV HOME="/home/app"

# Expose port
EXPOSE 8000

# Switch to non-root user for runtime
USER app

# Set entrypoint
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]

# Default command using uv run
CMD ["uv", "run", "uvicorn", "src.claude_sdk_server.main:app", "--host", "0.0.0.0", "--port", "8000"]
