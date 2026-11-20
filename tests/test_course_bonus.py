"""Offline regression tests for optional course bonus checkpoints."""
import importlib.util
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


training = load(
    "course_function_call_training",
    "challenges/08-function-calling-finetune/train_lora.py",
)
battle = load("course_pokemon_battle", "challenges/09-pokemon-agent/battle_agent.py")


class CourseBonusTests(unittest.TestCase):
    def test_function_call_records_have_matching_observation(self):
        records = training.validate_records(training.TRAINING_RECORDS)
        call = records[0]["messages"][2]["tool_calls"][0]
        observation = records[0]["messages"][3]
        self.assertEqual(call["id"], observation["tool_call_id"])
        self.assertEqual(json.loads(call["function"]["arguments"]), {"city": "London"})

    def test_training_defaults_to_validation_only(self):
        self.assertEqual(training.main([]), 0)

    def test_training_config_matches_installed_torch(self):
        import torch
        config = training.build_sft_config("unused-test-output")
        self.assertEqual(config.use_cpu, not torch.cuda.is_available())
        self.assertFalse(config.bf16 and config.fp16)
        self.assertFalse(config.gradient_checkpointing)
        if torch.cuda.is_available() and torch.cuda.get_device_capability(0)[0] < 8:
            self.assertTrue(config.fp16)

    def test_battle_agent_selects_expected_damage_and_tie_breaks(self):
        moves = [
            battle.Move("Zeta", 90, 1.0, 1),
            battle.Move("Alpha", 45, 1.0, 2),
            battle.Move("Weak", 120, 0.5, 1),
        ]
        self.assertEqual(battle.choose_move(moves).name, "Alpha")

    def test_battle_tool_rejects_invalid_or_invented_moves(self):
        tool = battle.BattleDecisionTool()
        payload = json.dumps([
            {"name": "Water Gun", "power": 40, "accuracy": 1.0, "effectiveness": 2},
            {"name": "Tackle", "power": 40, "accuracy": 1.0, "effectiveness": 1},
        ])
        self.assertEqual(tool.forward(payload), "Water Gun")
        with self.assertRaises(ValueError):
            tool.forward("not json")


if __name__ == "__main__":
    unittest.main()
