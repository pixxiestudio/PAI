"""PAI - Personal AI Assistant Backend Server"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from backend.utils.config import settings


def create_app():
    """Create and configure FastAPI application"""
    app = FastAPI(
        title=settings.app_name,
        description="Personal AI Assistant powered by Claude Code Agent SDK",
        version="0.1.0"
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure properly in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Health check endpoint
    @app.get("/health")
    async def health_check():
        return {
            "status": "healthy",
            "app": settings.app_name,
            "version": "0.1.0"
        }

    # Root endpoint
    @app.get("/")
    async def root():
        return {
            "message": "Welcome to PAI - Personal AI Assistant",
            "docs": "/docs",
            "version": "0.1.0"
        }

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
