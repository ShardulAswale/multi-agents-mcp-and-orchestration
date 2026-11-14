"""Offline regression tests for lessons 3 and 4."""
import importlib.util
from datetime import datetime, timedelta, timezone
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

def load(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    import sys
    sys.modules[name] = module  # dataclass resolves module namespace
    spec.loader.exec_module(module)
    return module

workflow = load("course_workflow", "lessons/03-reliable-workflows/workflow.py")
memory = load("course_memory", "lessons/04-memory-and-planning/memory.py")

class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.request = workflow.Request("LON", "PAR", "2026-12-01", 100)

    def test_hard_constraints_beat_price(self):
        data = [
            dict(id="direct", origin="LON", destination="PAR", date="2026-12-01", price_gbp=80, stops=0),
            dict(id="cheap_connection", origin="LON", destination="PAR", date="2026-12-01", price_gbp=40, stops=1),
            dict(id="wrong_route", origin="LON", destination="AMS", date="2026-12-01", price_gbp=30, stops=0),
        ]
        self.assertEqual([x["id"] for x in workflow.recommend(self.request, lambda _: data)], ["direct"])

    def test_retry_is_bounded(self):
        calls = []
        def flaky(_):
            calls.append(1)
            if len(calls) < 3:
                raise workflow.TransientSearchError()
            return []
        self.assertEqual(workflow.search_with_retry(flaky, self.request, sleep=lambda _: None), [])
        self.assertEqual(len(calls), 3)

    def test_invalid_input_never_searches(self):
        with self.assertRaises(ValueError):
            workflow.recommend(workflow.Request("LON", "PAR", "invalid", 100), lambda _: self.fail("called"))

    def test_booking_requires_approval(self):
        with self.assertRaises(PermissionError):
            workflow.require_booking_approval(False)

    def test_direct_only_must_be_boolean_and_skips_search(self):
        with self.assertRaises(ValueError):
            workflow.recommend(
                workflow.Request("LON", "PAR", "2026-12-01", 100, "yes"),
                lambda _: self.fail("search called"))

    def test_retry_exhaustion_and_non_transient_error(self):
        transient_calls = []
        def transient(_):
            transient_calls.append(1)
            raise workflow.TransientSearchError("busy")
        with self.assertRaises(workflow.TransientSearchError):
            workflow.search_with_retry(transient, self.request, attempts=2,
                                       sleep=lambda _: None)
        self.assertEqual(len(transient_calls), 2)

        permanent_calls = []
        def permanent(_):
            permanent_calls.append(1)
            raise ValueError("bad request")
        with self.assertRaises(ValueError):
            workflow.search_with_retry(permanent, self.request, attempts=3,
                                       sleep=lambda _: None)
        self.assertEqual(len(permanent_calls), 1)

    def test_malformed_search_output_is_rejected_or_skipped(self):
        with self.assertRaises(ValueError):
            workflow.recommend(self.request, lambda _: None)
        records = [None, {"price_gbp": 5},
                   dict(id="bool_stops", origin="LON", destination="PAR",
                        date="2026-12-01", price_gbp=5, stops=False),
                   dict(id="bad_route_type", origin=123, destination="PAR",
                        date="2026-12-01", price_gbp=5, stops=0)]
        self.assertEqual(workflow.recommend(self.request, lambda _: records), [])

class MemoryTests(unittest.TestCase):
    def test_expiration_and_isolation(self):
        now = datetime(2026, 11, 12, tzinfo=timezone.utc)
        store = memory.PreferenceStore()
        store.remember("A", "seat", "aisle", now=now, ttl=timedelta(days=1))
        self.assertEqual(store.recall("A", "seat", now=now), "aisle")
        self.assertIsNone(store.recall("B", "seat", now=now))
        self.assertIsNone(store.recall("A", "seat", now=now + timedelta(days=2)))

    def test_missing_information_stops_plan(self):
        self.assertEqual(memory.plan_flight_search("LON", "PAR", None), ["ask_user:departure"])

    def test_naive_memory_timestamps_are_rejected(self):
        store = memory.PreferenceStore()
        naive = datetime(2026, 11, 12)
        with self.assertRaises(ValueError):
            store.remember("A", "seat", "aisle", now=naive,
                           ttl=timedelta(days=1))
        with self.assertRaises(ValueError):
            store.recall("A", "seat", now=naive)

    def test_inferred_preference_is_not_persisted(self):
        store = memory.PreferenceStore()
        with self.assertRaises(PermissionError):
            store.remember("A", "seat", "aisle",
                           now=datetime(2026, 11, 12, tzinfo=timezone.utc),
                           ttl=timedelta(days=1), source="inferred")

if __name__ == "__main__":
    unittest.main()
