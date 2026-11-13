"""material review and module fields
Revision ID: 0006_material_review_fields
Revises: 0005_course_material_suggestions
"""
from alembic import op
import sqlalchemy as sa
revision="0006_material_review_fields"; down_revision="0005_course_material_suggestions"; branch_labels=None; depends_on=None
def upgrade():
    op.add_column("course_materials", sa.Column("module", sa.String(120), nullable=True))
    op.add_column("course_materials", sa.Column("processing_status", sa.String(30), nullable=False, server_default="ready"))
def downgrade():
    op.drop_column("course_materials", "processing_status"); op.drop_column("course_materials", "module")
