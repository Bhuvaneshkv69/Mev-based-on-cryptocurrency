"""Reports and Summary API Routes.

Provides aggregated statistics on stored simulation experiments,
including totals, module distribution, and status breakdowns.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.experiment import ReportSummaryResponse
from app.services.experiment_service import ExperimentService

router = APIRouter()


@router.get(
    "/summary",
    response_model=ReportSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Experiment Reports Summary",
    description="Returns aggregate database metrics including total counts, module breakdown, and execution statuses.",
)
def get_report_summary(
    db: Session = Depends(get_db),
) -> ReportSummaryResponse:
    """Retrieve database-backed summary statistics across all experiments."""
    return ExperimentService.get_report_summary(db)
