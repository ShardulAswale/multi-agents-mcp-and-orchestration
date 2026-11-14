"""Opt-in live Hugging Face smoke test; never run in the offline suite."""
import importlib.util
import os
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / "challenges/00-first-tool/run_agent.py"
spec = importlib.util.spec_from_file_location("stage_one_live_smoke", path)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


@unittest.skipUnless(os.environ.get("RUN_HF_LIVE_TESTS") == "1",
                     "live inference requires explicit opt-in")
class LiveHuggingFaceTests(unittest.TestCase):
    def test_tool_call_smoke(self):
        token = module.require_live_credentials()
        result = module.build_agent(token).run(
            "Call search_flights_tool exactly once with origin LON, destination "
            "PAR, and date 2026-12-01. Then summarize only the returned mock records."
        )
        self.assertTrue(str(result).strip())
        self.assertNotIn(token, str(result))


if __name__ == "__main__":
    unittest.main()
