"""Process-local limiter for a single local API process; use edge limits in production."""
from collections import defaultdict, deque
from threading import Lock
from time import monotonic

from fastapi import HTTPException, Request

_buckets = defaultdict(deque)
_lock = Lock()


def limit_request(request: Request, *, bucket: str, count: int, seconds: int):
    host = request.client.host if request.client else "unknown"
    key = (bucket, host)
    now = monotonic()
    with _lock:
        if len(_buckets) > 10_000:
            for old_key in list(_buckets):
                old_events = _buckets[old_key]
                if not old_events or old_events[-1] <= now - 300:
                    _buckets.pop(old_key, None)
        events = _buckets[key]
        while events and events[0] <= now - seconds:
            events.popleft()
        if len(events) >= count:
            raise HTTPException(429, "Too many requests. Try again shortly.", headers={"Retry-After": str(seconds)})
        events.append(now)
