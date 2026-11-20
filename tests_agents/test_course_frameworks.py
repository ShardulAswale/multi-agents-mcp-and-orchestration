"""Offline compatibility checks for optional course frameworks."""
import asyncio
import importlib.util
from pathlib import Path
import sys
import tempfile
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


try:
    llama_module = load(
        "course_llamaindex_workflow", "challenges/04-llamaindex/workflow.py"
    )
except ImportError:
    llama_module = None

try:
    langgraph_module = load(
        "course_langgraph_mail_sorter", "challenges/05-langgraph/mail_sorter.py"
    )
except ImportError:
    langgraph_module = None

try:
    vision_module = load(
        "course_smolagents_vision", "challenges/07-vision-agent/vision_agent.py"
    )
except ImportError:
    vision_module = None


class CourseFrameworkTests(unittest.TestCase):
    @unittest.skipIf(llama_module is None, 'install the "course" optional dependencies')
    def test_llamaindex_function_tool_and_workflow(self):
        result = llama_module.total_tool.call(unit_price=12.5, quantity=2)
        self.assertEqual(result.raw_output, 25.0)
        self.assertEqual(
            asyncio.run(llama_module.run_order_workflow(19.99, 2)), 39.98
        )
        with patch("llama_index.llms.ollama.Ollama") as ollama:
            with patch(
                "llama_index.core.agent.workflow.AgentWorkflow.from_tools_or_functions"
            ) as factory:
                llama_module.build_local_agent()
        ollama.assert_called_once()
        factory.assert_called_once()

        index = llama_module.build_document_index()
        results = index.as_retriever(similarity_top_k=1).retrieve("When does check-in close?")
        self.assertEqual(results[0].metadata["source"], "check-in-policy")
        from llama_index.core.llms import MockLLM
        engine = llama_module.build_query_engine(llm=MockLLM(max_tokens=32))
        response = engine.query("What is the baggage policy?")
        self.assertTrue(response.source_nodes)

    @unittest.skipIf(langgraph_module is None, 'install the "course" optional dependencies')
    def test_langgraph_routes_mail_through_conditional_edge(self):
        graph = langgraph_module.build_graph()
        billing = graph.invoke(
            {"subject": "Invoice question", "body": "I need a refund"}
        )
        support = graph.invoke(
            {"subject": "Help", "body": "The application is broken"}
        )
        self.assertEqual((billing["category"], billing["route"]), ("billing", "billing_queue"))
        self.assertEqual((support["category"], support["route"]), ("support", "support_queue"))
        react_graph = langgraph_module.build_local_react_graph()
        self.assertTrue({"model", "tools"}.issubset(react_graph.get_graph().nodes))

    @unittest.skipIf(langgraph_module is None, 'install the "course" optional dependencies')
    def test_langgraph_document_analysis_uses_injected_vision(self):
        calls = []

        def extractor(path, instruction):
            calls.append((path, instruction))
            return "Breakfast 12.50 Lunch 7.50"

        graph = langgraph_module.build_document_graph(extractor)
        result = graph.invoke({
            "document_path": "menu.png", "instruction": "Calculate the total",
            "extracted_text": "", "answer": "",
        })
        self.assertEqual(result["answer"], "20")
        self.assertEqual(calls, [("menu.png", "Calculate the total")])

    @unittest.skipIf(vision_module is None, 'install the "agents" optional dependencies')
    def test_smolagents_vision_tool_validates_and_calls_local_ollama(self):
        response = SimpleNamespace(
            raise_for_status=lambda: None,
            json=lambda: {"message": {"content": "A red ticket."}},
        )
        session = SimpleNamespace(post=lambda *args, **kwargs: response)
        with tempfile.TemporaryDirectory() as temporary:
            image = Path(temporary) / "ticket.png"
            image.write_bytes(b"not decoded by the mocked endpoint")
            result = vision_module.LocalVisionTool(session=session).forward(
                str(image), "What is visible?"
            )
        self.assertEqual(result, "A red ticket.")
