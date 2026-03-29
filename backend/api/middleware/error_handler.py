"""Exception handling middleware for PAI API

Maps custom PAI exceptions to HTTP responses with proper status codes
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from datetime import datetime, timezone
import logging

from backend.core.exceptions import PAIException
from backend.core.models import ErrorResponse

logger = logging.getLogger(__name__)


def setup_exception_handlers(app: FastAPI):
    """Setup exception handlers for the FastAPI application"""

    @app.exception_handler(PAIException)
    async def pai_exception_handler(request: Request, exc: PAIException):
        """Handle custom PAI exceptions"""
        logger.warning(
            f"PAI Exception: {exc.error_code} - {str(exc)} | "
            f"Path: {request.url.path} | Method: {request.method}"
        )

        error_response = ErrorResponse(
            error_code=exc.error_code,
            message=str(exc),
            http_status_code=exc.http_status_code,
            timestamp=datetime.now(timezone.utc)
        )

        return JSONResponse(
            status_code=exc.http_status_code,
            content=error_response.model_dump()
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handle validation errors from request bodies"""
        logger.warning(
            f"Validation Error | Path: {request.url.path} | "
            f"Errors: {exc.errors()}"
        )

        error_response = ErrorResponse(
            error_code="VALIDATION_ERROR",
            message="Request validation failed",
            http_status_code=422,
            timestamp=datetime.now(timezone.utc),
            details=exc.errors()
        )

        return JSONResponse(
            status_code=422,
            content=error_response.model_dump(exclude_none=True)
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle unexpected exceptions"""
        logger.error(
            f"Unhandled Exception: {str(exc)} | "
            f"Path: {request.url.path} | Method: {request.method}",
            exc_info=True
        )

        error_response = ErrorResponse(
            error_code="INTERNAL_SERVER_ERROR",
            message="An unexpected error occurred",
            http_status_code=500,
            timestamp=datetime.now(timezone.utc)
        )

        return JSONResponse(
            status_code=500,
            content=error_response.model_dump()
        )
