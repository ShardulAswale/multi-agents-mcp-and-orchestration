# Official Hugging Face Agents Course progress

Source: [Hugging Face AI Agents Course](https://huggingface.co/learn/agents-course/en/unit0/introduction).

This file distinguishes official course progress from extra engineering material in this repository. A checked code checkpoint means the corresponding local example runs and has regression coverage; it does not award or claim a Hugging Face certificate.

## Completed up to the current code boundary

### Unit 0 — Welcome and setup

- Read the syllabus and prerequisites.
- Local Python environment and optional Hugging Face dependency installation work.
- `HF_TOKEN` remains optional and is never required for offline tests.

### Unit 1 — Introduction to Agents

- Agent/tool concepts and the Thought → Action → Observation loop are documented in `lessons/01-agent-fundamentals`.
- The course’s dummy-agent lesson explains why an Observation must come from executing a tool rather than from model fabrication. Locally, deterministic search is the source of truth and the model is instructed to report only tool output.
- `challenges/00-first-tool/search_flights.py` is the Python-function tool.
- The official Unit 1 tutorial demonstrates a `CodeAgent` in a Hugging Face Space. This repository does not claim that exact Space exercise as completed. Its runnable checkpoint uses the safer structured `ToolCallingAgent` introduced in Unit 2.1, adapted to mock flights with bounded steps, explicit model/provider settings, and opt-in inference.

### Unit 2.1 — smolagents (partial)

- Tools: `smolagents_tool.py` uses the recommended `@tool` decorator, type hints, return type, clear docstring, and `Args:` descriptions.
- Tool Calling Agents: `run_agent.py` uses `ToolCallingAgent`, whose structured calls are validated by the Python tool boundary.
- The wrapper and agent construction have optional compatibility tests that make no provider call.

## Deliberately not completed

- Remaining Unit 2.1 topics: CodeAgent exercises, retrieval agents, vision agents, and the official multi-agent notebook.
- Unit 2.2: LlamaIndex.
- Unit 2.3: LangGraph.
- Unit 3: Agentic RAG use case.
- Unit 4: benchmark qualification, leaderboard submission, and certification. The code in `projects/gaia-final-agent/` is a runnable starting implementation but has not been submitted, scored, or certified.
- Bonus units.

The repository’s Lessons 3–7 are independent engineering extensions covering reliability, memory, coordination, evaluation, and observability. They are useful and tested, but they must not be confused with completion of the official units above.

## Run the implemented checkpoints

```text
python -m pip install -e ".[agents]"
python challenges/00-first-tool/search_flights.py
python challenges/00-first-tool/smolagents_tool.py
python -m unittest discover -s tests -v
python -m unittest discover -s tests_agents -v
```

The first two examples are local. Constructing the agent in `tests_agents` is also local. A real provider call is made only by `run_agent.py` or `tests_live` after the explicit live-inference gates are enabled.
