"""Lesson 7 regression tests."""
import importlib.util
from pathlib import Path
import sys
import unittest

p = Path(__file__).resolve().parents[1] / "lessons/07-observability/observability.py"
spec = importlib.util.spec_from_file_location("lesson07_observability", p)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


class ObservabilityTests(unittest.TestCase):
    def test_trace_contains_expected_spans(self):
        recorder = module.Recorder()
        out = module.run_traced({"direct_only": True},
                                [module.mod.Flight("A", 10, True)], recorder)
        self.assertEqual(out["status"], "success")
        self.assertEqual({s.name for s in recorder.spans},
                         {"coordinator", "search", "rank"})
        self.assertEqual(len({s.trace_id for s in recorder.spans}), 1)

    def test_empty_search_skips_rank_span(self):
        recorder = module.Recorder()
        out = module.run_traced({}, [], recorder)
        self.assertEqual(out["status"], "no_flights_found")
        self.assertEqual({s.name for s in recorder.spans}, {"coordinator", "search"})

    def test_invalid_request_skips_tools(self):
        recorder = module.Recorder()
        out = module.run_traced({"direct_only": "yes"}, [], recorder)
        self.assertEqual(out["status"], "invalid_request")
        self.assertEqual([s.name for s in recorder.spans], ["coordinator"])

    def test_errors_recorded_and_propagated(self):
        recorder = module.Recorder(clock=lambda: 1.0)
        with self.assertRaises(ValueError):
            with recorder.span("trace", "search"):
                raise ValueError("tool unavailable")
        self.assertEqual(recorder.summary()["errors"], 1)

    def test_nearest_rank_percentiles(self):
        recorder = module.Recorder()
        for duration in (10, 20, 30, 40, 50):
            recorder.spans.append(module.Span("t", "test", duration, "ok"))
        summary = recorder.summary()
        self.assertEqual((summary["p50_ms"], summary["p95_ms"], summary["p99_ms"]),
                         (30, 50, 50))

    def test_json_has_no_request_secrets(self):
        recorder = module.Recorder()
        module.run_traced({"direct_only": True, "api_key": "SECRET_TOKEN"},
                          [module.mod.Flight("A", 10, True)], recorder)
        self.assertNotIn("SECRET_TOKEN", recorder.to_json_lines())

    def test_model_directed_trace(self):
        recorder = module.Recorder()
        out = module.run_traced({}, [module.mod.Flight("A", 10, True)],
                                recorder, model_directed=True)
        self.assertEqual(out["status"], "success")
        self.assertEqual(len(recorder.spans), 3)


if __name__ == "__main__":
    unittest.main()
