"""Seed the student-only APEX Calculus prototype without committing the textbook."""
import shutil
from pathlib import Path

from sqlalchemy import select

from .apex_preprocess import ATTRIBUTION, extract_calc_i_sources
from .config import settings
from .db import SessionLocal
from .ingestion import chunk_extracted_text, safe_storage_path
from .models import Concept, Course, CourseMaterial, CourseStatus, Exercise, MaterialChunk, Membership, Role, User


# Original, compact learning cards keep the shareable demo usable without
# redistributing the textbook. If a lawful local APEX PDF is supplied, the
# real selected sections below replace these cards during the next seed.
DEMO_CALC_I_CARDS = (
    ("1.1", "An Introduction To Limits", "Chapter 1 · Limits", "A limit describes the value a function approaches as x approaches a target. Use a table, graph, or algebraic simplification to test the left- and right-hand behavior. Practice pattern: factor (x^2-a^2)/(x-a), cancel only away from x=a, then evaluate the simplified expression."),
    ("1.3", "Finding Limits Analytically", "Chapter 1 · Limits", "For direct substitution, first check whether the expression is defined. An indeterminate 0/0 form calls for algebra such as factoring, rationalizing, or combining fractions before substitution. State the simplified expression and the resulting limit separately."),
    ("1.4", "One-Sided Limits", "Chapter 1 · Limits", "The left-hand limit uses inputs smaller than a; the right-hand limit uses inputs larger than a. A two-sided limit exists only when both one-sided limits exist and agree. Piecewise definitions are a useful setting for comparing the two sides."),
    ("1.5", "Continuity", "Chapter 1 · Limits", "A function is continuous at a when f(a) is defined, lim x→a f(x) exists, and those two values agree. Classify a discontinuity before proposing a repair: removable holes differ from jumps and infinite discontinuities."),
    ("2.1", "Instantaneous Rates of Change: The Derivative", "Chapter 2 · Derivatives", "The derivative is the instantaneous rate of change. Its definition at a is lim h→0 [f(a+h)-f(a)]/h. Begin definition problems by forming the difference quotient carefully, simplify, and take the limit only after cancelling h when appropriate."),
    ("2.3", "Basic Differentiation Rules", "Chapter 2 · Derivatives", "Use the constant, power, sum, and constant-multiple rules. For x^n, the derivative is n x^(n-1). Identify each term first; then differentiate term by term and simplify only at the end."),
    ("2.4", "The Product and Quotient Rules", "Chapter 2 · Derivatives", "For a product uv, (uv)' = u'v + uv'. For a quotient u/v, (u/v)' = (u'v - uv')/v^2. Label u and v before differentiating; this prevents accidentally differentiating only one factor."),
    ("2.5", "The Chain Rule", "Chapter 2 · Derivatives", "For a composite f(g(x)), differentiate the outside function while keeping the inside, then multiply by the derivative of the inside. Example structure: for (3x-1)^5, use outer power rule and inner derivative 3."),
    ("2.6", "Implicit Differentiation", "Chapter 2 · Derivatives", "When y is defined implicitly, differentiate every term with respect to x. Any derivative of y-dependent expression needs dy/dx by the chain rule. Collect dy/dx terms and solve algebraically at the end."),
    ("3.1", "Extreme Values", "Chapter 3 · Using Derivatives", "Absolute extrema on a closed interval occur at critical numbers in the interval or at endpoints. Find f', identify critical numbers, evaluate f at all candidates, and compare function values rather than derivative values."),
    ("3.2", "The Mean Value Theorem", "Chapter 3 · Using Derivatives", "If f is continuous on [a,b] and differentiable on (a,b), some c satisfies f'(c) = [f(b)-f(a)]/(b-a). Check the hypotheses first, calculate the average rate, then solve the derivative equation for c."),
    ("3.3", "Increasing and Decreasing Functions", "Chapter 3 · Using Derivatives", "A positive derivative means f is increasing; a negative derivative means f is decreasing. Use a sign chart organized around critical numbers and points where f' is undefined, then report intervals with correct notation."),
    ("3.4", "Concavity and the Second Derivative", "Chapter 3 · Using Derivatives", "Positive f'' indicates concave up and negative f'' indicates concave down. A possible inflection point requires a change in concavity, not merely f''=0. Use a second-derivative sign chart to justify conclusions."),
    ("4.2", "Related Rates", "Chapter 4 · Derivative Applications", "Write an equation relating the changing quantities, differentiate with respect to time, then substitute numerical values only after differentiating. Include units and identify which quantities are rates such as dr/dt or dV/dt."),
    ("4.3", "Optimization", "Chapter 4 · Derivative Applications", "Define an objective function in one variable using the constraint. Identify a realistic domain, find critical points and endpoints, compare objective values, and state the optimal quantity with units and a sentence interpreting the result."),
)


