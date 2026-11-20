"""Optional Unit 2.1 compatibility tests; no network or token required."""
import importlib.util
from pathlib import Path
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch

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
code_agent_module = load(
    "course_stage_one_code_agent", "challenges/00-first-tool/run_code_agent.py")
retrieval_module = load(
    "course_retrieval_agent", "challenges/02-retrieval-agent/retrieval_agent.py")
multi_agent_module = load(
    "course_multi_agent", "challenges/03-multi-agent/multi_agent.py")
agentic_rag_module = load(
    "course_agentic_rag", "challenges/06-agentic-rag/agentic_rag.py")


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

    def test_local_code_agent_is_bounded_and_constructs_without_network(self):
        agent = code_agent_module.build_local_agent()
        self.assertEqual(agent.max_steps, agent_module.MAX_STEPS)
        self.assertEqual(agent.model.model_id, agent_module.LOCAL_MODEL_ID)
        self.assertIn("search_flights_tool", agent.tools)
        self.assertEqual(agent.python_executor.additional_authorized_imports, [])

    def test_retrieval_tool_returns_ranked_source_label(self):
        tool = retrieval_module.KnowledgeBaseTool()
        result = tool(query="When does check-in close before departure?")
        self.assertIn("SOURCE: check-in-policy", result)
        self.assertIn("60 minutes", result)

    def test_retrieval_agent_constructs_without_network(self):
        agent = retrieval_module.build_local_agent()
        self.assertEqual(agent.max_steps, retrieval_module.MAX_STEPS)
        self.assertIn("search_travel_knowledge", agent.tools)

    def test_multi_agent_manager_and_worker_are_bounded(self):
        manager, worker = multi_agent_module.build_local_agents()
        self.assertEqual(manager.max_steps, multi_agent_module.MAX_STEPS)
        self.assertEqual(worker.max_steps, multi_agent_module.MAX_STEPS)
        self.assertEqual(worker.name, "travel_policy_researcher")
        self.assertIn("travel_policy_researcher", manager.managed_agents)
        self.assertIn("search_travel_knowledge", worker.tools)
        self.assertEqual(manager.python_executor.additional_authorized_imports, [])

    def test_agentic_rag_tools_are_labelled_and_agent_is_bounded(self):
        guest = agentic_rag_module.retrieve_guest(name="Ada Lovelace")
        weather = agentic_rag_module.get_fixture_weather(city="London")
        self.assertIn("GUEST SOURCE: local-guest-ada", guest)
        self.assertIn("WEATHER SOURCE: local-fixture-london", weather)
        agent = agentic_rag_module.build_local_agent()
        self.assertEqual(agent.max_steps, agentic_rag_module.MAX_STEPS)
        self.assertTrue(
            {"retrieve_guest", "get_fixture_weather"}.issubset(agent.tools)
        )

    def test_official_guest_rows_are_loaded_without_network(self):
        count = agentic_rag_module.load_official_guests([{
            "name": "Test Guest",
            "relation": "Friend",
            "description": "Enjoys science.",
            "email": "guest@example.com",
        }])
        result = agentic_rag_module.retrieve_guest(name="Test Guest")
        self.assertEqual(count, 1)
        self.assertIn("agents-course/unit3-invitees", result)
        self.assertIn("Enjoys science.", result)

    def test_guest_retrieval_ignores_common_honorifics(self):
        result = agentic_rag_module.retrieve_guest(name="Lady Ada Lovelace")
        self.assertIn("GUEST SOURCE: local-guest-ada", result)

    def test_guest_only_question_uses_deterministic_retrieval(self):
        result = agentic_rag_module.answer_guest_question(
            "Tell me about Lady Ada Lovelace."
        )
        self.assertIn("GUEST SOURCE: local-guest-ada", result)

    def test_mixed_live_question_is_left_for_agent(self):
        result = agentic_rag_module.answer_guest_question(
            "Tell me about Ada Lovelace and the latest news."
        )
        self.assertIsNone(result)

    def test_hub_stats_formats_mocked_public_result(self):
        model = SimpleNamespace(id="author/model", downloads=1234)
        with patch("huggingface_hub.list_models", return_value=[model]) as listed:
            result = agentic_rag_module.get_hub_stats(author="author")
        self.assertIn("author/model", result)
        self.assertIn("1,234", result)
        listed.assert_called_once_with(
            author="author", sort="downloads", direction=-1, limit=1
        )

    def test_official_agent_has_all_course_tools_without_network(self):
        agent = agentic_rag_module.build_official_agent()
        self.assertEqual(agent.max_steps, 5)
        self.assertTrue({
            "retrieve_guest", "get_fixture_weather", "get_hub_stats", "web_search"
        }.issubset(agent.tools))


if __name__ == "__main__":
    unittest.main()
