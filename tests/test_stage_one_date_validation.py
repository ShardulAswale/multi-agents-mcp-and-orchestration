"""Regression tests for Stage 1 flight search date validation."""
import importlib.util
from pathlib import Path
import unittest

SOURCE = Path(__file__).resolve().parents[1] / "challenges/00-first-tool/search_flights.py"
spec = importlib.util.spec_from_file_location("stage_one_flights", SOURCE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class DateValidationTests(unittest.TestCase):
    def test_valid_date_returns_matches(self):
        result = module.search_flights(module.MOCK_FLIGHTS, "LON", "PAR", "2026-12-01")
        self.assertEqual([flight["id"] for flight in result], ["FL101", "FL102"])

    def test_no_matches_returns_empty(self):
        self.assertEqual(module.search_flights(module.MOCK_FLIGHTS, "PAR", "LON", "2026-12-01"), [])

    def test_empty_input_returns_empty(self):
        self.assertEqual(module.search_flights([], "LON", "PAR", "2026-12-01"), [])

    def test_impossible_date_rejected(self):
        with self.assertRaises(ValueError):
            module.search_flights([], "LON", "PAR", "2026-02-30")

    def test_natural_language_date_rejected(self):
        with self.assertRaises(ValueError):
            module.search_flights([], "LON", "PAR", "next Friday")

    def test_non_padded_date_rejected(self):
        with self.assertRaises(ValueError):
            module.search_flights([], "LON", "PAR", "2026-2-3")


if __name__ == "__main__":
    unittest.main()
