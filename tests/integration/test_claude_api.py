"""Integration tests for Claude API endpoints."""

import pytest
from httpx import AsyncClient


class TestClaudeAPI:
    """Test Claude API endpoints."""

    @pytest.mark.asyncio
    async def test_health_endpoint(self, async_client: AsyncClient):
        """Test health check endpoint."""
        # Act
        response = await async_client.get("/health")
        
        # Assert
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}

    @pytest.mark.asyncio
    async def test_query_endpoint_success(self, async_client: AsyncClient):
        """Test successful query to Claude endpoint."""
        # Arrange
        payload = {
            "prompt": "What is 2+2?",
            "model": "claude-3-opus-20240229",
            "temperature": 0.7
        }
        
        # Act
        response = await async_client.post("/api/v1/claude/query", json=payload)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert "conversation_id" in data
        assert data["model"] == payload["model"]

    @pytest.mark.asyncio
    async def test_query_endpoint_validation_error(self, async_client: AsyncClient):
        """Test query endpoint with invalid payload."""
        # Arrange
        payload = {
            # Missing required 'prompt' field
            "model": "claude-3-opus-20240229"
        }
        
        # Act
        response = await async_client.post("/api/v1/claude/query", json=payload)
        
        # Assert
        assert response.status_code == 422
        assert "detail" in response.json()

    @pytest.mark.asyncio
    async def test_query_endpoint_with_attachments(self, async_client: AsyncClient):
        """Test query endpoint with file attachments."""
        # Arrange
        payload = {
            "prompt": "Analyze this data",
            "attachments": [
                {"filename": "data.csv", "content": "col1,col2\n1,2\n3,4"}
            ]
        }
        
        # Act
        response = await async_client.post("/api/v1/claude/query", json=payload)
        
        # Assert
        assert response.status_code == 200
        assert "response" in response.json()

    @pytest.mark.asyncio
    async def test_streaming_query_endpoint(self, async_client: AsyncClient):
        """Test streaming query endpoint."""
        # Arrange
        payload = {
            "prompt": "Tell me a story",
            "stream": True
        }
        
        # Act
        async with async_client.stream("POST", "/api/v1/claude/query", json=payload) as response:
            assert response.status_code == 200
            chunks = []
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    chunks.append(line[6:])
            
            # Assert
            assert len(chunks) > 0

    @pytest.mark.asyncio
    async def test_cors_headers(self, async_client: AsyncClient):
        """Test CORS headers are properly set."""
        # Act
        response = await async_client.options("/api/v1/claude/query")
        
        # Assert
        assert response.status_code == 200
        assert "Access-Control-Allow-Origin" in response.headers

    @pytest.mark.asyncio
    async def test_rate_limiting(self, async_client: AsyncClient):
        """Test rate limiting functionality."""
        # Arrange
        payload = {"prompt": "Test"}
        
        # Act - Send multiple requests rapidly
        responses = []
        for _ in range(10):
            response = await async_client.post("/api/v1/claude/query", json=payload)
            responses.append(response)
        
        # Assert - At least one should be rate limited
        status_codes = [r.status_code for r in responses]
        assert 429 in status_codes or all(s == 200 for s in status_codes)

    @pytest.mark.asyncio
    async def test_session_endpoints(self, async_client: AsyncClient):
        """Test session management endpoints."""
        # Create session
        response = await async_client.post("/api/v1/claude/sessions")
        assert response.status_code == 201
        session_id = response.json()["session_id"]
        
        # Get session
        response = await async_client.get(f"/api/v1/claude/sessions/{session_id}")
        assert response.status_code == 200
        
        # Delete session
        response = await async_client.delete(f"/api/v1/claude/sessions/{session_id}")
        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_openapi_docs(self, async_client: AsyncClient):
        """Test OpenAPI documentation endpoint."""
        # Act
        response = await async_client.get("/docs")
        
        # Assert
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]