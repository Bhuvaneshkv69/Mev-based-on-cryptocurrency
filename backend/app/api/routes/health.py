"""Health and Readiness Check Routes.

Provides operational health checks (liveness) and database connectivity checks
(readiness) to enable robust monitoring and Kubernetes/Docker health probes.
"""

from typing import Dict, Any
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.database import check_db_connectivity
from app.schemas.common import HealthResponse

# Create router for health-related endpoints
router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Service Liveness Check",
    description="Returns the operational status of the web service without database dependencies.",
    response_description="Service is running and accepting HTTP requests",
)
async def check_health() -> HealthResponse:
    """Return operational health status of the MEVShield backend.

    This liveness probe verifies that the FastAPI/Uvicorn process is active.
    It does NOT depend on database availability.
    """
    return HealthResponse(
        status="healthy",
        service=settings.APP_NAME,
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
    )


@router.get(
    "/health/ready",
    summary="Database Readiness Check",
    description="Tests live connectivity to the PostgreSQL database by issuing a lightweight ping query.",
    response_description="Database connectivity status",
)
def check_readiness() -> JSONResponse:
    """Readiness probe that checks database connectivity.

    Returns HTTP 200 if the database responds, or HTTP 503 if unreachable.
    """
    is_connected, message = check_db_connectivity()

    if is_connected:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "ready",
                "database": "connected",
                "message": message,
            },
        )

    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "status": "not_ready",
            "database": "disconnected",
            "message": message,
        },
    )
