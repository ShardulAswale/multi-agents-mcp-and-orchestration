"""Offline Unit 4 regression tests; no provider, API, or credentials needed."""
import importlib.util
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1] / "projects/gaia-final-agent"


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


agent = load("gaia_capstone_agent", "agent.py")
benchmark = load("gaia_capstone_benchmark", "benchmark.py")


class GaiaAgentTests(unittest.TestCase):
    def test_calculator_order_of_operations(self):
        self.assertEqual(agent.calculate("2 + 3 * 4"), "14")
        self.assertEqual(agent.calculate("-(10 - 3)"), "-7")

    def test_calculator_rejects_code_and_resource_exhaustion(self):
        for expression in ['__import__("os")', '2 ** 10000000', '[1] * 100000', '"a" * 10']:
            with self.subTest(expression=expression), self.assertRaises((ValueError, SyntaxError)):
                agent.calculate(expression)

    def test_attachment_text_and_missing_file(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "evidence.txt"
            path.write_text("Relevant evidence", encoding="utf-8")
            self.assertEqual(agent.read_attachment(str(path)), "Relevant evidence")
            with self.assertRaises(FileNotFoundError):
                agent.read_attachment(str(path.with_name("missing.txt")))

    def test_unsupported_attachment_fails_explicitly(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "photo.png"
            path.write_bytes(b"not a photo")
            with self.assertRaisesRegex(ValueError, "Unsupported"):
                agent.read_attachment(str(path))

    def test_hf_requires_separate_live_opt_in(self):
        with self.assertRaisesRegex(RuntimeError, "HF_TOKEN"):
            agent.GAIAAgent(client=object(), environment={"AGENT_BACKEND": "hf"})
        with self.assertRaisesRegex(RuntimeError, "HF_LIVE_INFERENCE"):
            agent.GAIAAgent(client=object(), environment={
                "AGENT_BACKEND": "hf", "HF_TOKEN": "secret"})
        instance = agent.GAIAAgent(client=object(), environment={
            "AGENT_BACKEND": "hf", "HF_TOKEN": "secret", "HF_LIVE_INFERENCE": "1"})
        self.assertIn("Qwen", instance.model)

    def test_local_backend_no_token_or_provider_call(self):
        fake = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(
            create=lambda **kwargs: SimpleNamespace(choices=[SimpleNamespace(message=
                SimpleNamespace(content="FINAL ANSWER: 42", tool_calls=[]))]))))
        bot = agent.GAIAAgent(client=fake, environment={})
        self.assertEqual(bot.answer("What is the answer?"), "42")

    def test_calculator_tool_call_then_answer(self):
        calls = []
        tool_call = SimpleNamespace(id="abc", function=SimpleNamespace(
            name="calculate", arguments='{"expression": "6 * 7"}'))

        def respond(**kwargs):
            calls.append(kwargs)
            message = (SimpleNamespace(content=None, tool_calls=[tool_call])
                       if len(calls) == 1 else SimpleNamespace(content="42", tool_calls=[]))
            return SimpleNamespace(choices=[SimpleNamespace(message=message)])

        bot = agent.GAIAAgent(client=SimpleNamespace(chat=SimpleNamespace(
            completions=SimpleNamespace(create=respond))), environment={})
        self.assertEqual(bot.answer("Multiply 6 by 7"), "42")
        self.assertEqual(calls[1]["messages"][-1]["content"], "42")


class GaiaBenchmarkTests(unittest.TestCase):
    def test_question_format_checked(self):
        fake = SimpleNamespace(raise_for_status=lambda: None, json=lambda: ["bad"])
        with patch.dict(sys.modules, {"requests": SimpleNamespace(get=lambda *a, **k: fake)}):
            with self.assertRaises(ValueError):
                benchmark.questions()

    def test_evaluation_keeps_failure_explicit(self):
        class FakeAgent:
            def answer(self, question, attachment=None):
                if question == "bad":
                    raise RuntimeError("Do not hallucinate")
                return "good answer"
        with patch.object(benchmark, "questions", return_value=[
            {"task_id": "one", "question": "ok"},
            {"task_id": "two", "question": "bad"}]):
            results = benchmark.evaluate(FakeAgent())
        self.assertEqual(results[0]["submitted_answer"], "good answer")
        self.assertEqual(results[1]["submitted_answer"], "")
        self.assertEqual(results[1]["error"], "RuntimeError")

    def test_invalid_attachment_path_rejected_before_network(self):
        with self.assertRaisesRegex(ValueError, "task ID"):
            benchmark.attachment_for("../../etc", "a.txt", "/tmp")

    def test_submissions_reject_incomplete_blank_or_duplicate_answers(self):
        valid = [{"task_id": str(i), "submitted_answer": "answer"} for i in range(20)]
        url = "https://huggingface.co/spaces/test/agent/tree/main"
        with self.assertRaisesRegex(ValueError, "20 answers"):
            benchmark.submit("test", url, valid[:19])
        with self.assertRaisesRegex(ValueError, "empty"):
            benchmark.submit("test", url, valid[:19] + [{"task_id": "19", "submitted_answer": ""}])
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            benchmark.submit("test", url, valid[:19] + [valid[0]])
        with self.assertRaisesRegex(ValueError, "public Hugging Face"):
            benchmark.submit("test", url.replace("huggingface.co", "huggingface.co.evil"), valid)

    def test_valid_submission_posts_expected_payload(self):
        valid = [{"task_id": str(i), "submitted_answer": "yes"} for i in range(20)]
        recorded = {}

        def fake_post(url, json, timeout):
            recorded.update(url=url, data=json, timeout=timeout)
            return SimpleNamespace(raise_for_status=lambda: None, json=lambda: {"score": 0.3})

        with patch.dict(sys.modules, {"requests": SimpleNamespace(post=fake_post)}):
            response = benchmark.submit("test", "https://huggingface.co/spaces/test/agent/tree/main", valid)
        self.assertEqual(response["score"], 0.3)
        self.assertEqual(len(recorded["data"]["answers"]), 20)
        self.assertEqual(recorded["url"], benchmark.BASE + "/submit")


if __name__ == "__main__":
    unittest.main()
