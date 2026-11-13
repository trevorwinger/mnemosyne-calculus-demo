"""core identity and course memberships

Revision ID: 0001_core_identity_courses
Revises:
Create Date: 2026-11-11
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_core_identity_courses"
down_revision = None
branch_labels = None
depends_on = None

# Named PostgreSQL types are created explicitly below.  The column instances
# must not attempt a second CREATE TYPE when their tables are created.
role = postgresql.ENUM("instructor", "student", name="role", create_type=False)
course_status = postgresql.ENUM("draft", "published", "archived", name="coursestatus", create_type=False)

def upgrade():
    postgresql.ENUM("instructor", "student", name="role").create(op.get_bind(), checkfirst=True)
    postgresql.ENUM("draft", "published", "archived", name="coursestatus").create(op.get_bind(), checkfirst=True)
    op.create_table("users", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("email", sa.String(320), nullable=False), sa.Column("display_name", sa.String(120), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False), sa.UniqueConstraint("email"))
    op.create_index("ix_users_email", "users", ["email"])
    op.create_table("courses", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("owner_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False), sa.Column("title", sa.String(180), nullable=False), sa.Column("course_code", sa.String(60)), sa.Column("description", sa.Text(), nullable=False, server_default=""), sa.Column("term", sa.String(80)), sa.Column("learning_objectives", postgresql.JSONB(), nullable=False, server_default="[]"), sa.Column("tutoring_preferences", postgresql.JSONB(), nullable=False, server_default="{}"), sa.Column("status", course_status, nullable=False, server_default="draft"), sa.Column("allow_without_sources", sa.Boolean(), nullable=False, server_default=sa.false()), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False))
    op.create_index("ix_courses_owner_id", "courses", ["owner_id"])
    op.create_table("memberships", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False), sa.Column("course_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("courses.id", ondelete="CASCADE"), nullable=False), sa.Column("role", role, nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False), sa.UniqueConstraint("user_id", "course_id", name="uq_membership_user_course"))
    op.create_index("ix_memberships_user_id", "memberships", ["user_id"]); op.create_index("ix_memberships_course_id", "memberships", ["course_id"]); op.create_index("ix_membership_course_role", "memberships", ["course_id", "role"])
    op.create_table("enrollments", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("course_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("courses.id", ondelete="CASCADE"), nullable=False), sa.Column("code_hash", sa.String(128), nullable=False), sa.Column("expires_at", sa.DateTime(timezone=True)), sa.Column("revoked_at", sa.DateTime(timezone=True)), sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False), sa.UniqueConstraint("code_hash"))
    op.create_index("ix_enrollments_course_id", "enrollments", ["course_id"]); op.create_index("ix_enrollments_code_hash", "enrollments", ["code_hash"])

def downgrade():
    op.drop_table("enrollments"); op.drop_table("memberships"); op.drop_table("courses"); op.drop_table("users")
    course_status.drop(op.get_bind(), checkfirst=True); role.drop(op.get_bind(), checkfirst=True)
