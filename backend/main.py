"""PAI - Personal AI Assistant Backend Server"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging
from backend.utils.config import settings

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_app():
    """Create and configure FastAPI application"""
    app = FastAPI(
        title=settings.app_name,
        description="Personal AI Assistant powered by Claude Code Agent SDK",
        version="0.1.0"
    )

    # Add CORS middleware - configure allowed origins
    allowed_origins = [
        "http://localhost:3000",      # Local development
        "http://localhost:8000",      # Local API
        "http://127.0.0.1:3000",      # Alternative localhost
        "http://127.0.0.1:8000",      # Alternative localhost
    ]

    # Add production origins if specified in config
    if hasattr(settings, 'allowed_cors_origins') and settings.allowed_cors_origins:
        allowed_origins.extend(settings.allowed_cors_origins.split(','))

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization"],
    )

    logger.info(f"CORS enabled for origins: {allowed_origins}")

    # Health check endpoint
    @app.get("/health")
    async def health_check():
        logger.debug("Health check requested")
        return {
            "status": "healthy",
            "app": settings.app_name,
            "version": "0.1.0"
        }

    # Root endpoint
    @app.get("/")
    async def root():
        logger.debug("Root endpoint requested")
        return {
            "message": "Welcome to PAI - Personal AI Assistant",
            "docs": "/docs",
            "version": "0.1.0"
        }

    # Startup event
    @app.on_event("startup")
    async def startup_event():
        logger.info(f"Starting {settings.app_name}")
        logger.info(f"Debug mode: {settings.debug}")
        logger.info(f"Database: {settings.database_url}")

    # Shutdown event
    @app.on_event("shutdown")
    async def shutdown_event():
        logger.info(f"Shutting down {settings.app_name}")

    return app


# Create application instance
app = create_app()


if __name__ == "__main__":
    uvicorn.run(
        "backend.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
