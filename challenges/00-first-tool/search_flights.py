"""Stage 1: write your first agent-compatible Python tool.

This stage demonstrates dependency injection and deterministic filtering.
No LLM, network request, or API key is needed for this first step.
"""

from datetime import datetime

MOCK_FLIGHTS = [
    {"id": "FL101", "origin": "LON", "destination": "PAR", "date": "2026-12-01", "price_gbp": 85},
    {"id": "FL102", "origin": "LON", "destination": "PAR", "date": "2026-12-01", "price_gbp": 120},
    {"id": "FL103", "origin": "LON", "destination": "AMS", "date": "2026-12-01", "price_gbp": 95},
]


def _city_code(value: str, field: str) -> str:
    """Validate and normalize an IATA-style three-letter city code."""
    if (not isinstance(value, str) or len(value) != 3 or
            not value.isascii() or not value.isalpha()):
        raise ValueError(f"{field} must be a three-letter ASCII city code")
    return value.upper()


def search_flights(flights: list[dict], origin: str, destination: str, date: str) -> list[dict]:
    """Search mock flights by origin, destination, and departure date.

    Args:
        flights: Flight records to search without modifying them.
        origin: Three-letter origin city code, e.g. LON.
        destination: Three-letter destination city code, e.g. PAR.
        date: Departure date in YYYY-MM-DD format.

    Returns:
        Matching flight records, or an empty list if none match.
    """
    if not isinstance(flights, list):
        raise ValueError("flights must be a list of records")
    origin = _city_code(origin, "origin")
    destination = _city_code(destination, "destination")
    if origin == destination:
        raise ValueError("origin and destination cannot match")
    if not isinstance(date, str):
        raise ValueError("date must be a string in YYYY-MM-DD format")
    try:
        parsed_date = datetime.strptime(date, "%Y-%m-%d")
    except ValueError as exc:
        raise ValueError("date must be a valid calendar date in YYYY-MM-DD format") from exc
    if parsed_date.strftime("%Y-%m-%d") != date:
        raise ValueError("date must use exactly YYYY-MM-DD format")

    matches = []
    for flight in flights:
        # Provider records are untrusted. A malformed record must not crash the
        # whole search or be returned to the model as if it were valid.
        if not isinstance(flight, dict):
            continue
        record_origin = flight.get("origin")
        record_destination = flight.get("destination")
        if not isinstance(record_origin, str) or not isinstance(record_destination, str):
            continue
        if (record_origin.upper() == origin and
                record_destination.upper() == destination and
                flight.get("date") == date):
            matches.append(flight)
    return matches


if __name__ == "__main__":
    print(search_flights(MOCK_FLIGHTS, "LON", "PAR", "2026-12-01"))
