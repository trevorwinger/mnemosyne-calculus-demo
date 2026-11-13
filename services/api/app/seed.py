"""Seed the student-only APEX Calculus III prototype."""
import shutil
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from .apex_preprocess import ATTRIBUTION, extract_calc_iii_sources
from .config import settings
from .db import SessionLocal
from .ingestion import chunk_extracted_text, safe_storage_path
from .models import Concept, Course, CourseMaterial, CourseStatus, Exercise, MaterialChunk, Membership, Role, User


# Original, compact learning cards keep the shareable demo usable without
# redistributing the textbook. If a lawful local APEX PDF is supplied, the
# real selected sections below replace these cards during the next seed.
DEMO_CALC_III_CARDS = (
    ("9", "Sequences and Series", "Chapter 9 · Sequences and Series", "Identify the sequence or series type before choosing a convergence test. State the test's hypotheses, then show the quantity that lets you apply it."),
    ("10", "Curves in the Plane", "Chapter 10 · Curves in the Plane", "Use parametric or polar representations to describe a curve. Keep the parameter and its interval visible, and distinguish a curve's geometry from its orientation."),
    ("11", "Vectors", "Chapter 11 · Vectors", "Represent vectors in components. The dot product produces a scalar; the cross product produces a vector orthogonal to both inputs. Use direction and units to check a result."),
    ("12", "Vector-Valued Functions", "Chapter 12 · Vector-Valued Functions", "Differentiate vector-valued functions componentwise. For motion, position, velocity, and acceleration are related by successive derivatives."),
    ("13", "Functions of Several Variables", "Chapter 13 · Functions of Several Variables", "For a multivariable function, partial derivatives hold other variables fixed. Use the gradient, directional derivatives, and a clear domain when analyzing change."),
    ("14", "Multiple Integration", "Chapter 14 · Multiple Integration", "Set bounds that describe the region before evaluating a double or triple integral. State the coordinate system and the geometric quantity being accumulated."),
)


def get_user(db, email, name):
    user = db.scalar(select(User).where(User.email == email))
    if not user:
        candidate = User(email=email, display_name=name, can_create_courses=False)
        try:
            # Bootstrap may be launched twice while Docker finishes starting.
            # A savepoint makes this lookup/create path safe in that race.
            with db.begin_nested():
                db.add(candidate)
                db.flush()
            user = candidate
        except IntegrityError:
            user = db.scalar(select(User).where(User.email == email))
            if not user:
                raise
    return user


def add_material(db, course, title, module, text):
    material = db.scalar(select(CourseMaterial).where(CourseMaterial.course_id == course.id, CourseMaterial.title == title))
    if material:
        material.module, material.extracted_text = module, text
        db.query(MaterialChunk).filter_by(material_id=material.id).delete()
    else:
        material = CourseMaterial(course_id=course.id, title=title, material_type="textbook", module=module, extracted_text=text, student_visible=True, processing_status="ready")
        db.add(material); db.flush()
    for ordinal, (location, content) in enumerate(chunk_extracted_text(text)):
        db.add(MaterialChunk(material_id=material.id, ordinal=ordinal, content=content, location_label=location))
    return material


def seed_apex_sources(db, course):
    source = Path(settings.apex_textbook_path)
    records = extract_calc_iii_sources(source)
    if not records:
        for section, title, module, text in DEMO_CALC_III_CARDS:
            add_material(db, course, f"Calculus learning card §{section} — {title}", module, f"Mnemosyne original demo learning card · Section {section}: {title}\n\n{text}\n\nFor full textbook-grounded sources, add a lawfully obtained APEX PDF as .local-content/apex-novideo.pdf and rerun `docker compose exec -T api python -m app.seed`.")
        return False
    # The bundled textbook replaces the lightweight cards used by the no-PDF
    # demo. Delete their chunks explicitly so re-seeding is idempotent on
    # databases created before the archive was unpacked.
    demo_cards = db.scalars(select(CourseMaterial).where(
        CourseMaterial.course_id == course.id,
        CourseMaterial.title.like("Calculus learning card §%"),
    )).all()
    for material in demo_cards:
        db.query(MaterialChunk).filter_by(material_id=material.id).delete()
        db.delete(material)
    storage_key = "apex-calculus-5e.pdf"
    destination = safe_storage_path(settings.upload_dir, storage_key)
    if not destination.exists():
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
    for record in records:
        add_material(db, course, record["title"], record["module"], record["text"])
    return True


def main():
    db = SessionLocal()
    try:
        curator = get_user(db, "mnemosyne.prototype@demo.local", "Mnemosyne Prototype")
        prototype_student = get_user(db, "prototype.student@demo.local", "Alex · Prototype Student")
        prototype_student.display_name = "Alex · Prototype Student"
        course = db.scalar(select(Course).where(Course.course_code == "MATH 242", Course.owner_id == curator.id))
        if not course:
            course = Course(owner_id=curator.id, title="Calculus and Analytic Geometry III · APEX Prototype", course_code="MATH 242", term="Prototype", description="A student-only Calculus III tutoring prototype grounded in APEX Calculus Chapters 9–14, with worked examples and citable sources.", learning_objectives=["Analyze sequences, series, and Taylor approximations", "Model curves with parametric and polar equations and reason with vectors", "Use multivariable derivatives and multiple integrals to analyze change, area, volume, and geometry"], tutoring_preferences={"standard_tutor_model": settings.prototype_default_model, "instructional_mode": "guided-practice"}, status=CourseStatus.published)
            db.add(course); db.flush()
        elif course.tutoring_preferences.get("standard_tutor_model") == "demo-tutor" and settings.prototype_default_model != "demo-tutor":
            course.tutoring_preferences = {**course.tutoring_preferences, "standard_tutor_model": settings.prototype_default_model}
        if not db.scalar(select(Membership).where(Membership.user_id == prototype_student.id, Membership.course_id == course.id)):
            db.add(Membership(user_id=prototype_student.id, course_id=course.id, role=Role.student))
        concepts = (("Sequences and series", "sequences-series"), ("Parametric and polar curves", "parametric-polar"), ("Vectors and geometry", "vectors-geometry"), ("Vector-valued functions", "vector-valued-functions"), ("Multivariable derivatives", "multivariable-derivatives"), ("Multiple integration", "multiple-integration"))
        for name, slug in concepts:
            if not db.scalar(select(Concept).where(Concept.course_id == course.id, Concept.slug == slug)):
                db.add(Concept(course_id=course.id, name=name, slug=slug))
        source_loaded = seed_apex_sources(db, course)
        vectors = db.scalar(select(Concept).where(Concept.course_id == course.id, Concept.slug == "vectors-geometry"))
        title = "Practice: set up a dot product"
        if not db.scalar(select(Exercise).where(Exercise.course_id == course.id, Exercise.title == title)):
            db.add(Exercise(course_id=course.id, concept_id=vectors.id, title=title, prompt="For u = ⟨2, -1, 3⟩ and v = ⟨1, 4, -2⟩, set up u · v. Identify which matching components you multiply before adding; do not calculate the final value yet.", exercise_type="practice", student_visible=True))
        db.commit()
        print(f"Student prototype seeded: {course.course_code}. APEX preprocessing {'completed' if source_loaded else 'is waiting for .local-content/apex-novideo.pdf'}.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
