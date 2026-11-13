from app.rate_limit import SlidingWindowRateLimiter


def test_sliding_window_limits_each_key_and_expires_old_requests():
    limiter = SlidingWindowRateLimiter(limit=2, window_seconds=10)
    assert limiter.allow("jordan", now=0)
    assert limiter.allow("jordan", now=1)
    assert not limiter.allow("jordan", now=2)
    assert limiter.allow("avery", now=2)
    assert limiter.allow("jordan", now=10)


def test_zero_limit_disables_local_throttling():
    limiter = SlidingWindowRateLimiter(limit=0, window_seconds=10)
    assert all(limiter.allow("jordan", now=float(index)) for index in range(10))
