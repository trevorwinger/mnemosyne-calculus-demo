import enum
import uuid
from datetime import datetime
from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .db import Base

class Role(str, enum.Enum):
    instructor = "instructor"
    student = "student"

class CourseStatus(str, enum.Enum):
    draft = "draft"
    published = "published"
    archived = "archived"

class User(Base):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(120))
    can_create_courses: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class Course(Base):
    __tablename__ = "courses"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), index=True)
    title: Mapped[str] = mapped_column(String(180))
    course_code: Mapped[str | None] = mapped_column(String(60), nullable=True)
    description: Mapped[str] = mapped_column(Text, default="")
    term: Mapped[str | None] = mapped_column(String(80), nullable=True)
    learning_objectives: Mapped[list] = mapped_column(JSONB, default=list)
    tutoring_preferences: Mapped[dict] = mapped_column(JSONB, default=dict)
    status: Mapped[CourseStatus] = mapped_column(Enum(CourseStatus), default=CourseStatus.draft)
    allow_without_sources: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class Membership(Base):
    __tablename__ = "memberships"
    __table_args__ = (UniqueConstraint("user_id", "course_id", name="uq_membership_user_course"), Index("ix_membership_course_role", "course_id", "role"))
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    course_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), index=True)
    role: Mapped[Role] = mapped_column(Enum(Role))
    memory_reset_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class Enrollment(Base):
    __tablename__ = "enrollments"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), index=True)
    code_hash: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class TutoringSession(Base):
    __tablename__ = "tutoring_sessions"
    __table_args__ = (Index("ix_session_course_user_updated", "course_id", "user_id", "updated_at"),)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(240), default="New tutoring session")
    model_name: Mapped[str] = mapped_column(String(180), default="demo-tutor")
    reasoning_level: Mapped[bool | str] = mapped_column(JSONB, default=False)
    memory_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    material_scope: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    __table_args__ = (UniqueConstraint("session_id", "sequence", name="uq_message_session_sequence"), Index("ix_message_session_created", "session_id", "created_at"),)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tutoring_sessions.id", ondelete="CASCADE"), index=True)
    sequence: Mapped[int] = mapped_column(Integer)
    role: Mapped[str] = mapped_column(String(20))
    content: Mapped[str] = mapped_column(Text)
    message_metadata: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class ModelRun(Base):
    __tablename__ = "model_runs"
    __table_args__ = (Index("ix_model_run_session", "session_id", "created_at"),)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tutoring_sessions.id", ondelete="CASCADE"), index=True)
    request_message_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("chat_messages.id", ondelete="RESTRICT"))
    response_message_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("chat_messages.id", ondelete="SET NULL"), nullable=True)
    provider: Mapped[str] = mapped_column(String(40))
    model_identifier: Mapped[str] = mapped_column(String(180))
    model_digest: Mapped[str | None] = mapped_column(String(128), nullable=True)
    harness_version: Mapped[str] = mapped_column(String(40))
    latency_ms: Mapped[int | None] = mapped_column(nullable=True)
    input_tokens: Mapped[int | None] = mapped_column(nullable=True)
    output_tokens: Mapped[int | None] = mapped_column(nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="completed")
    run_metadata: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class Concept(Base):
    __tablename__ = "concepts"
    __table_args__ = (UniqueConstraint("course_id", "slug", name="uq_concept_course_slug"),)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(160))
    slug: Mapped[str] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class LearningEvent(Base):
    __tablename__ = "learning_events"
    __table_args__ = (UniqueConstraint("source_message_id", name="uq_event_source_message"), Index("ix_event_student_course_concept", "student_id", "course_id", "concept_id", "created_at"))
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    course_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), index=True)
    concept_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("concepts.id", ondelete="CASCADE"), index=True)
    source_message_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("chat_messages.id", ondelete="SET NULL"), nullable=True)
    observed_behavior: Mapped[str] = mapped_column(Text)
    result: Mapped[str] = mapped_column(String(40))
    hint_count: Mapped[int] = mapped_column(default=0)
    independence: Mapped[str] = mapped_column(String(40), default="not_assessed")
    evidence_type: Mapped[str] = mapped_column(String(40), default="tutor_inference")
    details: Mapped[dict] = mapped_column(JSONB, default=dict)
    forgotten_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class ConceptSummary(Base):
    __tablename__ = "concept_summaries"
    __table_args__ = (UniqueConstraint("student_id", "course_id", "concept_id", name="uq_summary_student_course_concept"),)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    course_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), index=True)
    concept_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("concepts.id", ondelete="CASCADE"), index=True)
    status: Mapped[str] = mapped_column(String(50), default="Not assessed")
    recent_evidence_count: Mapped[int] = mapped_column(default=0)
    version: Mapped[int] = mapped_column(default=1)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class BackgroundJob(Base):
    __tablename__ = "background_jobs"
    __table_args__ = (UniqueConstraint("idempotency_key", name="uq_job_idempotency"), Index("ix_job_claim", "status", "available_at"))
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    kind: Mapped[str] = mapped_column(String(80))
    payload: Mapped[dict] = mapped_column(JSONB, default=dict)
    idempotency_key: Mapped[str] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(30), default="pending")
    attempts: Mapped[int] = mapped_column(default=0)
    available_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    lease_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class CourseMaterial(Base):
    __tablename__ = "course_materials"
    __table_args__ = (Index("ix_material_course_visible", "course_id", "student_visible"), Index("ix_material_course_release", "course_id", "student_visible", "release_at"), Index("ix_material_course_active", "course_id", "active"))
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(240))
    material_type: Mapped[str] = mapped_column(String(50), default="lecture")
    module: Mapped[str | None] = mapped_column(String(120), nullable=True)
    extracted_text: Mapped[str] = mapped_column(Text)
    student_visible: Mapped[bool] = mapped_column(Boolean, default=False)
    processing_status: Mapped[str] = mapped_column(String(30), default="ready")
    release_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    original_filename: Mapped[str | None] = mapped_column(String(300), nullable=True)
    storage_key: Mapped[str | None] = mapped_column(String(300), nullable=True, unique=True)
    mime_type: Mapped[str | None] = mapped_column(String(160), nullable=True)
    extraction_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    replaces_material_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("course_materials.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class MaterialChunk(Base):
    __tablename__ = "material_chunks"
    __table_args__ = (Index("ix_chunk_material", "material_id", "ordinal"),)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    material_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("course_materials.id", ondelete="CASCADE"), index=True)
    ordinal: Mapped[int] = mapped_column()
    content: Mapped[str] = mapped_column(Text)
    location_label: Mapped[str] = mapped_column(String(120), default="Text")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class Exercise(Base):
    __tablename__ = "exercises"
    __table_args__ = (Index("ix_exercise_course_visible", "course_id", "student_visible"),)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), index=True)
    concept_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("concepts.id", ondelete="SET NULL"), nullable=True)
    title: Mapped[str] = mapped_column(String(240))
    prompt: Mapped[str] = mapped_column(Text)
    exercise_type: Mapped[str] = mapped_column(String(50), default="practice")
    expected_answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    student_visible: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    @property
    def automatic_check_configured(self) -> bool:
        return bool(self.expected_answer and self.expected_answer.strip())

class ExerciseAttempt(Base):
    __tablename__ = "exercise_attempts"
    __table_args__ = (Index("ix_attempt_exercise_student", "exercise_id", "student_id", "created_at"),)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    exercise_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("exercises.id", ondelete="CASCADE"), index=True)
    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    session_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("tutoring_sessions.id", ondelete="SET NULL"), nullable=True)
    response: Mapped[str] = mapped_column(Text)
    self_assessment: Mapped[str | None] = mapped_column(String(40), nullable=True)
    evaluation_status: Mapped[str] = mapped_column(String(30), default="not_configured")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
