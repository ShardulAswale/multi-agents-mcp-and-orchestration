"""Lesson 6 evaluation regression tests, stdlib only."""
import importlib.util
from pathlib import Path
import sys
import unittest

path = Path(__file__).resolve().parents[1] / "lessons/06-agent-evaluation/evaluate.py"
spec = importlib.util.spec_from_file_location("lesson06_evaluation", path)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


class EvaluationTests(unittest.TestCase):
    def test_deterministic_suite(self):
        report = module.evaluate_suite()
        self.assertEqual(report["total"], 5)
        self.assertEqual(report["passed"], 5)
        self.assertEqual(report["task_success_rate"], 1.0)

    def test_simulated_router_suite(self):
        report = module.evaluate_suite(model_directed=True)
        self.assertEqual(report["passed"], 5)

    def test_constraint_failure_detected(self):
        case = module.Case("bad_reference", {"direct_only": True},
                           (module.Flight("A", 30, False),),
                           "success", ("A",))
        result = module.evaluate_case(case)
        self.assertFalse(result["passed"])

    def test_wrong_ranking_reference_detected(self):
        case = module.Case("wrong_order", {},
                           (module.Flight("A", 10, True),
                            module.Flight("B", 20, True)),
                           "success", ("B", "A"))
        self.assertFalse(module.evaluate_case(case)["passed"])

    def test_empty_suite_no_division_error(self):
        report = module.evaluate_suite(cases=())
        self.assertEqual(report["total"], 0)
        self.assertEqual(report["task_success_rate"], 0.0)

    def test_empty_inventory_does_not_rank(self):
        result = module.evaluate_case(module.CASES[2])
        self.assertEqual(result["rank_calls"], 0)
        self.assertTrue(result["passed"])


if __name__ == "__main__":
    unittest.main()
