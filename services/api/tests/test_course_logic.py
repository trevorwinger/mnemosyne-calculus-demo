from app.main import concept_slug, learning_evidence_candidate


def test_concept_slugs_are_stable_and_safe():
    assert concept_slug("Arrays & Loop Bounds!") == "arrays-loop-bounds"
    assert concept_slug("!!!") == ""


def test_learning_evidence_requires_an_attempt_and_matches_course_terms():
    assert learning_evidence_candidate("What is a dot product?") is None
    candidate = learning_evidence_candidate("I think my dot product is 3, but I need a hint.")
    assert candidate and candidate["concept_slug"] == "vectors-geometry"
