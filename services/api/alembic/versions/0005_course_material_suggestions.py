"""released course materials for grounded suggestions

Revision ID: 0005_course_material_suggestions
Revises: 0004_course_creator_permission
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
revision = "0005_course_material_suggestions"; down_revision = "0004_course_creator_permission"; branch_labels = None; depends_on = None
def upgrade():
    op.create_table("course_materials", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("course_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("courses.id", ondelete="CASCADE"), nullable=False), sa.Column("title", sa.String(240), nullable=False), sa.Column("material_type", sa.String(50), nullable=False), sa.Column("extracted_text", sa.Text(), nullable=False), sa.Column("student_visible", sa.Boolean(), nullable=False, server_default=sa.false()), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")))
    op.create_index("ix_course_materials_course_id", "course_materials", ["course_id"]); op.create_index("ix_material_course_visible", "course_materials", ["course_id", "student_visible"])
def downgrade(): op.drop_table("course_materials")
