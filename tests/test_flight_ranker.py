"""Unit tests for the first flight-filtering challenge."""

import importlib.util
from pathlib import Path
import unittest

MODULE_PATH = Path(__file__).resolve().parents[1] / "challenges/01-flight-filtering/flight_ranker.py"
spec = importlib.util.spec_from_file_location("flight_ranker", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class FlightRankingTests(unittest.TestCase):
    def test_overnight_excluded(self):
        flights = [
            {"id": "overnight", "price_gbp": 180, "layovers": [{"arrival": "2026-12-01T23:00:00", "departure": "2026-12-02T06:00:00"}]},
            {"id": "direct", "price_gbp": 220, "layovers": []},
        ]
        self.assertEqual([f["id"] for f in module.rank_flights(flights)], ["direct"])

    def test_price_sort(self):
        flights = [{"id": "expensive", "price_gbp": 300}, {"id": "cheap", "price_gbp": 100}]
        self.assertEqual([f["id"] for f in module.rank_flights(flights)], ["cheap", "expensive"])

    def test_invalid_price_excluded(self):
        self.assertEqual(module.rank_flights([{"id": "bad", "price_gbp": -1}]), [])

    def test_empty(self):
        self.assertEqual(module.rank_flights([]), [])


if __name__ == "__main__":
    unittest.main()
