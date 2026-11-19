from datetime import datetime
from typing import Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictStr

class IdentityOut(BaseModel):
    id: UUID
    email: str
    display_name: str
    can_create_courses: bool

class CourseCreate(BaseModel):
    title: str = Field(min_length=2, max_length=180)
    course_code: str | None = Field(default=None, max_length=60)
    description: str = Field(default="", max_length=5000)
    term: str | None = Field(default=None, max_length=80)
    learning_objectives: list[str] = Field(default_factory=list, max_length=12)
    tutoring_preferences: dict = Field(default_factory=dict)

class CourseOut(BaseModel):
    id: UUID
    title: str
    course_code: str | None
    description: str
    term: str | None
    status: str
    allow_without_sources: bool
    role: str | None = None
    model_config = {"from_attributes": True}

class CourseSettingsOut(CourseOut):
    learning_objectives: list[str]
    tutoring_preferences: dict

class CourseSettingsUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str | None = Field(default=None, min_length=2, max_length=180)
    course_code: str | None = Field(default=None, max_length=60)
    description: str | None = Field(default=None, max_length=5000)
    term: str | None = Field(default=None, max_length=80)
    learning_objectives: list[str] | None = Field(default=None, max_length=12)
    tutoring_preferences: dict | None = None

class EnrollmentCreate(BaseModel):
    expires_at: datetime | None = None

class PublishCourse(BaseModel):
    acknowledge_without_sources: bool = False

class EnrollmentOut(BaseModel):
    code: str
    course_id: UUID
    expires_at: datetime | None

class EnrollmentStatusOut(BaseModel):
    id: UUID
    expires_at: datetime | None
    revoked_at: datetime | None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class RosterMember(BaseModel):
    id: UUID
    display_name: str
    email: str
    role: str
    joined_at: datetime

class JoinRequest(BaseModel):
    code: str = Field(min_length=6, max_length=128)

class JoinPreview(BaseModel):
    title: str
    course_code: str | None
    description: str
    enrollment_open: bool

class ModelOut(BaseModel):
    name: str
    digest: str | None
    size: int | None
    parameter_size: str | None
    quantization: str | None
    provider: str
    approved: bool
    reason: str | None
    thinking_values: list[StrictBool | StrictStr] = Field(default_factory=list)
    thinking_default: StrictBool | StrictStr | None = None

class ModelProviderStatus(BaseModel):
    reachable: bool
    approved_model_count: int
    detail: str

class IngestionCapabilities(BaseModel):
    max_upload_mb: int
    extensions: list[str]

class QueueStatus(BaseModel):
    kind: str
    status: str
    count: int
    oldest_created_at: datetime

class CourseSuggestion(BaseModel):
    prompt: str
    basis: str
    material_title: str

class ConceptOut(BaseModel):
    id: UUID
    name: str
    slug: str
    model_config = ConfigDict(from_attributes=True)

