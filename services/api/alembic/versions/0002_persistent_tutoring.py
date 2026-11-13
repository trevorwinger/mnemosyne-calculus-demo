"""persistent tutoring sessions, messages and model runs

Revision ID: 0002_persistent_tutoring
Revises: 0001_core_identity_courses
Create Date: 2026-11-11
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0002_persistent_tutoring"
down_revision = "0001_core_identity_courses"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table("tutoring_sessions", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("course_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("courses.id", ondelete="CASCADE"), nullable=False), sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False), sa.Column("title", sa.String(240), nullable=False, server_default="New tutoring session"), sa.Column("model_name", sa.String(180), nullable=False, server_default="demo-tutor"), sa.Column("memory_enabled", sa.Boolean(), nullable=False, server_default=sa.true()), sa.Column("material_scope", postgresql.JSONB(), nullable=False, server_default="{}"), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")))
    op.create_index("ix_tutoring_sessions_course_id", "tutoring_sessions", ["course_id"]); op.create_index("ix_tutoring_sessions_user_id", "tutoring_sessions", ["user_id"]); op.create_index("ix_session_course_user_updated", "tutoring_sessions", ["course_id", "user_id", "updated_at"])
    op.create_table("chat_messages", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("session_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tutoring_sessions.id", ondelete="CASCADE"), nullable=False), sa.Column("role", sa.String(20), nullable=False), sa.Column("content", sa.Text(), nullable=False), sa.Column("metadata", postgresql.JSONB(), nullable=False, server_default="{}"), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")))
    op.create_index("ix_chat_messages_session_id", "chat_messages", ["session_id"]); op.create_index("ix_message_session_created", "chat_messages", ["session_id", "created_at"])
    op.create_table("model_runs", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("session_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tutoring_sessions.id", ondelete="CASCADE"), nullable=False), sa.Column("request_message_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("chat_messages.id", ondelete="RESTRICT"), nullable=False), sa.Column("response_message_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("chat_messages.id", ondelete="SET NULL")), sa.Column("provider", sa.String(40), nullable=False), sa.Column("model_identifier", sa.String(180), nullable=False), sa.Column("model_digest", sa.String(128)), sa.Column("harness_version", sa.String(40), nullable=False), sa.Column("latency_ms", sa.Integer()), sa.Column("input_tokens", sa.Integer()), sa.Column("output_tokens", sa.Integer()), sa.Column("status", sa.String(30), nullable=False, server_default="completed"), sa.Column("metadata", postgresql.JSONB(), nullable=False, server_default="{}"), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")))
    op.create_index("ix_model_runs_session_id", "model_runs", ["session_id"]); op.create_index("ix_model_run_session", "model_runs", ["session_id", "created_at"])

def downgrade():
    op.drop_table("model_runs"); op.drop_table("chat_messages"); op.drop_table("tutoring_sessions")
