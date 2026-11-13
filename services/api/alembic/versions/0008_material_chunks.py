"""retrieval chunks for course materials
Revision ID: 0008_material_chunks
Revises: 0007_memory_controls
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
revision="0008_material_chunks"; down_revision="0007_memory_controls"; branch_labels=None; depends_on=None
def upgrade():
    op.create_table("material_chunks", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("material_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("course_materials.id", ondelete="CASCADE"), nullable=False), sa.Column("ordinal", sa.Integer(), nullable=False), sa.Column("content", sa.Text(), nullable=False), sa.Column("location_label", sa.String(120), nullable=False, server_default="Text"), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")))
    op.create_index("ix_material_chunks_material_id", "material_chunks", ["material_id"]); op.create_index("ix_chunk_material", "material_chunks", ["material_id", "ordinal"])
def downgrade(): op.drop_table("material_chunks")
