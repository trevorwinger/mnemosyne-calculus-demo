"""persist the selected model reasoning level per tutoring session

Revision ID: 0015_session_reasoning_level
Revises: 0014_chat_message_sequence
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0015_session_reasoning_level"
down_revision = "0014_chat_message_sequence"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("tutoring_sessions", sa.Column("reasoning_level", postgresql.JSONB(), nullable=False, server_default=sa.text("'false'::jsonb")))
    op.alter_column("tutoring_sessions", "reasoning_level", server_default=None)


def downgrade():
    op.drop_column("tutoring_sessions", "reasoning_level")
