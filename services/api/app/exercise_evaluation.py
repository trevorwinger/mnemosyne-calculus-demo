"""Bounded, deterministic feedback for instructor-keyed short-answer practice."""

import re


def normalize_answer(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().casefold())


def evaluate_short_answer(response: str, expected_answer: str | None) -> str:
    """Return feedback state only; never return or expose the instructor key."""
    if not expected_answer or not expected_answer.strip():
        return "not_configured"
    return "matched" if normalize_answer(response) == normalize_answer(expected_answer) else "try_again"
