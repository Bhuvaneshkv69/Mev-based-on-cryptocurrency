"""Experiment Request and Response Schemas.

Defines Pydantic models for creating, updating, listing, and returning
MEV simulation experiments, as well as reporting summary statistics.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class ExperimentModuleEnum(str, Enum):
    """Allowed simulation module identifiers."""

    PROTECTION = "protection"
    DECENTRALIZATION = "decentralization"
    EFFICIENCY = "efficiency"


class ExperimentStatusEnum(str, Enum):
    """Allowed simulation lifecycle statuses."""

    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


# ------------------------------------------------------------------------------
# 1. Experiment Creation Schema
# ------------------------------------------------------------------------------
class ExperimentCreate(BaseModel):
    """Payload accepted when registering a new experiment."""

    module: str = Field(
        ...,
        description="Target simulation module: 'protection', 'decentralization', or 'efficiency'",
        examples=["protection"],
    )
    scenario: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Scenario identifier or human-readable label",
        examples=["sandwich_v2_pool_sim"],
    )
    input_parameters: Dict[str, Any] = Field(
        ...,
        description="Simulation parameters and settings dictionary",
        examples=[{"trade_amount_eth": 5.0, "slippage_tolerance_pct": 0.5}],
    )
    assumptions: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional environmental assumptions and notes",
        examples=[{"mempool_latency_ms": 150, "data_source": "synthetic"}],
    )

    @field_validator("module")
    @classmethod
    def validate_module_name(cls, value: str) -> str:
        """Enforce that module matches one of the three supported modules."""
        normalized = value.strip().lower()
        allowed = {e.value for e in ExperimentModuleEnum}
        if normalized not in allowed:
            raise ValueError(
                f"Invalid module '{value}'. Supported modules: {', '.join(sorted(allowed))}"
            )
        return normalized

    @field_validator("scenario")
    @classmethod
    def validate_scenario(cls, value: str) -> str:
        """Ensure scenario is not empty or pure whitespace."""
        stripped = value.strip()
        if not stripped:
            raise ValueError("Scenario identifier cannot be empty")
        return stripped

    @field_validator("input_parameters")
    @classmethod
    def validate_input_parameters(cls, value: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure input_parameters is a non-empty dictionary."""
        if not isinstance(value, dict) or len(value) == 0:
            raise ValueError("input_parameters must be a non-empty dictionary")
        # Guard against absurdly large JSON payloads (>100 keys)
        if len(value) > 100:
            raise ValueError("input_parameters cannot exceed 100 top-level keys")
        return value

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "module": "protection",
                "scenario": "sample_sandwich_scenario",
                "input_parameters": {
                    "trade_amount": 100,
                    "slippage_tolerance": 0.01,
                },
                "assumptions": {
                    "data_source": "simulated",
                    "notes": "Example inputs for testing",
                },
            }
        }
    )


# ------------------------------------------------------------------------------
# 2. Experiment Metadata Update Schema
# ------------------------------------------------------------------------------
class ExperimentUpdate(BaseModel):
    """Fields that can be safely updated by an API client.

    Note: Clients cannot arbitrarily alter 'status', 'module', or 'results'
    through this endpoint.
    """

    scenario: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="Updated scenario identifier or label",
    )
    assumptions: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Updated assumptions or user notes",
    )

    @field_validator("scenario")
    @classmethod
    def validate_scenario_if_provided(cls, value: Optional[str]) -> Optional[str]:
        if value is not None:
            stripped = value.strip()
            if not stripped:
                raise ValueError("Scenario cannot be empty if specified")
            return stripped
        return value

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "scenario": "updated_scenario_title",
                "assumptions": {"notes": "Updated simulation assumptions"},
            }
        }
    )


# ------------------------------------------------------------------------------
# 3. Experiment Detailed Response Schema
# ------------------------------------------------------------------------------
class ExperimentResponse(BaseModel):
    """Complete representation of a persisted experiment."""

    id: int = Field(..., description="Unique database identifier")
    module: str = Field(..., description="Simulation module identifier")
    scenario: str = Field(..., description="Scenario identifier or label")
    status: str = Field(..., description="Current status: pending, completed, or failed")
    input_parameters: Dict[str, Any] = Field(..., description="Simulation input parameters")
    results: Optional[Dict[str, Any]] = Field(None, description="Output results, null if pending")
    assumptions: Optional[Dict[str, Any]] = Field(None, description="Experiment assumptions and notes")
    error_message: Optional[str] = Field(None, description="Error details if execution failed")
    created_at: datetime = Field(..., description="UTC creation timestamp")
    updated_at: datetime = Field(..., description="UTC last-update timestamp")

    # Pydantic v2 configuration enabling direct serialization from SQLAlchemy models
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "module": "protection",
                "scenario": "sample_sandwich_scenario",
                "status": "pending",
                "input_parameters": {
                    "trade_amount": 100,
                    "slippage_tolerance": 0.01,
                },
                "results": None,
                "assumptions": {
                    "data_source": "simulated",
                },
                "error_message": None,
                "created_at": "2026-10-11T12:00:00Z",
                "updated_at": "2026-10-11T12:00:00Z",
            }
        },
    )


# ------------------------------------------------------------------------------
# 4. Paginated Experiment List Response Schema
# ------------------------------------------------------------------------------
class ExperimentListResponse(BaseModel):
    """Paginated list of experiment records."""

    items: List[ExperimentResponse] = Field(..., description="List of experiments on this page")
    total: int = Field(..., description="Total number of experiments matching filters")
    page: int = Field(..., description="Current page number (1-indexed)")
    page_size: int = Field(..., description="Number of items per page")
    total_pages: int = Field(..., description="Total pages available")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [],
                "total": 0,
                "page": 1,
                "page_size": 20,
                "total_pages": 0,
            }
        }
    )


# ------------------------------------------------------------------------------
# 5. Reporting Summary Schema
# ------------------------------------------------------------------------------
class ReportSummaryResponse(BaseModel):
    """Aggregated experiment statistics across all modules and statuses."""

    total_experiments: int = Field(..., description="Total number of recorded experiments")
    by_module: Dict[str, int] = Field(..., description="Experiment count grouped by module")
    by_status: Dict[str, int] = Field(..., description="Experiment count grouped by execution status")
    latest_experiment_at: Optional[datetime] = Field(
        None, description="UTC timestamp of the most recent experiment, or null if none exist"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_experiments": 5,
                "by_module": {
                    "protection": 2,
                    "decentralization": 2,
                    "efficiency": 1,
                },
                "by_status": {
                    "pending": 4,
                    "completed": 1,
                    "failed": 0,
                },
                "latest_experiment_at": "2026-10-11T12:30:00Z",
            }
        }
    )
