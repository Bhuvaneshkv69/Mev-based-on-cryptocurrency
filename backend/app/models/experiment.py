"""Experiment Database Model.

Defines the PostgreSQL schema for storing simulation experiments,
input parameters, execution statuses, and generated results across all
three MEVShield modules.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Index,
    JSON,
)
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql import func

from app.database import Base


class ExperimentModule(str, Enum):
    """Supported MEV simulation modules in MEVShield."""

    PROTECTION = "protection"           # Module 1: Front-running and sandwich attack mitigation
    DECENTRALIZATION = "decentralization"  # Module 2: Builder market share and relay concentration
    EFFICIENCY = "efficiency"           # Module 3: Gas dynamics and transaction competition


class ExperimentStatus(str, Enum):
    """Execution status lifecycle for simulation experiments."""

    PENDING = "pending"      # Registered; ready for execution in subsequent simulation phases
    COMPLETED = "completed"  # Successfully computed with results populated
    FAILED = "failed"        # Failed execution with safe error details recorded


# Use JSON column with PostgreSQL JSONB variant for binary indexing and high performance
JSONB_VARIANT = JSON().with_variant(postgresql.JSONB(), "postgresql")


class Experiment(Base):
    """SQLAlchemy model representing an MEV experiment."""

    __tablename__ = "experiments"

    # 1. Primary Key
    id: int = Column(Integer, primary_key=True, autoincrement=True, index=True)

    # 2. Module Identification (protection, decentralization, efficiency)
    module: str = Column(String(50), nullable=False, index=True)

    # 3. Scenario Description / Identifier
    scenario: str = Column(String(100), nullable=False)

    # 4. Lifecycle Status (pending, completed, failed)
    status: str = Column(
        String(20),
        nullable=False,
        default=ExperimentStatus.PENDING.value,
        index=True,
    )

    # 5. Simulation Parameters (JSON/JSONB)
    input_parameters: Dict[str, Any] = Column(JSONB_VARIANT, nullable=False)

    # 6. Simulation Results (JSON/JSONB; null when status is pending)
    results: Optional[Dict[str, Any]] = Column(JSONB_VARIANT, nullable=True, default=None)

    # 7. Experiment Assumptions / Metadata
    assumptions: Optional[Dict[str, Any]] = Column(JSONB_VARIANT, nullable=True, default=None)

    # 8. Non-sensitive failure explanation (populated if status is failed)
    error_message: Optional[str] = Column(Text, nullable=True, default=None)

    # 9. Timezone-Aware Audit Timestamps (UTC)
    created_at: datetime = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )
    updated_at: datetime = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Composite Index for common filtering (e.g., list experiments by module ordered by newest first)
    __table_args__ = (
        Index("ix_experiments_module_created_at", "module", "created_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<Experiment(id={self.id}, module='{self.module}', "
            f"scenario='{self.scenario}', status='{self.status}')>"
        )
