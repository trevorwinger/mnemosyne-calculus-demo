"""course exercises and attempts

Revision ID: 0011_exercises_attempts
Revises: 0010_private_ingestion_metadata
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0011_exercises_attempts"
down_revision = "0010_private_ingestion_metadata"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table("exercises", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("course_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("courses.id", ondelete="CASCADE"), nullable=False), sa.Column("concept_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("concepts.id", ondelete="SET NULL"), nullable=True), sa.Column("title", sa.String(240), nullable=False), sa.Column("prompt", sa.Text(), nullable=False), sa.Column("exercise_type", sa.String(50), nullable=False, server_default="practice"), sa.Column("student_visible", sa.Boolean(), nullable=False, server_default=sa.true()), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")))
    op.create_index("ix_exercise_course_visible", "exercises", ["course_id", "student_visible"])
    op.create_table("exercise_attempts", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("exercise_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("exercises.id", ondelete="CASCADE"), nullable=False), sa.Column("student_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False), sa.Column("session_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tutoring_sessions.id", ondelete="SET NULL"), nullable=True), sa.Column("response", sa.Text(), nullable=False), sa.Column("self_assessment", sa.String(40), nullable=True), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")))
    op.create_index("ix_attempt_exercise_student", "exercise_attempts", ["exercise_id", "student_id", "created_at"])

def downgrade():
    op.drop_table("exercise_attempts")
    op.drop_table("exercises")
