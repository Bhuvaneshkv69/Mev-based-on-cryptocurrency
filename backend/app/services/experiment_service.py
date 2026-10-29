"""Experiment Database Service.

Provides reusable database operations for managing simulation experiments,
handling queries, transaction boundaries, filtering, pagination, and reporting.
"""

from typing import List, Optional, Tuple
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.experiment import Experiment, ExperimentModule, ExperimentStatus
from app.schemas.experiment import (
    ExperimentCreate,
    ExperimentUpdate,
    ReportSummaryResponse,
)


class ExperimentService:
    """Service class handling persistence and reporting logic for experiments."""

    @staticmethod
    def create_experiment(db: Session, data: ExperimentCreate) -> Experiment:
        """Create and persist a new simulation experiment record.

        Defaults:
        - status: 'pending' (ready for execution in Phase 3+)
        - results: None (no fabricated or premature results stored)
        - error_message: None
        """
        experiment = Experiment(
            module=data.module,
            scenario=data.scenario,
            status=ExperimentStatus.PENDING.value,
            input_parameters=data.input_parameters,
            assumptions=data.assumptions,
            results=None,
            error_message=None,
        )
        db.add(experiment)
        db.commit()
        db.refresh(experiment)
        return experiment

    @staticmethod
    def get_by_id(db: Session, experiment_id: int) -> Optional[Experiment]:
        """Fetch a single experiment record by its primary key ID."""
        return db.query(Experiment).filter(Experiment.id == experiment_id).first()

    @staticmethod
    def list_experiments(
        db: Session,
        page: int = 1,
        page_size: int = 20,
        module: Optional[str] = None,
        status: Optional[str] = None,
    ) -> Tuple[List[Experiment], int]:
        """List experiments with optional filtering, pagination, and deterministic sorting.

        Returns:
            Tuple of (list_of_experiments, total_count_matching_filter)
        """
        query = db.query(Experiment)

        # Apply module filter if supplied
        if module:
            query = query.filter(Experiment.module == module.strip().lower())

        # Apply status filter if supplied
        if status:
            query = query.filter(Experiment.status == status.strip().lower())

        # Compute total matching records
        total = query.count()

        # Deterministic ordering: Newest first, with secondary sort on ID
        query = query.order_by(Experiment.created_at.desc(), Experiment.id.desc())

        # Pagination offset and limit
        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()

        return items, total

    @staticmethod
    def update_experiment(
        db: Session,
        experiment: Experiment,
        data: ExperimentUpdate,
    ) -> Experiment:
        """Update permissible metadata fields (scenario, assumptions) of an existing experiment.

        Does not allow modifying primary key, module, input_parameters, status, or results.
        """
        if data.scenario is not None:
            experiment.scenario = data.scenario
        if data.assumptions is not None:
            experiment.assumptions = data.assumptions

        db.commit()
        db.refresh(experiment)
        return experiment

    @staticmethod
    def delete_experiment(db: Session, experiment: Experiment) -> None:
        """Delete an experiment record from the database."""
        db.delete(experiment)
        db.commit()

    @staticmethod
    def get_report_summary(db: Session) -> ReportSummaryResponse:
        """Calculate aggregated metrics and counts across all recorded experiments."""
        # 1. Total count
        total_count = db.query(func.count(Experiment.id)).scalar() or 0

        # 2. Group by module
        module_rows = (
            db.query(Experiment.module, func.count(Experiment.id))
            .group_by(Experiment.module)
            .all()
        )
        # Initialize default zero counts for all supported modules
        by_module = {m.value: 0 for m in ExperimentModule}
        for mod, count in module_rows:
            by_module[mod] = count

        # 3. Group by status
        status_rows = (
            db.query(Experiment.status, func.count(Experiment.id))
            .group_by(Experiment.status)
            .all()
        )
        # Initialize default zero counts for all supported statuses
        by_status = {s.value: 0 for s in ExperimentStatus}
        for st, count in status_rows:
            by_status[st] = count

        # 4. Latest experiment timestamp
        latest_timestamp = db.query(func.max(Experiment.created_at)).scalar()

        return ReportSummaryResponse(
            total_experiments=total_count,
            by_module=by_module,
            by_status=by_status,
            latest_experiment_at=latest_timestamp,
        )
