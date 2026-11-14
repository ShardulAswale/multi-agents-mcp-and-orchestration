"""Lesson 4: explicit, scoped, expiring memory and a deterministic planner.

Run: python lessons/04-memory-and-planning/memory.py
An in-memory store is intentionally used instead of a database so learners
can inspect state transitions and test expiration without external services.
"""
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


@dataclass(frozen=True)
class Preference:
    value: str
    expires_at: datetime
    source: str  # e.g. 'explicit-user' — never silently infer consent


class PreferenceStore:
    def __init__(self) -> None:
        self._data: dict[tuple[str, str], Preference] = {}

    def remember(self, user_id: str, key: str, value: str, *,
                 now: datetime, ttl: timedelta, source: str = "explicit-user") -> None:
        """Only store explicit, scoped preferences with positive lifetime."""
        if (not isinstance(user_id, str) or not isinstance(key, str) or
                not isinstance(value, str) or not user_id or not key or not value or
                not isinstance(ttl, timedelta) or ttl <= timedelta(0)):
            raise ValueError("user, key, value and positive TTL are required")
        if not isinstance(now, datetime) or now.tzinfo is None or now.utcoffset() is None:
            raise ValueError("now must be timezone-aware")
        if source != "explicit-user":
            raise PermissionError("Do not persist inferred preferences as user instructions")
        self._data[(user_id, key)] = Preference(value, now + ttl, source)

    def recall(self, user_id: str, key: str, *, now: datetime) -> str | None:
        """Expired preferences are deleted and never silently reused."""
        if not isinstance(now, datetime) or now.tzinfo is None or now.utcoffset() is None:
            raise ValueError("now must be timezone-aware")
        item = self._data.get((user_id, key))
        if item is None:
            return None
        if now >= item.expires_at:
            del self._data[(user_id, key)]
            return None
        return item.value

    def forget(self, user_id: str, key: str) -> None:
        self._data.pop((user_id, key), None)


def plan_flight_search(origin: str | None, destination: str | None,
                       departure: str | None) -> list[str]:
    """Make missing inputs visible before any tool call.

    A plan is not an execution: every subsequent tool result must be checked.
    """
    missing = [name for name, value in
               (("origin", origin), ("destination", destination), ("departure", departure))
               if not value]
    if missing:
        return ["ask_user:" + ",".join(missing)]
    return ["validate_request", "search_flights", "filter_constraints",
            "rank_results", "present_options", "await_booking_approval"]


if __name__ == "__main__":
    store = PreferenceStore()
    now = datetime.now(timezone.utc)
    store.remember("demo-user", "seat", "aisle", now=now, ttl=timedelta(days=30))
    print("Seat preference:", store.recall("demo-user", "seat", now=now))
    print("Plan:", plan_flight_search("LON", "PAR", "2026-12-01"))
