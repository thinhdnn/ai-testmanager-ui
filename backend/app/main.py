from fastapi import FastAPI, Depends, Request, HTTPException
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRoute
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import text
import traceback
import logging
import os

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
    redirect_slashes=False,
    # Disable default docs to use custom endpoint
    docs_url=None,
    redoc_url=None,
    openapi_url="/openapi.json"
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

# Mount static files for Swagger UI customization
static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Custom Swagger UI endpoint with dark mode support
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    """
    Custom Swagger UI HTML with dark mode toggle functionality
    """
    return HTMLResponse(content="""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <meta name="description" content="SwaggerUI" />
    <title>SwaggerUI</title>
    <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@5.10.3/swagger-ui.css" />
    <link rel="stylesheet" type="text/css" href="/static/css/swagger-dark.css" />
    <style>
        html {
            box-sizing: border-box;
            overflow: -moz-scrollbars-vertical;
            overflow-y: scroll;
        }
        *, *:before, *:after {
            box-sizing: inherit;
        }
        body {
            margin:0;
            background: #fafafa;
        }
    </style>
</head>
<body>
    <div id="swagger-ui"></div>
    <script src="https://unpkg.com/swagger-ui-dist@5.10.3/swagger-ui-bundle.js" crossorigin></script>
    <script src="https://unpkg.com/swagger-ui-dist@5.10.3/swagger-ui-standalone-preset.js" crossorigin></script>
    <script src="/static/js/swagger-dark-mode.js" crossorigin></script>
    <script>
        window.onload = function() {
            // Build a system
            const ui = SwaggerUIBundle({
                url: '/openapi.json',
                dom_id: '#swagger-ui',
                deepLinking: true,
                presets: [
                    SwaggerUIBundle.presets.apis,
                    SwaggerUIStandalonePreset
                ],
                plugins: [
                    SwaggerUIBundle.plugins.DownloadUrl
                ],
                layout: "BaseLayout",
                displayRequestDuration: true,
                requestSnippetsEnabled: true,
                requestSnippets: {
                    generators: {
                        'curl_bash': {
                            title: 'cURL (bash)',
                            syntax: 'bash'
                        }
                    }
                },
                showExtensions: true,
                showCommonExtensions: true,
                operationsSorter: 'method',
                tagsSorter: 'alpha',
                filter: true,
                showRequestHeaders: true,
                tryItOutEnabled: true,
                defaultModelsExpandDepth: 1,
                defaultModelExpandDepth: 1,
                displayOperationId: false,
                onComplete: function() {
                    // Initialize dark mode functionality after Swagger UI loads
                    setTimeout(function() {
                        if (window.swaggerDarkMode) {
                            window.swaggerDarkMode.init();
                        }
                    }, 100);
                }
            });

            // Initialize theme based on localStorage
            setTimeout(function() {
                const savedTheme = localStorage.getItem('swagger-ui-theme');
                if (savedTheme === 'dark') {
                    document.body.classList.add('dark-mode');
                }
            }, 200);

            window.ui = ui
        }
    </script>
</body>
</html>
    """)

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