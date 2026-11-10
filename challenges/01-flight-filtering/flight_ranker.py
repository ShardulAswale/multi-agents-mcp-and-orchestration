"""Deterministic mock flight filtering for the first agent challenge."""

from datetime import datetime
from typing import Any


def has_overnight_layover(flight: dict[str, Any]) -> bool:
    """True when any connection crosses a local calendar date."""
    for layover in flight.get("layovers", []):
        arrival = datetime.fromisoformat(layover["arrival"])
        departure = datetime.fromisoformat(layover["departure"])
        if departure < arrival:
            raise ValueError("Layover departure precedes arrival")
        if departure.date() > arrival.date():
            return True
    return False


def rank_flights(flights: list[dict[str, Any]], exclude_overnight: bool = True) -> list[dict[str, Any]]:
    """Validate, filter, and return flights sorted by price."""
    eligible = []
    for flight in flights:
        if not isinstance(flight.get("price_gbp"), (int, float)) or isinstance(flight["price_gbp"], bool) or flight["price_gbp"] < 0:
            continue
        try:
            if exclude_overnight and has_overnight_layover(flight):
                continue
        except (KeyError, TypeError, ValueError):
            continue
        eligible.append(flight)
    return sorted(eligible, key=lambda flight: flight["price_gbp"])


if __name__ == "__main__":
    flights = [
        {"id": "A", "price_gbp": 180, "layovers": [{"arrival": "2026-12-01T23:00:00", "departure": "2026-12-02T06:00:00"}]},
        {"id": "B", "price_gbp": 220, "layovers": []},
    ]
    print(rank_flights(flights))
