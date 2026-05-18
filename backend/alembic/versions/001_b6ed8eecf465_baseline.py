"""Baseline schema — all tables, triggers, views, RLS policies.

Revision ID: b6ed8eecf465
Revises: (initial)
Create Date: 2026-05-18
"""

from pathlib import Path

from alembic import op

revision = "b6ed8eecf465"
down_revision = None
branch_labels = None
depends_on = None

_SQL_FILE = Path(__file__).parent / "001_initial_schema.sql"


def upgrade() -> None:
    op.execute(_SQL_FILE.read_text())


def downgrade() -> None:
    # Dropping the entire schema is destructive — do it manually if needed.
    raise NotImplementedError("Downgrade from baseline is not supported automatically.")
