from app.exercise_evaluation import evaluate_short_answer


def test_short_answer_check_is_normalized_and_never_reveals_key():
    assert evaluate_short_answer("  X = 4 ", "x = 4") == "matched"
    assert evaluate_short_answer("x = 5", "x = 4") == "try_again"
    assert evaluate_short_answer("x = 4", None) == "not_configured"
