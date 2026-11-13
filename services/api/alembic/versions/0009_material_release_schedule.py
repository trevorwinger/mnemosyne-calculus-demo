"""material release schedule

Revision ID: 0009_material_release_schedule
Revises: 0008_material_chunks
"""
from alembic import op
import sqlalchemy as sa

revision = "0009_material_release_schedule"
down_revision = "0008_material_chunks"
branch_labels = None
depends_on = None

def upgrade():
    op.add_column("course_materials", sa.Column("release_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_material_course_release", "course_materials", ["course_id", "student_visible", "release_at"])

def downgrade():
    op.drop_index("ix_material_course_release", table_name="course_materials")
    op.drop_column("course_materials", "release_at")
