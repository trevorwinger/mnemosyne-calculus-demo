import pytest

from app.retention import learning_evidence_retention_days


def test_learning_evidence_retention_is_optional_and_bounded():
    assert learning_evidence_retention_days({}) is None
    assert learning_evidence_retention_days({"learning_evidence_retention_days": 90}) == 90
    with pytest.raises(ValueError):
        learning_evidence_retention_days({"learning_evidence_retention_days": 0})
    with pytest.raises(ValueError):
        learning_evidence_retention_days({"learning_evidence_retention_days": True})
