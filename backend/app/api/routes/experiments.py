"""Experiment API Routes.

Provides RESTful endpoints for creating, retrieving, listing with pagination,
updating metadata, and deleting MEV simulation experiments.
"""

import math
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.common import ErrorResponse
from app.schemas.experiment import (
    ExperimentCreate,
    ExperimentUpdate,
    ExperimentResponse,
    ExperimentListResponse,
)
from app.services.experiment_service import ExperimentService

router = APIRouter()


@router.post(
    "",
    response_model=ExperimentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create New Experiment",
    description="Registers a new MEV simulation experiment in the 'pending' state.",
    responses={
        201: {"description": "Experiment created successfully"},
        422: {"description": "Validation error in request payload"},
    },
)
def create_experiment(
    payload: ExperimentCreate,
    db: Session = Depends(get_db),
) -> ExperimentResponse:
    """Create a new experiment record.

    Validates that the module is supported ('protection', 'decentralization', or 'efficiency')
    and persists initial input parameters.
    """
    return ExperimentService.create_experiment(db, payload)


@router.get(
    "",
    response_model=ExperimentListResponse,
    status_code=status.HTTP_200_OK,
    summary="List Experiments",
    description="Returns a paginated list of experiments, optionally filtered by module or status.",
)
def list_experiments(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page (max 100)"),
    module: Optional[str] = Query(None, description="Filter by module (e.g. 'protection')"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status ('pending', 'completed', 'failed')"),
    db: Session = Depends(get_db),
) -> ExperimentListResponse:
    """Retrieve experiments with pagination and deterministic sorting (newest first)."""
    items, total = ExperimentService.list_experiments(
        db=db,
        page=page,
        page_size=page_size,
        module=module,
        status=status_filter,
    )

    total_pages = math.ceil(total / page_size) if total > 0 else 0

    return ExperimentListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get(
    "/{experiment_id}",
    response_model=ExperimentResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Experiment by ID",
    description="Retrieves a specific experiment record by its database ID.",
    responses={
        200: {"description": "Experiment found"},
        404: {"model": ErrorResponse, "description": "Experiment not found"},
    },
)
def get_experiment(
    experiment_id: int = Path(..., ge=1, description="Primary key ID of the experiment"),
    db: Session = Depends(get_db),
) -> ExperimentResponse:
    """Retrieve a single experiment record by ID."""
    experiment = ExperimentService.get_by_id(db, experiment_id)
    if not experiment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Experiment with ID {experiment_id} not found",
        )
    return experiment


@router.patch(
    "/{experiment_id}",
    response_model=ExperimentResponse,
    status_code=status.HTTP_200_OK,
    summary="Update Experiment Metadata",
    description="Allows updating metadata such as scenario label or assumptions. Does not allow tampering with status or results.",
    responses={
        200: {"description": "Experiment updated successfully"},
        404: {"model": ErrorResponse, "description": "Experiment not found"},
    },
)
def update_experiment(
    payload: ExperimentUpdate,
    experiment_id: int = Path(..., ge=1, description="Primary key ID of the experiment"),
    db: Session = Depends(get_db),
) -> ExperimentResponse:
    """Update metadata for an existing experiment."""
    experiment = ExperimentService.get_by_id(db, experiment_id)
    if not experiment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Experiment with ID {experiment_id} not found",
        )
    return ExperimentService.update_experiment(db, experiment, payload)


@router.delete(
    "/{experiment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Experiment",
    description="Deletes an experiment record from the database.",
    responses={
        204: {"description": "Experiment deleted successfully"},
        404: {"model": ErrorResponse, "description": "Experiment not found"},
    },
)
def delete_experiment(
    experiment_id: int = Path(..., ge=1, description="Primary key ID of the experiment"),
    db: Session = Depends(get_db),
) -> None:
    """Remove an experiment from the database."""
    experiment = ExperimentService.get_by_id(db, experiment_id)
    if not experiment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Experiment with ID {experiment_id} not found",
        )
    ExperimentService.delete_experiment(db, experiment)
