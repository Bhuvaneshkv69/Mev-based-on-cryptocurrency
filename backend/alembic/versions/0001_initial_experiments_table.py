"""Initial experiments table schema.

Revision ID: 0001_initial_experiments
Revises: 
Create Date: 2026-10-11 15:35:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0001_initial_experiments"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Use JSON with JSONB variant for PostgreSQL
    jsonb_type = sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql")

    op.create_table(
        "experiments",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("module", sa.String(length=50), nullable=False),
        sa.Column("scenario", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="pending", nullable=False),
        sa.Column("input_parameters", jsonb_type, nullable=False),
        sa.Column("results", jsonb_type, nullable=True),
        sa.Column("assumptions", jsonb_type, nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes for search, filtering, and reporting performance
    op.create_index(op.f("ix_experiments_id"), "experiments", ["id"], unique=False)
    op.create_index(op.f("ix_experiments_module"), "experiments", ["module"], unique=False)
    op.create_index(op.f("ix_experiments_status"), "experiments", ["status"], unique=False)
    op.create_index(op.f("ix_experiments_created_at"), "experiments", ["created_at"], unique=False)
    op.create_index(
        "ix_experiments_module_created_at",
        "experiments",
        ["module", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_experiments_module_created_at", table_name="experiments")
    op.drop_index(op.f("ix_experiments_created_at"), table_name="experiments")
    op.drop_index(op.f("ix_experiments_status"), table_name="experiments")
    op.drop_index(op.f("ix_experiments_module"), table_name="experiments")
    op.drop_index(op.f("ix_experiments_id"), table_name="experiments")
    op.drop_table("experiments")
