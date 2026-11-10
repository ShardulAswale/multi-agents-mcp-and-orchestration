"""Run a first LLM-driven flight search with smolagents.

Install: pip install -e ".[agents]"
Set HF_TOKEN in your environment (never commit it).
Run: python challenges/00-first-tool/run_agent.py

Requires network access and a Hugging Face account with inference access.
The flights themselves are mock records, not live availability.
"""
import importlib.util
import os
from pathlib import Path

from smolagents import InferenceClientModel, ToolCallingAgent

tool_path = Path(__file__).with_name("smolagents_tool.py")
spec = importlib.util.spec_from_file_location("flight_tool_stage_one", tool_path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

if not os.environ.get("HF_TOKEN"):
    raise SystemExit("Set HF_TOKEN before running this example.")

model = InferenceClientModel()
agent = ToolCallingAgent(
    tools=[module.search_flights_tool],
    model=model,
    max_steps=3,
)

request = (
    "Today is Tuesday 2026-11-10 in Europe/London. "
    "Find flights from London (LON) to Paris (PAR) next Friday. "
    "Resolve the date to YYYY-MM-DD before calling the search tool. "
    "Only report results returned by the tool; these are mock flights, "
    "not bookable live flights. If there are no results, say so."
)
print(agent.run(request))
