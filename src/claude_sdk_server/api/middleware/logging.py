"""Logging middleware for request/response tracking."""

import time
import uuid
from typing import Callable

from fastapi import FastAPI, Request, Response
from fastapi.routing import APIRoute
from starlette.middleware.base import BaseHTTPMiddleware
from loguru import logger


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging requests and responses."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and log details."""
        # Generate request ID
        request_id = str(uuid.uuid4())[:8]
        
        # Start timer
        start_time = time.time()
        
        # Log request
        logger.bind(request_id=request_id).info(
            f"REQUEST | {request.method} {request.url.path} | "
            f"Client: {request.client.host if request.client else 'unknown'}"
        )
        
        # Add request ID to request state
        request.state.request_id = request_id
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Log response
            logger.bind(request_id=request_id).info(
                f"RESPONSE | Status: {response.status_code} | "
                f"Duration: {duration:.3f}s"
            )
            
            # Add headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = str(duration)
            
            return response
            
        except Exception as e:
            # Calculate duration
            duration = time.time() - start_time
            
            # Log error
            logger.bind(request_id=request_id).error(
                f"ERROR | {type(e).__name__}: {str(e)} | "
                f"Duration: {duration:.3f}s"
            )
            
            raise


class LoggingRoute(APIRoute):
    """Custom route class for detailed endpoint logging."""
    
    def get_route_handler(self) -> Callable:
        """Get route handler with logging."""
        original_route_handler = super().get_route_handler()
        
        async def logged_route_handler(request: Request) -> Response:
            """Handle route with logging."""
            # Log endpoint access
            logger.debug(
                f"Endpoint accessed: {self.path} | "
                f"Method: {request.method} | "
                f"Name: {self.name}"
            )
            
            # Call original handler
            response = await original_route_handler(request)
            
            return response
        
        return logged_route_handler


def setup_logging_middleware(app: FastAPI) -> None:
    """Setup logging middleware."""
    logger.info("Setting up logging middleware")
    
    # Add logging middleware
    app.add_middleware(LoggingMiddleware)
    
    # Set custom route class for detailed logging
    app.router.route_class = LoggingRoute
    
    logger.info("Logging middleware configured successfully")