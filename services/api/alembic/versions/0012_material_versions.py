"""versioned course materials

Revision ID: 0012_material_versions
Revises: 0011_exercises_attempts
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0012_material_versions"
down_revision = "0011_exercises_attempts"
branch_labels = None
depends_on = None

def upgrade():
    op.add_column("course_materials", sa.Column("version", sa.Integer(), nullable=False, server_default="1"))
    op.add_column("course_materials", sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.add_column("course_materials", sa.Column("replaces_material_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("course_materials.id", ondelete="SET NULL"), nullable=True))
    op.create_index("ix_material_course_active", "course_materials", ["course_id", "active"])

def downgrade():
    op.drop_index("ix_material_course_active", table_name="course_materials")
    op.drop_column("course_materials", "replaces_material_id")
    op.drop_column("course_materials", "active")
    op.drop_column("course_materials", "version")
