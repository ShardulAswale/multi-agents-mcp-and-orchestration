"""Unit 2.1 bounded manager/worker checkpoint using local Ollama."""
from __future__ import annotations

import importlib.util
from pathlib import Path

from smolagents import CodeAgent, OpenAIModel, ToolCallingAgent

LOCAL_MODEL_ID = "qwen2.5:3b"
OLLAMA_BASE_URL = "http://127.0.0.1:11434/v1"
MAX_STEPS = 3


def _load_retrieval_module():
    path = Path(__file__).resolve().parents[1] / "02-retrieval-agent" / "retrieval_agent.py"
    spec = importlib.util.spec_from_file_location("course_retrieval_checkpoint", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _local_model():
    return OpenAIModel(
        model_id=LOCAL_MODEL_ID,
        api_base=OLLAMA_BASE_URL,
        api_key="ollama-local",
        client_kwargs={"timeout": 120, "max_retries": 0},
        max_tokens=256,
        temperature=0.0,
    )


def build_local_agents():
    """Construct a retrieval worker and its manager without making a model call."""
    retrieval = _load_retrieval_module()
    worker = ToolCallingAgent(
        tools=[retrieval.KnowledgeBaseTool()],
        model=_local_model(),
        max_steps=MAX_STEPS,
        name="travel_policy_researcher",
        description=(
            "Searches the local mock-travel knowledge base and returns source-labelled "
            "policy evidence. It cannot search the web or modify bookings."
        ),
        provide_run_summary=True,
    )
    manager = CodeAgent(
        tools=[],
        model=_local_model(),
        managed_agents=[worker],
        max_steps=MAX_STEPS,
        additional_authorized_imports=[],
        executor_type="local",
    )
    return manager, worker


if __name__ == "__main__":
    agent, _ = build_local_agents()
    print(
        agent.run(
            "Ask the travel policy researcher when check-in closes. "
            "Return the answer and its source identifier."
        )
    )
