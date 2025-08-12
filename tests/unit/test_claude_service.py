"""Unit tests for Claude service (TDD Red phase)."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.claude_sdk_server.services.claude_service import ClaudeService
from src.claude_sdk_server.models.dto import QueryRequest, QueryResponse
from src.claude_sdk_server.models.errors import (
    AuthenticationError,
    RateLimitError,
    SDKError
)


class TestClaudeService:
    """Test Claude service functionality."""

    @pytest.mark.asyncio
    async def test_query_success(self, mock_claude_sdk):
        """Test successful query to Claude SDK."""
        # Arrange
        service = ClaudeService()
        service._client = mock_claude_sdk
        request = QueryRequest(
            prompt="Test prompt",
            model="claude-3-opus-20240229"
        )
        
        # Act
        response = await service.query(request)
        
        # Assert
        assert isinstance(response, QueryResponse)
        assert response.response == "Test SDK response"
        assert response.model == request.model
        mock_claude_sdk.query.assert_called_once()

    @pytest.mark.asyncio
    async def test_query_with_temperature(self, mock_claude_sdk):
        """Test query with custom temperature."""
        # Arrange
        service = ClaudeService()
        service._client = mock_claude_sdk
        request = QueryRequest(
            prompt="Test prompt",
            temperature=0.5
        )
        
        # Act
        response = await service.query(request)
        
        # Assert
        assert response.response == "Test SDK response"

    @pytest.mark.asyncio
    async def test_query_authentication_error(self):
        """Test authentication error handling."""
        # Arrange
        service = ClaudeService()
        service._client = MagicMock()
        service._client.query = AsyncMock(
            side_effect=Exception("Authentication failed")
        )
        request = QueryRequest(prompt="Test")
        
        # Act & Assert
        with pytest.raises(AuthenticationError):
            await service.query(request)

    @pytest.mark.asyncio
    async def test_query_rate_limit_error(self):
        """Test rate limit error handling."""
        # Arrange
        service = ClaudeService()
        service._client = MagicMock()
        service._client.query = AsyncMock(
            side_effect=Exception("Rate limit exceeded")
        )
        request = QueryRequest(prompt="Test")
        
        # Act & Assert
        with pytest.raises(RateLimitError):
            await service.query(request)

    @pytest.mark.asyncio
    async def test_streaming_response(self, mock_claude_sdk):
        """Test streaming response handling."""
        # Arrange
        service = ClaudeService()
        service._client = mock_claude_sdk
        mock_claude_sdk.query.return_value = ["chunk1", "chunk2", "chunk3"]
        request = QueryRequest(
            prompt="Test prompt",
            stream=True
        )
        
        # Act
        response_stream = service.stream_query(request)
        chunks = []
        async for chunk in response_stream:
            chunks.append(chunk)
        
        # Assert
        assert len(chunks) == 3
        assert chunks == ["chunk1", "chunk2", "chunk3"]

    @pytest.mark.asyncio
    async def test_session_management(self, mock_claude_sdk):
        """Test conversation session management."""
        # Arrange
        service = ClaudeService()
        service._client = mock_claude_sdk
        conversation_id = "test-conversation-123"
        
        # Act
        session = await service.create_session(conversation_id)
        active = await service.is_session_active(conversation_id)
        await service.close_session(conversation_id)
        
        # Assert
        assert session["id"] == conversation_id
        assert active is True

    @pytest.mark.asyncio
    async def test_max_tokens_validation(self):
        """Test max tokens validation."""
        # Arrange
        service = ClaudeService()
        
        # Act & Assert
        with pytest.raises(ValueError):
            request = QueryRequest(
                prompt="Test",
                max_tokens=100000  # Too high
            )
            await service.query(request)

    @pytest.mark.asyncio
    async def test_error_logging(self, mock_claude_sdk, caplog):
        """Test error logging functionality."""
        # Arrange
        service = ClaudeService()
        service._client = mock_claude_sdk
        mock_claude_sdk.query.side_effect = Exception("Test error")
        request = QueryRequest(prompt="Test")
        
        # Act
        with pytest.raises(SDKError):
            await service.query(request)
        
        # Assert
        assert "Error in Claude SDK" in caplog.text