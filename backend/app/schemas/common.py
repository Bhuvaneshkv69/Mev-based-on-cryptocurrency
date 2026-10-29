"""Common API Schemas.

Defines Pydantic models used for standard API responses, including
health check status, root service info, and general error messages.
"""

from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class HealthResponse(BaseModel):
    """Schema for the GET /api/health endpoint response."""

    status: str = Field(
        ...,
        description="Current operational status of the service",
        examples=["healthy"],
    )
    service: str = Field(
        ...,
        description="Name of the backend service",
        examples=["MEVShield API"],
    )
    version: str = Field(
        ...,
        description="Semantic version of the application",
        examples=["1.0.0"],
    )
    environment: str = Field(
        ...,
        description="Deployment environment mode",
        examples=["development"],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "healthy",
                "service": "MEVShield API",
                "version": "1.0.0",
                "environment": "development",
            }
        }
    )


class RootResponse(BaseModel):
    """Schema for the GET / root endpoint response."""

    name: str = Field(
        ...,
        description="Application name",
        examples=["MEVShield API"],
    )
    version: str = Field(
        ...,
        description="Application version",
        examples=["1.0.0"],
    )
    environment: str = Field(
        ...,
        description="Deployment environment mode",
        examples=["development"],
    )
    description: str = Field(
        ...,
        description="Concise description of the platform purpose",
        examples=["Educational MEV analysis and simulation platform for Ethereum"],
    )
    health_check: str = Field(
        ...,
        description="Direct path to the health check endpoint",
        examples=["/api/health"],
    )
    documentation: Optional[str] = Field(
        None,
        description="Path to interactive API documentation, if enabled",
        examples=["/docs"],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "MEVShield API",
                "version": "1.0.0",
                "environment": "development",
                "description": "Educational MEV analysis and simulation platform for Ethereum",
                "health_check": "/api/health",
                "documentation": "/docs",
            }
        }
    )


class ErrorResponse(BaseModel):
    """Standardized JSON error response schema."""

    detail: str = Field(
        ...,
        description="Human-readable error explanation",
        examples=["Resource not found"],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "detail": "An internal server error occurred. Please contact the administrator."
            }
        }
    )
