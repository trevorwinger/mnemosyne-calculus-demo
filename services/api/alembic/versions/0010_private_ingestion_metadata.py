"""private ingestion metadata

Revision ID: 0010_private_ingestion_metadata
Revises: 0009_material_release_schedule
"""
from alembic import op
import sqlalchemy as sa

revision = "0010_private_ingestion_metadata"
down_revision = "0009_material_release_schedule"
branch_labels = None
depends_on = None

def upgrade():
    op.add_column("course_materials", sa.Column("original_filename", sa.String(300), nullable=True))
    op.add_column("course_materials", sa.Column("storage_key", sa.String(300), nullable=True))
    op.add_column("course_materials", sa.Column("mime_type", sa.String(160), nullable=True))
    op.add_column("course_materials", sa.Column("extraction_error", sa.Text(), nullable=True))
    op.create_index("ix_material_storage_key", "course_materials", ["storage_key"], unique=True)

def downgrade():
    op.drop_index("ix_material_storage_key", table_name="course_materials")
    op.drop_column("course_materials", "extraction_error")
    op.drop_column("course_materials", "mime_type")
    op.drop_column("course_materials", "storage_key")
    op.drop_column("course_materials", "original_filename")
