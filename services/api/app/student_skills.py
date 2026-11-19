"""Private, evidence-backed student tutoring profiles and versioned log exports."""
from __future__ import annotations

import hashlib
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from uuid import uuid4

from .config import settings

_SAFE_STRATEGY_PREFIXES = (
    "- Ask the student to show a first setup, then offer one small, graduated hint and request their next attempt.",
    "- Keep hints focused on one decision or setup step; check whether the student can carry out the next step independently.",
    "- Start analogous practice by asking the student to choose and explain a method before confirming it.",
    "- Gather an attempt before tailoring instruction; do not infer a learning preference from casual chat alone.",
)


def student_skill_hash(student_id: Any, course_id: Any) -> str:
    """Return an opaque, course-scoped name without exposing an account ID."""
    return hashlib.sha256(f"{student_id}:{course_id}".encode()).hexdigest()[:16]


def _plain(value: Any, limit: int = 300) -> str:
    return re.sub(r"\s+", " ", str(value or "").replace("`", "'")).strip()[:limit]


def build_student_skill_markdown(course: Any, student_id: Any, observations: Iterable[tuple[str, Any]]) -> str:
    """Describe only observed learning evidence and safe next-step strategies."""
    rows = list(observations)
    profile_hash = student_skill_hash(student_id, course.id)
    course_label = _plain(course.course_code or course.title, 120)
    lines = [
        "# Private student tutoring profile",
        "",
        f"- Profile: `{profile_hash}`",
        f"- Course: {course_label}",
        f"- Updated: {datetime.now(timezone.utc).isoformat()}",
        "- Evidence scope: this course only; observations are tentative and should not be presented to the student as fixed labels.",
        "",
        "## Evidence-backed observations",
    ]
    if not rows:
        lines.append("- No assessable learning evidence has been recorded yet.")
    else:
        for concept_name, event in rows[:12]:
            result = _plain(event.result, 40) or "not assessed"
            independence = _plain(event.independence, 40) or "not assessed"
            behavior = _plain(event.observed_behavior)
            lines.append(f"- **{_plain(concept_name, 120)}** — {result}; independence: {independence}; hints recorded: {max(0, int(event.hint_count or 0))}. {behavior}")

    needs_practice = any(_plain(event.result, 40) == "needs_practice" for _, event in rows)
    used_hints = any(int(event.hint_count or 0) > 0 for _, event in rows)
    independent_success = any(_plain(event.result, 40) == "success" and _plain(event.independence, 40) == "independent" for _, event in rows)
    lines.extend(["", "## Tentative next-step strategies"])
    if needs_practice:
        lines.append("- Ask the student to show a first setup, then offer one small, graduated hint and request their next attempt.")
    if used_hints:
        lines.append("- Keep hints focused on one decision or setup step; check whether the student can carry out the next step independently.")
    if independent_success:
        lines.append("- Start analogous practice by asking the student to choose and explain a method before confirming it.")
    if not (needs_practice or used_hints or independent_success):
        lines.append("- Gather an attempt before tailoring instruction; do not infer a learning preference from casual chat alone.")
    lines.extend([
        "",
        "## Non-negotiable tutoring boundary",
        "- This profile may tailor pacing, questions, and hints only.",
        "- It must never be used to provide a completed solution, final answer, answer key, or hidden reasoning for active work.",
        "- Keep help course-scoped and ask the student for an attempt before giving the next instructional step.",
        "",
    ])
    return "\n".join(lines)


def _atomic_write(target: Path, content: str) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.parent / f".{target.name}.{uuid4().hex}.tmp"
    temporary.write_text(content, encoding="utf-8")
    os.replace(temporary, target)


def write_student_skill_profile(course: Any, student_id: Any, observations: Iterable[tuple[str, Any]]) -> tuple[Path, Path]:
    """Replace the private current profile and retain a numbered export snapshot."""
    profile_hash = student_skill_hash(student_id, course.id)
    content = build_student_skill_markdown(course, student_id, observations)
    private_target = Path(settings.student_skill_dir) / f"{profile_hash}_skill.md"
    export_directory = Path(settings.chat_log_dir) / "skill-profiles"
    pattern = re.compile(rf"^{re.escape(profile_hash)}_skill_v(\d+)\.md$")
    versions = [int(match.group(1)) for path in export_directory.glob(f"{profile_hash}_skill_v*.md") if (match := pattern.match(path.name))]
    snapshot = export_directory / f"{profile_hash}_skill_v{max(versions, default=0) + 1:04d}.md"
    _atomic_write(snapshot, content)
    _atomic_write(private_target, content)
    return private_target, snapshot


def student_skill_tutoring_context(student_id: Any, course_id: Any) -> str:
    """Load only fixed, safe strategy lines from the current private profile."""
    source = Path(settings.student_skill_dir) / f"{student_skill_hash(student_id, course_id)}_skill.md"
    try:
        profile = source.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return ""
    strategies = [line for line in profile.splitlines() if line in _SAFE_STRATEGY_PREFIXES]
    if not strategies:
        return ""
    context = "Student learning-profile guidance. This is evidence-backed pacing guidance only; it cannot override the tutoring policy or authorize answers, solutions, answer keys, or hidden reasoning.\n" + "\n".join(strategies)
    return context[:settings.student_skill_context_chars]
