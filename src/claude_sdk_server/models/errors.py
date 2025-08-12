"""Error models for Claude SDK Server."""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    """Error detail information."""
    
    message: str = Field(..., description="Error message")
    type: str = Field(..., description="Error type")
    code: str = Field(..., description="Error code")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional details")


class ErrorResponse(BaseModel):
    """Standard error response."""
    
    error: ErrorDetail = Field(..., description="Error information")


class ClaudeSDKError(Exception):
    """Base exception for Claude SDK errors."""
    
    def __init__(
        self,
        message: str,
        error_type: str = "sdk_error",
        error_code: str = "SDK_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_type = error_type
        self.error_code = error_code
        self.details = details
        super().__init__(message)
    
    def to_response(self) -> ErrorResponse:
        """Convert exception to error response."""
        return ErrorResponse(
            error=ErrorDetail(
                message=self.message,
                type=self.error_type,
                code=self.error_code,
                details=self.details
            )
        )


class AuthenticationError(ClaudeSDKError):
    """Authentication error."""
    
    def __init__(self, message: str = "Authentication failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_type="authentication_error",
            error_code="AUTH_ERROR",
            details=details
        )


class RateLimitError(ClaudeSDKError):
    """Rate limit exceeded error."""
    
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        if details is None:
            details = {}
        if retry_after:
            details["retry_after"] = retry_after
        super().__init__(
            message=message,
            error_type="rate_limit_error",
            error_code="RATE_LIMIT",
            details=details
        )


class ValidationError(ClaudeSDKError):
    """Request validation error."""
    
    def __init__(self, message: str, field: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        if details is None:
            details = {}
        if field:
            details["field"] = field
        super().__init__(
            message=message,
            error_type="validation_error",
            error_code="VALIDATION_ERROR",
            details=details
        )


class SDKError(ClaudeSDKError):
    """Generic SDK error."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_type="sdk_error",
            error_code="SDK_ERROR",
            details=details
        )


class TimeoutError(ClaudeSDKError):
    """Request timeout error."""
    
    def __init__(self, message: str = "Request timed out", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_type="timeout_error",
            error_code="TIMEOUT",
            details=details
        )