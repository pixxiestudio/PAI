"""Logging middleware for request/response tracking"""

from fastapi import FastAPI
from fastapi.requests import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import logging
import time
import json

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Log all HTTP requests and responses"""

    async def dispatch(self, request: Request, call_next) -> Response:
        """Log request and response details"""
        start_time = time.time()
        request_id = request.headers.get("x-request-id", "")

        # Log request
        logger.info(
            f"Request ID: {request_id} | "
            f"{request.method} {request.url.path} | "
            f"Client: {request.client.host if request.client else 'unknown'}"
        )

        try:
            # Process request
            response = await call_next(request)

            # Calculate duration
            duration = time.time() - start_time

            # Log response
            logger.info(
                f"Request ID: {request_id} | "
                f"Status: {response.status_code} | "
                f"Duration: {duration:.3f}s"
            )

            # Add request ID to response headers
            response.headers["x-request-id"] = request_id

            return response

        except Exception as exc:
            duration = time.time() - start_time
            logger.error(
                f"Request ID: {request_id} | "
                f"Error: {str(exc)} | "
                f"Duration: {duration:.3f}s",
                exc_info=True
            )
            raise


def setup_logging_middleware(app: FastAPI):
    """Setup logging middleware for the application"""
    app.add_middleware(LoggingMiddleware)
