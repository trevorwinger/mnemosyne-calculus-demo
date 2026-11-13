"""Validation shared by course settings and the retention worker."""

from typing import Any


def learning_evidence_retention_days(preferences: Any) -> int | None:
    """Return the configured evidence-retention period, or unlimited retention.

    Preferences are JSON data, so accept only an actual integer here.  In
    particular, ``bool`` is intentionally rejected even though it subclasses
    ``int`` in Python.
    """
    if not isinstance(preferences, dict):
        raise ValueError("Tutoring preferences must be an object.")
    value = preferences.get("learning_evidence_retention_days")
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 3650:
        raise ValueError("Learning-evidence retention must be a whole number from 1 to 3650 days, or be left blank.")
    return value
