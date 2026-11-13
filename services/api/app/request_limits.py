"""Early request-header validation shared by API middleware tests."""


def content_length_exceeds(content_length: str | None, max_bytes: int) -> bool:
    if content_length is None:
        return False
    try:
        return int(content_length) > max_bytes
    except ValueError:
        return True
