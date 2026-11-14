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

    def test_city_codes_are_normalized(self):
        result = module.search_flights(module.MOCK_FLIGHTS, "lon", "par", "2026-12-01")
        self.assertEqual([flight["id"] for flight in result], ["FL101", "FL102"])

    def test_invalid_or_same_city_codes_are_rejected(self):
        for origin, destination in (("LO", "PAR"), ("L0N", "PAR"),
                                    ("LON", "LON"), (None, "PAR")):
            with self.subTest(origin=origin, destination=destination):
                with self.assertRaises(ValueError):
                    module.search_flights([], origin, destination, "2026-12-01")

    def test_malformed_provider_records_are_skipped(self):
        records = [None, {}, {"origin": "LON", "destination": "PAR"},
                   {"origin": 123, "destination": "PAR", "date": "2026-12-01"}]
        self.assertEqual(module.search_flights(records, "LON", "PAR", "2026-12-01"), [])


if __name__ == "__main__":
    unittest.main()
