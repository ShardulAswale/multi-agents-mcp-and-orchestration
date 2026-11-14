"""Regression tests for Lesson 5; stdlib unittest, no external services."""
import importlib.util
from pathlib import Path
import unittest

path = Path(__file__).resolve().parents[1] / "lessons/05-multi-agent-coordination/coordinator.py"
spec = importlib.util.spec_from_file_location("lesson05_coordinator", path)
module = importlib.util.module_from_spec(spec)
import sys
sys.modules[spec.name] = module
spec.loader.exec_module(module)
Flight = module.Flight
SearchAgent = module.SearchAgent
RankingAgent = module.RankingAgent


class CoordinatorTests(unittest.TestCase):
    def setUp(self):
        self.search = SearchAgent([Flight("A", 300, True),
                                   Flight("B", 100, False),
                                   Flight("C", 200, True)])
        self.rank = RankingAgent()

    def test_deterministic_filters_and_ranks(self):
        result = module.DeterministicCoordinator(self.search, self.rank).run(
            {"direct_only": True})
        self.assertEqual([f.code for f in result["flights"]], ["C", "A"])
        self.assertEqual(self.rank.calls, 1)

    def test_empty_search_skips_ranking(self):
        result = module.DeterministicCoordinator(SearchAgent([]), self.rank).run({})
        self.assertEqual(result["status"], "no_flights_found")
        self.assertEqual(self.rank.calls, 0)

    def test_invalid_flag_skips_tools(self):
        result = module.DeterministicCoordinator(self.search, self.rank).run(
            {"direct_only": "yes"})
        self.assertEqual(result["status"], "invalid_request")
        self.assertEqual(self.search.calls, 0)

    def test_model_directed_happy_path(self):
        result = module.LLMDrivenCoordinator(
            self.search, self.rank, module.demo_router).run({"direct_only": True})
        self.assertEqual(result["status"], "success")
        self.assertEqual(self.search.calls, 1)
        self.assertEqual(self.rank.calls, 1)

    def test_invalid_router_tool_rejected(self):
        result = module.LLMDrivenCoordinator(
            self.search, self.rank, lambda state, allowed: "book").run({})
        self.assertEqual(result["status"], "invalid_router_choice")
        self.assertEqual(self.search.calls, 0)

    def test_rank_before_search_rejected(self):
        result = module.LLMDrivenCoordinator(
            self.search, self.rank, lambda state, allowed: "rank").run({})
        self.assertEqual(result["status"], "invalid_step_order")
        self.assertEqual(self.rank.calls, 0)

    def test_model_empty_search_skips_ranking(self):
        result = module.LLMDrivenCoordinator(
            SearchAgent([]), self.rank, module.demo_router).run({})
        self.assertEqual(result["status"], "no_flights_found")
        self.assertEqual(self.rank.calls, 0)

    def test_step_budget(self):
        result = module.LLMDrivenCoordinator(
            self.search, self.rank, module.demo_router, max_steps=2).run({})
        self.assertEqual(result["status"], "step_limit_exceeded")

    def test_non_mapping_request_skips_tools(self):
        result = module.DeterministicCoordinator(self.search, self.rank).run(None)
        self.assertEqual(result["status"], "invalid_request")
        self.assertEqual(self.search.calls, 0)

    def test_duplicate_search_is_rejected(self):
        choices = iter(("search", "search"))
        result = module.LLMDrivenCoordinator(
            self.search, self.rank, lambda state, allowed: next(choices)).run({})
        self.assertEqual(result["status"], "duplicate_search")
        self.assertEqual(self.search.calls, 1)

    def test_duplicate_rank_is_rejected(self):
        choices = iter(("search", "rank", "rank"))
        result = module.LLMDrivenCoordinator(
            self.search, self.rank, lambda state, allowed: next(choices)).run({})
        self.assertEqual(result["status"], "duplicate_rank")
        self.assertEqual(self.rank.calls, 1)

    def test_premature_finish_is_rejected(self):
        result = module.LLMDrivenCoordinator(
            self.search, self.rank, lambda state, allowed: "finish").run({})
        self.assertEqual(result["status"], "premature_finish")

    def test_invalid_flight_records_fail_at_boundary(self):
        for args in (("", 10, True), ("A", float("nan"), True),
                     ("A", -1, True), ("A", 10, "yes")):
            with self.subTest(args=args):
                with self.assertRaises(ValueError):
                    Flight(*args)


if __name__ == "__main__":
    unittest.main()
