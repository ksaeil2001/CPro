"""Add warnings_json and current_stage columns to jobs table.

Revision ID: 001
Revises: None
Create Date: 2026-02-10
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("jobs", sa.Column("warnings_json", sa.String(), nullable=True))
    op.add_column("jobs", sa.Column("current_stage", sa.String(50), nullable=True))


def downgrade() -> None:
    op.drop_column("jobs", "current_stage")
    op.drop_column("jobs", "warnings_json")
