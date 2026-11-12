"""Lesson 3: deterministic workflow with validation, bounded retries and approval.

Run: python lessons/03-reliable-workflows/workflow.py
No network, model, credentials, or purchase is involved.

WHY: an LLM can propose actions, but Python must enforce hard constraints.
A retry is appropriate for a transient *read* failure, not for an unguarded
purchase or other irreversible side effect.
"""
from dataclasses import dataclass
from datetime import date
from typing import Callable
import time


class TransientSearchError(Exception):
    """A temporary dependency error; callers may safely retry a read."""


@dataclass(frozen=True)
class Request:
    origin: str
    destination: str
    departure: str
    max_price_gbp: float
    direct_only: bool = True


def validate(request: Request) -> None:
    """Fail before any tool invocation if the user's hard constraints are invalid."""
    for code in (request.origin, request.destination):
        if not isinstance(code, str) or len(code) != 3 or not code.isalpha():
            raise ValueError("Origin and destination must be three-letter codes")
    if request.origin.upper() == request.destination.upper():
        raise ValueError("Origin and destination cannot match")
    try:
        if date.fromisoformat(request.departure).isoformat() != request.departure:
            raise ValueError("Use YYYY-MM-DD")
    except (TypeError, ValueError) as exc:
        raise ValueError("Departure must be a valid YYYY-MM-DD date") from exc
    if isinstance(request.max_price_gbp, bool) or not isinstance(request.max_price_gbp, (int, float)) or not 0 < request.max_price_gbp < float("inf"):
        raise ValueError("Budget must be a positive finite number")


def search_with_retry(search: Callable[[Request], list[dict]], request: Request,
                      attempts: int = 3, sleep: Callable[[float], None] = time.sleep) -> list[dict]:
    """Retry only transient search failures, with a strict maximum attempt count.

    Dependency injection makes both the search and the delay testable offline.
    Production alternatives include jitter, deadlines and circuit breakers.
    """
    if attempts < 1:
        raise ValueError("attempts must be >= 1")
    for attempt in range(attempts):
        try:
            return search(request)
        except TransientSearchError:
            if attempt == attempts - 1:
                raise
            sleep(min(2 ** attempt, 8))
    raise AssertionError("unreachable")


def recommend(request: Request, search: Callable[[Request], list[dict]]) -> list[dict]:
    """Validate -> search -> independently filter -> rank, without booking."""
    validate(request)
    records = search_with_retry(search, request)
    eligible = []
    for item in records:
        price = item.get("price_gbp")
        if isinstance(price, bool) or not isinstance(price, (int, float)) or not 0 <= price <= request.max_price_gbp:
            continue
        if item.get("origin", "").upper() != request.origin.upper() or item.get("destination", "").upper() != request.destination.upper():
            continue
        if item.get("date") != request.departure:
            continue
        if request.direct_only and item.get("stops") != 0:
            continue
        eligible.append(item)
    return sorted(eligible, key=lambda item: (item["price_gbp"], item["id"]))


def require_booking_approval(approved: bool) -> None:
    """A separate gate for a future booking action; never assume consent."""
    if approved is not True:
        raise PermissionError("Explicit user approval is required before booking")


if __name__ == "__main__":
    request = Request("LON", "PAR", "2026-12-01", 150)
    def mock_search(_request: Request) -> list[dict]:
        return [
            {"id": "A", "origin": "LON", "destination": "PAR", "date": "2026-12-01", "price_gbp": 85, "stops": 0},
            {"id": "B", "origin": "LON", "destination": "PAR", "date": "2026-12-01", "price_gbp": 60, "stops": 1},
        ]
    print(recommend(request, mock_search))
