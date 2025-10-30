"""
ReconAI Backend - Main FastAPI Application

This is the main entry point for the ReconAI backend API.
Handles initialization, middleware, and route registration.
"""

import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from dotenv import load_dotenv

from app.core.firebase import initialize_firebase
from app.core.database import connect_to_mongodb, close_mongodb_connection, check_database_health
from app.core.redis_client import connect_to_redis, close_redis_connection, check_redis_health
from app.middleware.auth import FirebaseAuthMiddleware
from app.api.routes import auth, assets

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize Sentry if DSN is provided
sentry_dsn = os.getenv("SENTRY_DSN")
if sentry_dsn:
    sentry_sdk.init(
        dsn=sentry_dsn,
        integrations=[FastApiIntegration()],
        traces_sample_rate=0.1,
        environment=os.getenv("ENVIRONMENT", "development")
    )
    logger.info("Sentry initialized for error tracking")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager.

    Handles startup and shutdown events:
    - Startup: Initialize Firebase, MongoDB, Redis
    - Shutdown: Close database connections
    """
    # Startup
    logger.info("Starting ReconAI Backend...")

    try:
        # Initialize Firebase Admin SDK
        initialize_firebase()
        logger.info("✓ Firebase initialized")

        # Connect to MongoDB
        await connect_to_mongodb()
        logger.info("✓ MongoDB connected")

        # Connect to Redis
        connect_to_redis()
        logger.info("✓ Redis connected")

        logger.info("ReconAI Backend started successfully")

    except Exception as e:
        logger.error(f"Failed to start application: {str(e)}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down ReconAI Backend...")

    try:
        await close_mongodb_connection()
        close_redis_connection()
        logger.info("All connections closed successfully")

    except Exception as e:
        logger.error(f"Error during shutdown: {str(e)}")


# Create FastAPI application
app = FastAPI(
    title="ReconAI API",
    description="OSINT platform for asset discovery, risk scoring, and security intelligence",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure CORS
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add Firebase authentication middleware
app.add_middleware(FirebaseAuthMiddleware)

# Include routers
app.include_router(auth.router)
app.include_router(assets.router)

# Health check endpoint (public - no auth required)
@app.get("/health", tags=["system"])
async def health_check():
    """
    Health check endpoint.

    Returns system status and service health information.
    No authentication required.

    Returns:
        200: System is healthy
        503: One or more services are unhealthy
    """
    try:
        # Check database
        db_health = await check_database_health()

        # Check Redis
        redis_health = await check_redis_health()

        # Determine overall status
        all_healthy = (
            db_health.get("status") == "connected" and
            redis_health.get("status") == "connected"
        )

        status_code = 200 if all_healthy else 503

        return JSONResponse(
            status_code=status_code,
            content={
                "status": "healthy" if all_healthy else "degraded",
                "services": {
                    "mongodb": db_health.get("status"),
                    "redis": redis_health.get("status"),
                },
                "details": {
                    "mongodb": db_health,
                    "redis": redis_health,
                }
            }
        )

    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e)
            }
        )


# Root endpoint
@app.get("/", tags=["system"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": "ReconAI API",
        "version": "1.0.0",
        "description": "OSINT platform for asset discovery and risk scoring",
        "docs": "/docs",
        "health": "/health"
    }


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """
    Global exception handler for unhandled errors.

    Logs error and returns generic error response.
    """
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)

    return JSONResponse(
        status_code=500,
        content={
            "error": "InternalServerError",
            "detail": "An unexpected error occurred"
        }
    )


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=True,  # Disable in production
        log_level="info"
    )
