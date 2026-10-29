"""MEVShield Application Entry Point.

Configures the FastAPI application instance, CORS middleware, global
exception handlers, central routing, and the root status endpoint.
"""

import logging
from typing import Dict, Any

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.core.config import settings
from app.database import Base, engine
from app.schemas.common import RootResponse, ErrorResponse

# Configure structured application logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(name)s - %(message)s",
)
logger = logging.getLogger("mevshield.backend")


def create_application() -> FastAPI:
    """Factory function to instantiate and configure the FastAPI application."""

    # Initialize database tables on startup
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database schema initialized successfully.")
    except Exception as exc:
        logger.warning("Automatic database schema setup skipped: %s", exc)

    # Determine whether API documentation should be accessible
    is_docs_active = settings.is_docs_enabled

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=settings.APP_DESCRIPTION,
        # Interactive docs configuration based on environment settings
        docs_url="/docs" if is_docs_active else None,
        redoc_url="/redoc" if is_docs_active else None,
        openapi_url="/openapi.json" if is_docs_active else None,
    )

    # --------------------------------------------------------------------------
    # CORS Middleware Setup
    # --------------------------------------------------------------------------
    # Enables secure cross-origin requests from the React frontend (e.g., Vite on :5173).
    # Credentials are only enabled when origins are explicitly listed (not wildcard '*').
    origins = settings.ALLOWED_ORIGINS
    allow_all_origins = "*" in origins

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        # In compliance with security standards, credentials cannot be True with wildcard origins
        allow_credentials=not allow_all_origins,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["Content-Type"],
    )

    # --------------------------------------------------------------------------
    # Global Exception Handling
    # --------------------------------------------------------------------------
    # Catch unexpected application exceptions, log the full traceback on the server,
    # and return a safe, sanitized JSON response without leaking internal details.
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.error(
            "Unhandled server exception occurred: %s at path %s",
            str(exc),
            request.url.path,
            exc_info=True,
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "An internal server error occurred. Please contact the administrator."},
        )

    # --------------------------------------------------------------------------
    # Mount Central API Router
    # --------------------------------------------------------------------------
    # All sub-routes (health, future simulation modules) will be prefixed with /api
    app.include_router(api_router, prefix=settings.API_PREFIX)

    # --------------------------------------------------------------------------
    # Mount Frontend Static Assets & Web Application
    # --------------------------------------------------------------------------
    from pathlib import Path
    from fastapi.responses import FileResponse
    from fastapi.staticfiles import StaticFiles

    frontend_dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"
    if frontend_dist.exists() and (frontend_dist / "assets").exists():
        app.mount(
            "/assets",
            StaticFiles(directory=str(frontend_dist / "assets")),
            name="assets",
        )

    # --------------------------------------------------------------------------
    # Root Endpoint (Serves Web Dashboard for browsers, RootResponse for API clients)
    # --------------------------------------------------------------------------
    @app.get(
        "/",
        response_model=None,
        status_code=status.HTTP_200_OK,
        summary="API Root Information / Web Dashboard",
        description="Serves the MEVShield React web UI or returns service metadata for API clients.",
        tags=["Service"],
    )
    async def get_root(request: Request) -> Any:
        accept = request.headers.get("accept", "")
        if "text/html" in accept and frontend_dist.exists() and (frontend_dist / "index.html").exists():
            return FileResponse(str(frontend_dist / "index.html"))

        return RootResponse(
            name=settings.APP_NAME,
            version=settings.APP_VERSION,
            environment=settings.ENVIRONMENT,
            description=settings.APP_DESCRIPTION,
            health_check=f"{settings.API_PREFIX}/health",
            documentation="/docs" if is_docs_active else None,
        )

    return app


# Instantiate the main FastAPI application object
app = create_application()
