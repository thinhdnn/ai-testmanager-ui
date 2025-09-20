from fastapi import FastAPI, Depends, Request, HTTPException
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRoute
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
import traceback
import logging

from .config import settings
from .database import get_db, get_engine, Base
from .models import *
from .api.api import api_router

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    version="1.0.0",
    # Disable automatic redirect for trailing slashes
    redirect_slashes=False
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context: setup and teardown."""
    try:
        Base.metadata.create_all(bind=get_engine())
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        # Do not crash app if DB is unavailable at startup
    yield
    # No teardown actions needed currently

# Attach lifespan handler
app.router.lifespan_context = lifespan

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8080"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],  # Allow all response headers to be exposed
    max_age=3600,  # Cache preflight requests for 1 hour
)

@app.middleware("http")
async def log_exceptions(request: Request, call_next):
    try:
        logger.debug(f"Processing request: {request.method} {request.url}")
        response = await call_next(request)
        logger.debug(f"Request completed: {request.method} {request.url} - Status: {response.status_code}")
        return response
    except Exception as e:
        logger.error(f"Exception in request {request.url}:")
        logger.error(f"Error: {str(e)}")
        logger.error("Traceback:")
        logger.error(traceback.format_exc())
        raise

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception handler caught: {type(exc).__name__}")
    logger.error(f"Error message: {str(exc)}")
    logger.error("Traceback:")
    logger.error(traceback.format_exc())
    
    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail}
        )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

# Include API router
app.include_router(api_router, prefix="/api/v1")

# Health check endpoint
@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    try:
        # Try to execute a simple query
        db.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": str(e)} 