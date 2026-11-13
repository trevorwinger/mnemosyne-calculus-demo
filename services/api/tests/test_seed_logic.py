from app.providers import demo_response

def test_demo_provider_array_hint_is_not_a_finished_solution():
    answer = demo_response("I have a values.length loop")
    assert "last valid index" in answer
    assert "What condition" in answer
