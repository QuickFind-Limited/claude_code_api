"""Test configuration and fixtures."""

import asyncio
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport

from src.claude_sdk_server.main import app
from src.claude_sdk_server.services.claude_service import ClaudeService


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_client() -> TestClient:
    """Create test client for FastAPI app."""
    return TestClient(app)


@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Create async HTTP client for integration tests."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
def mock_claude_service() -> MagicMock:
    """Mock Claude service for unit tests."""
    mock = MagicMock(spec=ClaudeService)
    mock.query = AsyncMock(return_value={
        "response": "Test response from Claude",
        "conversation_id": "test-123",
        "model": "claude-3-opus-20240229"
    })
    return mock


@pytest.fixture
def mock_claude_sdk() -> MagicMock:
    """Mock Claude SDK for service tests."""
    mock = MagicMock()
    mock.get_client = MagicMock()
    mock.get_client.return_value.query = AsyncMock(
        return_value="Test SDK response"
    )
    return mock


@pytest.fixture
def sample_query_request() -> dict:
    """Sample query request payload."""
    return {
        "prompt": "Test prompt",
        "model": "claude-3-opus-20240229",
        "temperature": 0.7,
        "max_tokens": 1000,
        "stream": False
    }


@pytest.fixture
def sample_error_response() -> dict:
    """Sample error response."""
    return {
        "error": {
            "message": "Test error",
            "type": "test_error",
            "code": "TEST_ERROR"
        }
    }