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


if __name__ == "__main__":
    unittest.main()
