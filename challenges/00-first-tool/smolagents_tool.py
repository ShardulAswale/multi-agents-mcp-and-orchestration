"""Stage 1: expose the deterministic flight filter to smolagents.

Install: pip install smolagents
Run: python challenges/00-first-tool/smolagents_tool.py

This demonstrates the tool without needing an LLM or API token.
"""
import importlib.util
from pathlib import Path

from smolagents import tool

module_path = Path(__file__).with_name("search_flights.py")
spec = importlib.util.spec_from_file_location("flight_search_stage_one", module_path)
flight_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(flight_module)


@tool
def search_flights_tool(origin: str, destination: str, date: str) -> list[dict]:
    """Search mock flights for a specific route and departure date.

    Args:
        origin: Three-letter departure city code, such as LON.
        destination: Three-letter arrival city code, such as PAR.
        date: Departure date in YYYY-MM-DD format.
    """
    return flight_module.search_flights(
        flight_module.MOCK_FLIGHTS, origin, destination, date
    )


if __name__ == "__main__":
    print(search_flights_tool(origin="LON", destination="PAR", date="2026-12-01"))