def get_user(db, email, name):
    user = db.scalar(select(User).where(User.email == email))
    if not user:
        user = User(email=email, display_name=name, can_create_courses=False)
        db.add(user); db.flush()
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
    records = extract_calc_i_sources(source)
    if not records:
        for section, title, module, text in DEMO_CALC_I_CARDS:
            add_material(db, course, f"Calculus learning card §{section} — {title}", module, f"Mnemosyne original demo learning card · Section {section}: {title}\n\n{text}\n\nFor full textbook-grounded sources, add a lawfully obtained APEX PDF as .local-content/apex-novideo.pdf and rerun `docker compose exec -T api python -m app.seed`.")
        return False
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
        course = db.scalar(select(Course).where(Course.course_code == "MATH-240", Course.owner_id == curator.id))
        if not course:
            course = Course(owner_id=curator.id, title="Calculus I · APEX Prototype", course_code="MATH-240", term="Prototype", description="A student-only calculus tutoring prototype grounded in selected APEX Calculus sections and worked examples.", learning_objectives=["Reason about limits and continuity", "Use derivative rules, including product, quotient, and chain rules", "Apply derivatives to analyze functions and model rates of change"], tutoring_preferences={"standard_tutor_model": settings.prototype_default_model, "instructional_mode": "guided-practice"}, status=CourseStatus.published)
            db.add(course); db.flush()
        elif course.tutoring_preferences.get("standard_tutor_model") == "demo-tutor" and settings.prototype_default_model != "demo-tutor":
            course.tutoring_preferences = {**course.tutoring_preferences, "standard_tutor_model": settings.prototype_default_model}
        if not db.scalar(select(Membership).where(Membership.user_id == prototype_student.id, Membership.course_id == course.id)):
            db.add(Membership(user_id=prototype_student.id, course_id=course.id, role=Role.student))
        concepts = (("Limits", "limits"), ("Continuity", "continuity"), ("Derivative rules", "derivative-rules"), ("Product and quotient rules", "product-quotient-rules"), ("Chain rule", "chain-rule"), ("Derivative applications", "derivative-applications"), ("Related rates", "related-rates"), ("Optimization", "optimization"))
        for name, slug in concepts:
            if not db.scalar(select(Concept).where(Concept.course_id == course.id, Concept.slug == slug)):
                db.add(Concept(course_id=course.id, name=name, slug=slug))
        source_loaded = seed_apex_sources(db, course)
        chain_rule = db.scalar(select(Concept).where(Concept.course_id == course.id, Concept.slug == "chain-rule"))
        title = "Practice: choose a derivative rule"
        if not db.scalar(select(Exercise).where(Exercise.course_id == course.id, Exercise.title == title)):
            db.add(Exercise(course_id=course.id, concept_id=chain_rule.id, title=title, prompt="For f(x) = x e^{-x}, identify the derivative rule or rules you would apply first. Explain your choice in one or two sentences; do not calculate the full derivative yet.", exercise_type="practice", student_visible=True))
        db.commit()
        print(f"Student prototype seeded: {course.course_code}. APEX preprocessing {'completed' if source_loaded else 'is waiting for .local-content/apex-novideo.pdf'}.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
