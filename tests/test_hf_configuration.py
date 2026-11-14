"""Offline tests for the opt-in Hugging Face integration configuration."""
import importlib.util
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

path = Path(__file__).resolve().parents[1] / "challenges/00-first-tool/run_agent.py"
spec = importlib.util.spec_from_file_location("stage_one_live_agent", path)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


class HuggingFaceConfigurationTests(unittest.TestCase):
    def test_live_call_requires_token_and_explicit_opt_in(self):
        with self.assertRaisesRegex(RuntimeError, "HF_TOKEN"):
            module.require_live_credentials({})
        with self.assertRaisesRegex(RuntimeError, "HF_LIVE_INFERENCE"):
            module.require_live_credentials({"HF_TOKEN": "secret"})
        self.assertEqual(
            module.require_live_credentials(
                {"HF_TOKEN": "secret", "HF_LIVE_INFERENCE": "1"}),
            "secret")

    def test_model_and_agent_limits_are_explicit(self):
        captured = {}

        class FakeModel:
            def __init__(self, **kwargs):
                captured["model"] = kwargs

        class FakeAgent:
            def __init__(self, **kwargs):
                captured["agent"] = kwargs

        fake_smolagents = SimpleNamespace(
            InferenceClientModel=FakeModel,
            ToolCallingAgent=FakeAgent,
            tool=lambda function: function)
        with patch.dict(sys.modules, {"smolagents": fake_smolagents}):
            module.build_agent("secret")

        model = captured["model"]
        self.assertEqual(model["model_id"], module.MODEL_ID)
        self.assertEqual(model["provider"], module.PROVIDER)
        self.assertEqual(model["timeout"], module.TIMEOUT_SECONDS)
        self.assertTrue(model["retry"])
        self.assertEqual(model["max_tokens"], module.MAX_TOKENS)
        self.assertEqual(captured["agent"]["max_steps"], module.MAX_STEPS)
        self.assertNotIn("secret", repr({k: v for k, v in model.items() if k != "token"}))

    def test_local_model_configuration_has_no_provider_credentials(self):
        captured = {}

        class FakeModel:
            def __init__(self, **kwargs):
                captured["model"] = kwargs

        class FakeAgent:
            def __init__(self, **kwargs):
                captured["agent"] = kwargs

        fake_smolagents = SimpleNamespace(
            OpenAIModel=FakeModel, ToolCallingAgent=FakeAgent,
            tool=lambda function: function)
        with patch.dict(sys.modules, {"smolagents": fake_smolagents}):
            module.build_local_agent()

        self.assertEqual(captured["model"]["model_id"], module.LOCAL_MODEL_ID)
        self.assertEqual(captured["model"]["api_base"], module.OLLAMA_BASE_URL)
        self.assertEqual(
            captured["model"]["client_kwargs"]["timeout"],
            module.LOCAL_TIMEOUT_SECONDS)
        self.assertEqual(captured["model"]["client_kwargs"]["max_retries"], 0)
        self.assertEqual(captured["agent"]["max_steps"], module.MAX_STEPS)


if __name__ == "__main__":
    unittest.main()
