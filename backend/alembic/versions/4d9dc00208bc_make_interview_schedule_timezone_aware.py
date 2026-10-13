
"""Make interview schedule timezone aware.

Revision ID: 4d9dc00208bc
Revises: 1aef30c53524
"""

from alembic import op
import sqlalchemy as sa

revision = "4d9dc00208bc"
down_revision = "1aef30c53524"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "interviews",
        "scheduled_at",
        existing_type=sa.DateTime(timezone=False),
        type_=sa.DateTime(timezone=True),
        existing_nullable=False,
        postgresql_using="scheduled_at AT TIME ZONE 'Asia/Kolkata'",
    )


def downgrade() -> None:
    op.alter_column(
        "interviews",
        "scheduled_at",
        existing_type=sa.DateTime(timezone=True),
        type_=sa.DateTime(timezone=False),
        existing_nullable=False,
        postgresql_using="scheduled_at AT TIME ZONE 'Asia/Kolkata'",
    )
