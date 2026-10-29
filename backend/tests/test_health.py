"""Automated Test Suite for API Foundation and Health Check.

Tests the basic endpoints, schema conformity, routing prefixes,
error responses, and CORS configuration without requiring an external server,
database, or blockchain node.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import settings
from app.schemas.common import HealthResponse, RootResponse


@pytest.fixture(scope="module")
def client() -> TestClient:
    """Fixture providing a reusable FastAPI TestClient instance."""
    with TestClient(app) as test_client:
        yield test_client


def test_root_endpoint_returns_200_and_valid_payload(client: TestClient) -> None:
    """Requirement 1: Verify GET / returns HTTP 200 and matches RootResponse schema."""
    response = client.get("/")
    assert response.status_code == 200

    data = response.json()
    # Validate payload structure against Pydantic schema
    validated = RootResponse(**data)
    assert validated.name == settings.APP_NAME
    assert validated.version == settings.APP_VERSION
    assert validated.environment == settings.ENVIRONMENT
    assert validated.health_check == f"{settings.API_PREFIX}/health"


def test_health_endpoint_returns_200(client: TestClient) -> None:
    """Requirement 2: Verify GET /api/health returns HTTP 200."""
    response = client.get(f"{settings.API_PREFIX}/health")
    assert response.status_code == 200


def test_health_response_contains_required_fields(client: TestClient) -> None:
    """Requirement 3: Verify the health response contains all required fields."""
    response = client.get(f"{settings.API_PREFIX}/health")
    assert response.status_code == 200

    data = response.json()
    required_keys = {"status", "service", "version", "environment"}
    assert required_keys.issubset(data.keys())


def test_health_status_is_healthy(client: TestClient) -> None:
    """Requirement 4: Verify that the status field value is 'healthy'."""
    response = client.get(f"{settings.API_PREFIX}/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == settings.APP_NAME
    assert data["version"] == settings.APP_VERSION
    assert data["environment"] == settings.ENVIRONMENT


def test_health_response_matches_pydantic_schema(client: TestClient) -> None:
    """Requirement 5: Verify the response conforms to HealthResponse schema."""
    response = client.get(f"{settings.API_PREFIX}/health")
    assert response.status_code == 200

    # Pydantic validation: raises ValidationError if schema doesn't match
    health_obj = HealthResponse(**response.json())
    assert health_obj.status == "healthy"


def test_unknown_url_returns_404(client: TestClient) -> None:
    """Requirement 6: Verify that accessing a non-existent route returns HTTP 404."""
    response = client.get("/api/non-existent-endpoint-xyz")
    assert response.status_code == 404
    assert "detail" in response.json()


def test_api_prefix_is_applied_correctly(client: TestClient) -> None:
    """Requirement 7: Verify routing prefix behavior.

    /api/health must succeed (HTTP 200),
    whereas /health (without the prefix) must return HTTP 404.
    """
    valid_prefixed_response = client.get(f"{settings.API_PREFIX}/health")
    assert valid_prefixed_response.status_code == 200

    unprefixed_response = client.get("/health")
    assert unprefixed_response.status_code == 404


def test_cors_allows_configured_frontend_origin(client: TestClient) -> None:
    """Requirement 8: Verify CORS headers for the configured frontend origin."""
    allowed_origin = settings.ALLOWED_ORIGINS[0]

    # Test standard GET request with Origin header
    response = client.get(
        f"{settings.API_PREFIX}/health",
        headers={"Origin": allowed_origin},
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == allowed_origin

    # Test preflight OPTIONS request
    preflight_response = client.options(
        f"{settings.API_PREFIX}/health",
        headers={
            "Origin": allowed_origin,
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Content-Type",
        },
    )
    assert preflight_response.status_code == 200
    assert preflight_response.headers.get("access-control-allow-origin") == allowed_origin
    assert "GET" in preflight_response.headers.get("access-control-allow-methods", "")


def test_global_exception_handler_sanitizes_500_errors() -> None:
    """Requirement 9: Verify unhandled exceptions return a sanitized HTTP 500 JSON response."""
    # Register an endpoint that raises an unexpected internal exception
    @app.get("/api/test-server-error")
    def simulate_server_error() -> None:
        raise RuntimeError("Confidential server internal failure: DB_PASSWORD_123")

    # Create a TestClient configured not to re-raise internal server errors
    with TestClient(app, raise_server_exceptions=False) as unhandled_client:
        response = unhandled_client.get("/api/test-server-error")
        assert response.status_code == 500

        data = response.json()
        assert "detail" in data
        # Ensure internal details and stack traces are NOT exposed to clients
        assert "DB_PASSWORD_123" not in data["detail"]
        assert "RuntimeError" not in data["detail"]
        assert data["detail"] == "An internal server error occurred. Please contact the administrator."


def test_database_readiness_endpoint(client: TestClient) -> None:
    """Requirement: GET /api/health/ready distinguishes service liveness from DB readiness."""
    response = client.get(f"{settings.API_PREFIX}/health/ready")
    # Returns 200 if DB is operational, 503 if unreachable (non-crashing response)
    assert response.status_code in (200, 503)
    data = response.json()
    assert "status" in data
    assert "database" in data
    assert "message" in data


