"""FastAPI REST API for PAI - Personal AI Assistant

This module sets up the main FastAPI application with:
- Session management endpoints
- Message handling
- Memory and learning tracking
- Error handling middleware
- Health checks
"""

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from datetime import datetime, timezone
import logging
import json

from backend.core.container import ServiceContainer
from backend.utils.config import settings
from backend.api.middleware.error_handler import setup_exception_handlers
from backend.api.middleware.logging import setup_logging_middleware
from backend.api.middleware.auth import JWTAuthMiddleware
from backend.api.middleware.rate_limit import RateLimitMiddleware

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global container instance
_container: ServiceContainer = None


def get_container() -> ServiceContainer:
    """Get the global service container for dependency injection"""
    return _container


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan context manager for startup/shutdown"""
    global _container

    # Startup
    logger.info("PAI API Server starting...")
    try:
        # Initialize container
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        # Create database engine with optimized pool configuration
        pool_kwargs = {
            "echo": settings.database_echo,
            "pool_pre_ping": True,
        }
        # SQLite doesn't support pool_size/max_overflow
        if not settings.database_url.startswith("sqlite"):
            pool_kwargs.update({
                "pool_size": settings.database_pool_size,
                "max_overflow": settings.database_max_overflow,
                "pool_recycle": settings.database_pool_recycle,
            })
        engine = create_engine(settings.database_url, **pool_kwargs)

        # Create session factory
        SessionLocal = sessionmaker(bind=engine)
        db_session = SessionLocal()

        # Initialize container with database session
        _container = ServiceContainer(db_session=db_session)
        logger.info("Service container initialized")

    except Exception as e:
        logger.error(f"Failed to start server: {str(e)}")
        raise

    yield

    # Shutdown
    logger.info("PAI API Server shutting down...")
    try:
        if _container:
            await _container.shutdown()
            logger.info("Service container shutdown complete")
    except Exception as e:
        logger.error(f"Error during shutdown: {str(e)}")


# Create FastAPI app
app = FastAPI(
    title="PAI - Personal AI Assistant API",
    description="REST API for Claude-powered AI Assistant with self-learning capabilities",
    version="2.0.0",
    lifespan=lifespan
)

# Setup exception handlers
setup_exception_handlers(app)

# Setup logging middleware
setup_logging_middleware(app)

# Add JWT authentication middleware
app.add_middleware(JWTAuthMiddleware)

# Add rate limiting middleware
app.add_middleware(RateLimitMiddleware)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.allowed_hosts
)

# Include API routes
from backend.api.v1 import sessions, messages, memory, learning, skills, health, auth, github, files, streaming

app.include_router(auth.router, prefix="/api/v1", tags=["auth"])
app.include_router(sessions.router, prefix="/api/v1", tags=["sessions"])
app.include_router(messages.router, prefix="/api/v1", tags=["messages"])
app.include_router(memory.router, prefix="/api/v1", tags=["memory"])
app.include_router(learning.router, prefix="/api/v1", tags=["learning"])
app.include_router(skills.router, prefix="/api/v1", tags=["skills"])
app.include_router(github.router, prefix="/api/v1", tags=["github"])
app.include_router(files.router, prefix="/api/v1", tags=["files"])
app.include_router(streaming.router, prefix="/api/v1", tags=["streaming"])
app.include_router(health.router, prefix="/api/v1", tags=["health"])


@app.get("/")
async def root():
    """Root endpoint - redirects to API docs"""
    return {
        "message": "PAI API Server",
        "docs": "/docs",
        "version": "2.0.0"
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug
    )
