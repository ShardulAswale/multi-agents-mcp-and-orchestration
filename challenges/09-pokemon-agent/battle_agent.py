"""Bonus Unit 3: bounded local Pokémon-style battle advisor checkpoint."""
from __future__ import annotations

from dataclasses import dataclass
import json

from smolagents import OpenAIModel, Tool, ToolCallingAgent

LOCAL_MODEL_ID = "qwen2.5:3b"
OLLAMA_BASE_URL = "http://127.0.0.1:11434/v1"


@dataclass(frozen=True)
class Move:
    name: str
    power: int
    accuracy: float
    effectiveness: float = 1.0

    def __post_init__(self):
        if not self.name.strip() or not 0 <= self.power <= 250:
            raise ValueError("move name and power are invalid")
        if not 0 <= self.accuracy <= 1 or self.effectiveness not in {0, 0.25, 0.5, 1, 2, 4}:
            raise ValueError("accuracy or effectiveness is invalid")


def choose_move(moves: list[Move]) -> Move:
    """Choose maximum expected damage with a deterministic name tie-break."""
    if not moves:
        raise ValueError("at least one legal move is required")
    return sorted(
        moves,
        key=lambda move: (-(move.power * move.accuracy * move.effectiveness), move.name.casefold()),
    )[0]


class BattleDecisionTool(Tool):
    name = "choose_legal_move"
    description = "Choose the legal move with highest expected type-adjusted damage."
    inputs = {
        "moves_json": {
            "type": "string",
            "description": "JSON list of moves with name, power, accuracy, and effectiveness.",
        }
    }
    output_type = "string"

    def forward(self, moves_json: str) -> str:
        try:
            values = json.loads(moves_json)
            moves = [Move(**item) for item in values]
        except (TypeError, ValueError, json.JSONDecodeError) as error:
            raise ValueError("moves_json must contain valid legal moves") from error
        return choose_move(moves).name


def build_local_agent():
    """Construct a bounded Ollama advisor around the validated battle tool."""
    model = OpenAIModel(
        model_id=LOCAL_MODEL_ID, api_base=OLLAMA_BASE_URL,
        api_key="ollama-local", client_kwargs={"timeout": 120, "max_retries": 0},
        max_tokens=128, temperature=0.0,
    )
    return ToolCallingAgent(
        tools=[BattleDecisionTool()], model=model, max_steps=3,
        instructions=(
            "Always call choose_legal_move exactly once using only the supplied legal moves. "
            "Return only the selected move name; never invent a move or contact a battle server."
        ),
    )


if __name__ == "__main__":
    demo = [Move("Thunderbolt", 90, 1.0, 2), Move("Quick Attack", 40, 1.0, 1)]
    print(choose_move(demo).name)
