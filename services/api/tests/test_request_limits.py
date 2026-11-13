from app.request_limits import content_length_exceeds


def test_content_length_limit_accepts_small_values_and_rejects_invalid_or_large_headers():
    assert not content_length_exceeds(None, 100)
    assert not content_length_exceeds("100", 100)
    assert content_length_exceeds("101", 100)
    assert content_length_exceeds("not-a-size", 100)
