"""Write shareable, locally stored JSON transcripts for demo sessions."""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from sqlalchemy.orm import Session

from .config import settings
from .models import ChatMessage, Course, TutoringSession, User

logger = logging.getLogger(__name__)


def _timestamp(value: Any) -> str | None:
    return value.isoformat() if value is not None else None


def export_session_transcript(db: Session, session: TutoringSession, course: Course, student: User) -> None:
    """Atomically refresh one ordered transcript without affecting chat delivery."""
    if not settings.chat_logging_enabled:
        return
    try:
        directory = Path(settings.chat_log_dir)
        directory.mkdir(parents=True, exist_ok=True)
        messages = db.query(ChatMessage).filter_by(session_id=session.id).order_by(ChatMessage.sequence).all()
        payload = {
            "schema_version": 1,
            "exported_at": _timestamp(datetime.now(timezone.utc)),
            "session": {
                "id": str(session.id),
                "title": session.title,
                "model_name": session.model_name,
                "memory_enabled": session.memory_enabled,
                "material_scope": session.material_scope or {},
                "created_at": _timestamp(session.created_at),
                "updated_at": _timestamp(session.updated_at),
            },
            "course": {"id": str(course.id), "code": course.course_code, "title": course.title, "term": course.term},
            "student": {"id": str(student.id), "display_name": student.display_name},
            "messages": [
                {
                    "sequence": message.sequence,
                    "id": str(message.id),
                    "role": message.role,
                    "content": message.content,
                    "created_at": _timestamp(message.created_at),
                    "citations": (message.message_metadata or {}).get("citations", []),
                    "metadata": message.message_metadata or {},
                }
                for message in messages
            ],
        }
        target = directory / f"{session.id}.json"
        temporary = directory / f".{session.id}.{uuid4().hex}.tmp"
        temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        os.replace(temporary, target)
    except (OSError, TypeError, ValueError) as error:
        logger.warning("Could not export chat transcript for session %s: %s", session.id, error)
