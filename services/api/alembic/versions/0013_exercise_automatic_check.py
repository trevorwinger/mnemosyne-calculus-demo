"""optional deterministic practice checks

Revision ID: 0013_exercise_automatic_check
Revises: 0012_material_versions
"""
from alembic import op
import sqlalchemy as sa


revision = "0013_exercise_automatic_check"
down_revision = "0012_material_versions"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("exercises", sa.Column("expected_answer", sa.Text(), nullable=True))
    op.add_column("exercise_attempts", sa.Column("evaluation_status", sa.String(length=30), nullable=False, server_default="not_configured"))
    op.alter_column("exercise_attempts", "evaluation_status", server_default=None)


def downgrade():
    op.drop_column("exercise_attempts", "evaluation_status")
    op.drop_column("exercises", "expected_answer")
