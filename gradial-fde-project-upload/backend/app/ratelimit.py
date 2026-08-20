"""In-memory safety valves for a publicly deployed demo running with a real
OPENAI_API_KEY. Every accepted request spends real money, so a public link
needs hard caps rather than trusting visitors to be nice.

Deliberately simple (single-process, in-memory, resets on restart) — this
is sized for "a demo link in a job application," not production traffic.
A real deployment serving real load would move this to Redis and add
per-account billing limits instead.
"""
import threading
import time
from collections import defaultdict, deque

from fastapi import HTTPException

from .config import settings

_lock = threading.Lock()
_ip_hits: dict[str, deque] = defaultdict(deque)
_day_key: str | None = None
_day_count = 0

ONE_HOUR = 3600


def _today_key() -> str:
    return time.strftime("%Y-%m-%d", time.gmtime())


def check_and_record(client_ip: str, live: bool):
    """Raise HTTPException(429) if this request would exceed a limit;
    otherwise record it as spent. Only the live (real-OpenAI-key) path is
    capped by the daily global limit — mock mode is free, so it's only
    subject to the light per-IP limit that protects the server itself.
    """
    global _day_key, _day_count

    now = time.time()
    with _lock:
        hits = _ip_hits[client_ip]
        while hits and now - hits[0] > ONE_HOUR:
            hits.popleft()
        if len(hits) >= settings.max_requests_per_ip_per_hour:
            raise HTTPException(
                429,
                f"Rate limit: max {settings.max_requests_per_ip_per_hour} requests per hour per visitor "
                "on this public demo. Try again later, or run it locally with your own key for unlimited use.",
            )

        if live:
            today = _today_key()
            if _day_key != today:
                _day_key = today
                _day_count = 0
            if _day_count >= settings.max_live_requests_per_day:
                raise HTTPException(
                    429,
                    "This public demo has hit its daily cap on live AI requests (to keep the owner's OpenAI bill "
                    "sane). It'll reset tomorrow, or clone the repo and run it with your own key.",
                )
            _day_count += 1

        hits.append(now)
