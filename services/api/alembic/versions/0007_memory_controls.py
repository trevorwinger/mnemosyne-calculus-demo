"""student memory forgetting and reset controls
Revision ID: 0007_memory_controls
Revises: 0006_material_review_fields
"""
from alembic import op
import sqlalchemy as sa
revision="0007_memory_controls"; down_revision="0006_material_review_fields"; branch_labels=None; depends_on=None
def upgrade():
    op.add_column("memberships", sa.Column("memory_reset_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("learning_events", sa.Column("forgotten_at", sa.DateTime(timezone=True), nullable=True))
def downgrade():
    op.drop_column("learning_events", "forgotten_at"); op.drop_column("memberships", "memory_reset_at")
