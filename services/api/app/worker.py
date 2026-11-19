"""PostgreSQL-backed job worker with leases and idempotent evidence writes."""
import time
from datetime import datetime, timedelta, timezone
from uuid import UUID
from sqlalchemy import select
from .db import SessionLocal
from .config import settings
from .ingestion import chunk_extracted_text, extract_upload, safe_storage_path
from .models import BackgroundJob, ChatMessage, Concept, ConceptSummary, Course, CourseMaterial, ExerciseAttempt, LearningEvent, MaterialChunk, TutoringSession, User
from .retention import learning_evidence_retention_days
from .student_skills import write_student_skill_profile

def claim(db):
    job = db.scalar(select(BackgroundJob).where(BackgroundJob.status.in_(("pending", "retry")), BackgroundJob.available_at <= datetime.now(timezone.utc)).with_for_update(skip_locked=True).limit(1))
    if job: job.status, job.attempts, job.lease_until = "processing", job.attempts + 1, datetime.now(timezone.utc) + timedelta(seconds=30); db.commit()
    return job

def queue_student_skill_profile(db, student_id, course_id, source_key):
    """Coalesce a profile update for one observed learning event."""
    key = f"student-skill-profile:{source_key}"[:200]
    if not db.scalar(select(BackgroundJob.id).where(BackgroundJob.idempotency_key == key)):
        db.add(BackgroundJob(kind="refresh_student_skill_profile", payload={"student_id": str(student_id), "course_id": str(course_id)}, idempotency_key=key))

