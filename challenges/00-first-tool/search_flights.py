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
    if not isinstance(date, str):
        raise ValueError("date must be a string in YYYY-MM-DD format")
    try:
        parsed_date = datetime.strptime(date, "%Y-%m-%d")
    except ValueError as exc:
        raise ValueError("date must be a valid calendar date in YYYY-MM-DD format") from exc
    if parsed_date.strftime("%Y-%m-%d") != date:
        raise ValueError("date must use exactly YYYY-MM-DD format")

    return [
        flight for flight in flights
        if flight["origin"] == origin
        and flight["destination"] == destination
        and flight["date"] == date
    ]


if __name__ == "__main__":
    print(search_flights(MOCK_FLIGHTS, "LON", "PAR", "2026-12-01"))
