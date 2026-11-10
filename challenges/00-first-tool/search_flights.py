"""Stage 1: write your first agent-compatible Python tool.

Exercise: complete the TODO to return matching mock flights.
No LLM, network request, or API key is needed for this first step.
"""

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
    return [
        flight for flight in flights
        if flight["origin"] == origin
        and flight["destination"] == destination
        and flight["date"] == date
    ]


if __name__ == "__main__":
    print(search_flights(MOCK_FLIGHTS, "LON", "PAR", "2026-12-01"))
