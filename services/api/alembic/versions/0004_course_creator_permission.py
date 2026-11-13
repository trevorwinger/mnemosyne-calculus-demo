"""explicit course creator permission

Revision ID: 0004_course_creator_permission
Revises: 0003_learning_events_jobs
"""
from alembic import op
import sqlalchemy as sa
revision = "0004_course_creator_permission"; down_revision = "0003_learning_events_jobs"; branch_labels = None; depends_on = None
def upgrade(): op.add_column("users", sa.Column("can_create_courses", sa.Boolean(), nullable=False, server_default=sa.false()))
def downgrade(): op.drop_column("users", "can_create_courses")