class ConceptCreate(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    slug: str | None = Field(default=None, min_length=2, max_length=120)

class ExerciseCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(min_length=2, max_length=240)
    prompt: str = Field(min_length=2, max_length=12000)
    concept_id: UUID | None = None
    exercise_type: Literal["practice", "java", "python", "javascript", "c", "cpp"] = "practice"
    expected_answer: str | None = Field(default=None, max_length=12000)
    student_visible: bool = True

class ExerciseUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str | None = Field(default=None, min_length=2, max_length=240)
    prompt: str | None = Field(default=None, min_length=2, max_length=12000)
    concept_id: UUID | None = None
    exercise_type: Literal["practice", "java", "python", "javascript", "c", "cpp"] | None = None
    expected_answer: str | None = Field(default=None, max_length=12000)
    student_visible: bool | None = None

class CodeRunRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    language: Literal["java", "python", "javascript", "c", "cpp"]
    source: str = Field(min_length=1, max_length=20_000)
    stdin: str = Field(default="", max_length=4_000)

class CodeRunOut(BaseModel):
    status: str
    stdout: str
    stderr: str
    elapsed_ms: int = Field(ge=0)

class ExerciseOut(BaseModel):
    id: UUID
    course_id: UUID
    concept_id: UUID | None
    title: str
    prompt: str
    exercise_type: str
    automatic_check_configured: bool
    student_visible: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class AttemptCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    response: str = Field(min_length=1, max_length=12000)
    self_assessment: str | None = Field(default=None, pattern="^(needs_practice|success)$")
    session_id: UUID | None = None

class AttemptOut(BaseModel):
    id: UUID
    exercise_id: UUID
    response: str
    self_assessment: str | None
    evaluation_status: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ProgressItem(BaseModel):
    concept: str
    status: str
    recent_evidence_count: int

class InstructorConceptProgress(BaseModel):
    concept: str
    students_with_evidence: int
    hint_assisted_successes: int
    independent_successes: int

class InstructorStudentEvidence(BaseModel):
    student_name: str
    concept: str
    observed_behavior: str
    result: str
    hint_count: int
    independence: str
    created_at: datetime

class MemoryObservation(BaseModel):
    id: UUID
    concept: str
    observed_behavior: str
    result: str
    independence: str
    evidence_type: str
    created_at: datetime
    source_session_id: UUID | None = None

class MemoryCorrection(BaseModel):
    model_config = ConfigDict(extra="forbid")
    observed_behavior: str | None = Field(default=None, min_length=2, max_length=2000)
    result: str | None = Field(default=None, pattern="^(needs_practice|success)$")
    independence: str | None = Field(default=None, pattern="^(not_assessed|hint_assisted|independent)$")

class MaterialOut(BaseModel):
    id: UUID
    title: str
    material_type: str
    module: str | None
    student_visible: bool
    processing_status: str
    release_at: datetime | None
    original_filename: str | None
    extraction_error: str | None
    extracted_text: str
    version: int
    active: bool
    replaces_material_id: UUID | None
    model_config = ConfigDict(from_attributes=True)

class StudentMaterialOut(BaseModel):
    id: UUID
    title: str
    material_type: str
    module: str | None
    preview: str

class MaterialCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(min_length=2, max_length=240)
    material_type: str = Field(default="lecture", max_length=50)
    module: str | None = Field(default=None, max_length=120)
    extracted_text: str = Field(min_length=1, max_length=100000)
    student_visible: bool = False
    release_at: datetime | None = None
    replaces_material_id: UUID | None = None

class MaterialUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str | None = Field(default=None, min_length=2, max_length=240)
    material_type: str | None = Field(default=None, max_length=50)
    module: str | None = Field(default=None, max_length=120)
    extracted_text: str | None = Field(default=None, min_length=1, max_length=100000)
    student_visible: bool | None = None
    release_at: datetime | None = None

class SessionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str | None = Field(default=None, max_length=240)
    model_name: str | None = Field(default=None, max_length=180)
    reasoning_level: StrictBool | StrictStr | None = None
    memory_enabled: bool | None = None
    material_ids: list[UUID] | None = None

class SessionOut(BaseModel):
    id: UUID
    course_id: UUID
    title: str
    model_name: str
    reasoning_level: StrictBool | StrictStr
    memory_enabled: bool
    material_scope: dict
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class MessageOut(BaseModel):
    id: UUID
    role: str
    content: str
    created_at: datetime
    citations: list[dict] = Field(default_factory=list)

class SourceExcerpt(BaseModel):
    material_id: UUID
    title: str
    module: str | None
    location: str
    content: str
    previous_location: str | None = None
    previous_content: str | None = None
    next_location: str | None = None
    next_content: str | None = None

class SessionDetail(SessionOut):
    messages: list[MessageOut]

class SessionSettingsUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    model_name: str | None = Field(default=None, max_length=180)
    reasoning_level: StrictBool | StrictStr

class SendMessage(BaseModel):
    model_config = ConfigDict(extra="forbid")
    content: str = Field(min_length=1, max_length=12000)
    model_name: str | None = Field(default=None, max_length=180)
    reasoning_level: StrictBool | StrictStr | None = None
    memory_enabled: bool | None = None
    material_ids: list[UUID] | None = None
