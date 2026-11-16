import json
from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

from app.chat_logging import export_session_transcript
from app.config import settings


class _Query:
    def __init__(self, messages):
        self.messages = messages

    def filter_by(self, **_kwargs):
        return self

    def order_by(self, *_args):
        return self

    def all(self):
        return self.messages


class _Database:
    def __init__(self, messages):
        self.messages = messages

    def query(self, _model):
        return _Query(self.messages)


def test_session_transcript_is_ordered_and_timestamped(tmp_path, monkeypatch):
    session_id = uuid4()
    created_at = datetime(2026, 11, 15, 12, 30, tzinfo=timezone.utc)
    messages = [
        SimpleNamespace(id=uuid4(), sequence=1, role="user", content="Help me practice vectors.", created_at=created_at, message_metadata={}),
        SimpleNamespace(id=uuid4(), sequence=2, role="assistant", content="Let's begin with a dot product.", created_at=created_at, message_metadata={"citations": [{"title": "APEX §11.3"}]}),
    ]
    session = SimpleNamespace(id=session_id, title="Vectors", model_name="gemma4:12b", memory_enabled=True, material_scope={"material_ids": None}, created_at=created_at, updated_at=created_at)
    course = SimpleNamespace(id=uuid4(), course_code="MATH 242", title="Calculus III", term="Fall 2026")
    student = SimpleNamespace(id=uuid4(), display_name="Alex")
    monkeypatch.setattr(settings, "chat_log_dir", str(tmp_path))

    export_session_transcript(_Database(messages), session, course, student)

    transcript = json.loads((tmp_path / f"{session_id}.json").read_text())
    assert transcript["schema_version"] == 1
    assert transcript["course"]["code"] == "MATH 242"
    assert [message["sequence"] for message in transcript["messages"]] == [1, 2]
    assert transcript["messages"][0]["created_at"] == "2026-11-15T12:30:00+00:00"
    assert transcript["messages"][1]["citations"] == [{"title": "APEX §11.3"}]