def process(db, job):
    if job.kind == "prune_learning_evidence":
        course = db.get(Course, UUID(job.payload["course_id"]))
        if not course: return
        try: days = learning_evidence_retention_days(course.tutoring_preferences or {})
        except ValueError: return
        if days is None: return
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        expired = db.query(LearningEvent).filter(LearningEvent.course_id == course.id, LearningEvent.created_at < cutoff).all()
        affected = {(event.student_id, event.concept_id) for event in expired}
        for event in expired: db.delete(event)
        # Rebuild the materialized progress summaries from evidence that remains.
        for student_id, concept_id in affected:
            events = db.query(LearningEvent).filter(LearningEvent.student_id == student_id, LearningEvent.course_id == course.id, LearningEvent.concept_id == concept_id, LearningEvent.forgotten_at.is_(None), LearningEvent.created_at >= cutoff).all()
            summary = db.query(ConceptSummary).filter_by(student_id=student_id, course_id=course.id, concept_id=concept_id).one_or_none()
            if not events:
                if summary: db.delete(summary)
                queue_student_skill_profile(db, student_id, course.id, f"retention:{course.id}:{student_id}:{cutoff.date().isoformat()}")
                continue
            status = "Demonstrated independently" if any(event.independence == "independent" and event.result == "success" for event in events) else "Needs practice" if any(event.result == "needs_practice" for event in events) else "Practicing"
            if summary: summary.status, summary.recent_evidence_count, summary.version = status, len(events), summary.version + 1
            else: db.add(ConceptSummary(student_id=student_id, course_id=course.id, concept_id=concept_id, status=status, recent_evidence_count=len(events)))
            queue_student_skill_profile(db, student_id, course.id, f"retention:{course.id}:{student_id}:{cutoff.date().isoformat()}")
        return
    if job.kind == "refresh_student_skill_profile":
        student_id, course_id = UUID(job.payload["student_id"]), UUID(job.payload["course_id"])
        course, student = db.get(Course, course_id), db.get(User, student_id)
        if not course or not student: return
        observations = db.query(Concept.name, LearningEvent).join(Concept, Concept.id == LearningEvent.concept_id).filter(LearningEvent.student_id == student.id, LearningEvent.course_id == course.id, LearningEvent.forgotten_at.is_(None)).order_by(LearningEvent.created_at.desc()).all()
        # The profile job receives the student's entire course conversation,
        # not merely the latest evidence event. It still exports only safe,
        # synthesized teaching moves back into a future model prompt.
        chat_messages = db.query(ChatMessage).join(TutoringSession, TutoringSession.id == ChatMessage.session_id).filter(TutoringSession.user_id == student.id, TutoringSession.course_id == course.id).order_by(TutoringSession.created_at, ChatMessage.sequence).all()
        write_student_skill_profile(course, student.id, observations, chat_messages)
        return
    if job.kind == "ingest_material":
        material = db.get(CourseMaterial, UUID(job.payload["material_id"]))
        if not material or material.processing_status == "ready": return
        material.processing_status, material.extraction_error = "extracting", None
        try:
            if not material.storage_key or not material.original_filename: raise ValueError("The original private upload is unavailable.")
            path = safe_storage_path(settings.upload_dir, material.storage_key)
            if not path.is_file(): raise ValueError("The original private upload is unavailable.")
            extracted = extract_upload(material.original_filename, path.read_bytes())
            if not extracted.strip(): raise ValueError("No extractable text was found. Review the original or use OCR for scanned documents.")
            material.extracted_text, material.processing_status = extracted, "ready"
            db.query(MaterialChunk).filter_by(material_id=material.id).delete()
            for ordinal, (location_label, content) in enumerate(chunk_extracted_text(extracted)):
                db.add(MaterialChunk(material_id=material.id, ordinal=ordinal, content=content, location_label=location_label))
        except Exception as error:
            material.processing_status, material.extraction_error = "failed", str(error)[:1000]
        return
    if job.kind == "derive_attempt_event":
        payload = job.payload; attempt = db.get(ExerciseAttempt, UUID(payload["attempt_id"])); concept = db.get(Concept, UUID(payload["concept_id"]))
        if not attempt or not concept: return
        result = attempt.self_assessment or "needs_practice"
        existing = db.query(LearningEvent).filter(LearningEvent.details["attempt_id"].astext == str(attempt.id)).first()
        if existing: return
        event = LearningEvent(student_id=attempt.student_id, course_id=UUID(payload["course_id"]), concept_id=concept.id, observed_behavior="Submitted a practice activity attempt.", result=result, hint_count=0, independence="not_assessed", evidence_type="student_self_report", details={"attempt_id": str(attempt.id)})
        db.add(event); summary = db.scalar(select(ConceptSummary).where(ConceptSummary.student_id == event.student_id, ConceptSummary.course_id == event.course_id, ConceptSummary.concept_id == event.concept_id).with_for_update())
        status = "Practicing" if result == "success" else "Needs practice"
        if not summary: db.add(ConceptSummary(student_id=event.student_id, course_id=event.course_id, concept_id=event.concept_id, status=status, recent_evidence_count=1))
        else: summary.status, summary.recent_evidence_count, summary.version = status, summary.recent_evidence_count + 1, summary.version + 1
        queue_student_skill_profile(db, event.student_id, event.course_id, f"attempt:{attempt.id}")
        return
    if job.kind not in {"derive_array_boundary_event", "derive_learning_event"}: return
    payload = job.payload; message = db.get(ChatMessage, UUID(payload["message_id"])); concept = db.scalar(select(Concept).where(Concept.course_id == UUID(payload["course_id"]), Concept.slug == payload.get("concept_slug", "array-boundaries")))
    if not message or not concept or db.scalar(select(LearningEvent).where(LearningEvent.source_message_id == message.id)): return
    event = LearningEvent(student_id=UUID(payload["student_id"]), course_id=UUID(payload["course_id"]), concept_id=concept.id, source_message_id=message.id, observed_behavior=payload.get("observed_behavior", "Used an inclusive array-length boundary in a loop."), result=payload.get("result", "needs_practice"), hint_count=payload.get("hint_count", 0), independence=payload.get("independence", "not_assessed"), evidence_type="tutor_inference", details={"pattern": payload.get("concept_slug", "array-boundaries")})
    db.add(event); summary = db.scalar(select(ConceptSummary).where(ConceptSummary.student_id == event.student_id, ConceptSummary.course_id == event.course_id, ConceptSummary.concept_id == event.concept_id).with_for_update())
    status = "Demonstrated independently" if event.independence == "independent" and event.result == "success" else "Practicing" if event.result == "success" else "Needs practice"
    if not summary: summary = ConceptSummary(student_id=event.student_id, course_id=event.course_id, concept_id=event.concept_id, status=status, recent_evidence_count=1); db.add(summary)
    else: summary.status, summary.recent_evidence_count, summary.version = status, summary.recent_evidence_count + 1, summary.version + 1
    queue_student_skill_profile(db, event.student_id, event.course_id, f"message:{message.id}")
def run_once():
    db = SessionLocal()
    try:
        job = claim(db)
        if not job: return False
        try: process(db, job); job.status, job.lease_until = "completed", None; db.commit()
        except Exception as error: db.rollback(); job = db.get(BackgroundJob, job.id); job.status, job.last_error, job.available_at = ("retry" if job.attempts < 3 else "failed"), str(error)[:1000], datetime.now(timezone.utc) + timedelta(seconds=15); db.commit()
        return True
    finally: db.close()
if __name__ == "__main__":
    while True:
        if not run_once(): time.sleep(1)
