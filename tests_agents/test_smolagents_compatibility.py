"""Optional Unit 2.1 compatibility tests; no network or token required."""
import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


tool_module = load(
    "course_stage_one_tool", "challenges/00-first-tool/smolagents_tool.py")
agent_module = load(
    "course_stage_one_agent", "challenges/00-first-tool/run_agent.py")


class SmolagentsCompatibilityTests(unittest.TestCase):
    def test_decorated_tool_executes_validated_search(self):
        results = tool_module.search_flights_tool(
            origin="lon", destination="par", date="2026-12-01")
        self.assertEqual([flight["id"] for flight in results], ["FL101", "FL102"])

    def test_agent_constructs_without_provider_call(self):
        agent = agent_module.build_agent("test-token-not-a-credential")
        self.assertEqual(agent.max_steps, agent_module.MAX_STEPS)
        self.assertEqual(agent.model.model_id, agent_module.MODEL_ID)
        self.assertIn("search_flights_tool", agent.tools)

    def test_local_agent_constructs_without_network(self):
        agent = agent_module.build_local_agent()
        self.assertEqual(agent.max_steps, agent_module.MAX_STEPS)
        self.assertEqual(agent.model.model_id, agent_module.LOCAL_MODEL_ID)
        self.assertIn("search_flights_tool", agent.tools)


if __name__ == "__main__":
    unittest.main()
