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

### Unit 2.1 — smolagents (implemented local checkpoints)

- Tools: `smolagents_tool.py` uses the recommended `@tool` decorator, type hints, return type, clear docstring, and `Args:` descriptions.
- Tool Calling Agents: `run_agent.py` uses `ToolCallingAgent`, whose structured calls are validated by the Python tool boundary.
- The wrapper and agent construction have optional compatibility tests that make no provider call.
- Code agents: `run_code_agent.py` constructs a bounded `CodeAgent` with the same validated mock-flight tool, local Ollama default, no additional authorized imports, and explicit provider opt-in.
- Retrieval agents: `challenges/02-retrieval-agent/retrieval_agent.py` provides a source-labelled local knowledge-base tool with deterministic ranking and a bounded Ollama-backed `CodeAgent`.
- Multi-agent systems: `challenges/03-multi-agent/multi_agent.py` gives a bounded retrieval worker a narrow role and lets a bounded manager delegate policy research to it.
- Vision agents: `challenges/07-vision-agent/vision_agent.py` exposes a bounded, path-validated Ollama vision tool to a `ToolCallingAgent`. Tests mock the local endpoint; no hosted VLM is invoked automatically.

### Unit 2.2 — LlamaIndex

- `challenges/04-llamaindex/workflow.py` implements a validated `FunctionTool`, typed event-driven `Workflow`, and local Ollama `AgentWorkflow` construction.
- The same checkpoint builds a `VectorStoreIndex` with deterministic local embeddings, exposes a `QueryEngine`, and wraps it in a `QueryEngineTool` for a bounded local RAG agent.

### Unit 2.3 — LangGraph

- `challenges/05-langgraph/mail_sorter.py` implements typed state, nodes, edges, conditional routing, terminal paths, and local Ollama ReAct graph construction.
- Its document graph validates local image inputs, extracts visible evidence through the installed Ollama VLM, and routes the result through deterministic analysis. Offline tests inject the extractor and make no model call.

### Unit 3 — Agentic RAG

- `challenges/06-agentic-rag/agentic_rag.py` implements the official Alfred gala use case: source-labelled retrieval from `agents-course/unit3-invitees`, DuckDuckGo web search, the course's labelled weather fixture, Hugging Face Hub model statistics, and one bounded Ollama-backed agent.
- Offline mode retains local fixtures. Official mode requires `--official-live`, so importing, constructing, and testing the agent never downloads data or calls public services automatically.

### Bonus units — local checkpoints

- Bonus 1: `challenges/08-function-calling-finetune/train_lora.py` validates tool-call training conversations and provides an explicitly confirmed local LoRA pipeline. Matching 20-step adapter runs completed against `Qwen/Qwen2.5-0.5B-Instruct`: 139.5 seconds on CPU and 9.389 seconds on the RTX 2060 with FP16 (about 14.9x faster). Both private outputs are Git-ignored and have not been published; the two-record fixture is not a quality benchmark.
- Bonus 2: `lessons/06-agent-evaluation/evaluate.py` and `lessons/07-observability/observability.py` provide offline evaluation, latency/error spans, safe trace export and regression tests without a hosted telemetry subscription.
- Bonus 3: `challenges/09-pokemon-agent/battle_agent.py` implements validated legal moves, deterministic expected-damage selection, and a bounded Ollama battle advisor. It does not connect to Pokémon Showdown automatically.

## External completion evidence and boundaries

- Unit 4: the local Ollama workflow submitted 16 valid tasks and received an official 35% score (7/20) on 2026-11-20. The public code link is `https://huggingface.co/spaces/Shardul-Aswale/gaia-final-agent/tree/main`. The user confirmed certificate issuance on 2026-11-20.
- Hosted notebooks, live provider inference, telemetry services, adapter publication and online game servers remain explicit opt-in activities. Their local pipelines are implemented, but this file does not claim those external executions occurred.
- Bonus units.

The repository’s Lessons 3–7 are independent engineering extensions covering reliability, memory, coordination, evaluation, and observability. They are useful and tested, but they must not be confused with completion of the official units above.

## Run the implemented checkpoints

```text
python -m pip install -e ".[agents]"
python challenges/00-first-tool/search_flights.py
python challenges/00-first-tool/smolagents_tool.py
python challenges/00-first-tool/run_code_agent.py
python challenges/02-retrieval-agent/retrieval_agent.py
python challenges/03-multi-agent/multi_agent.py
python challenges/04-llamaindex/workflow.py
python challenges/05-langgraph/mail_sorter.py
python challenges/06-agentic-rag/agentic_rag.py
python challenges/08-function-calling-finetune/train_lora.py
python challenges/09-pokemon-agent/battle_agent.py
python -m unittest discover -s tests -v
python -m unittest discover -s tests_agents -v
```

The first two examples are local. Constructing the agent in `tests_agents` is also local. A real provider call is made only by `run_agent.py` or `tests_live` after the explicit live-inference gates are enabled.
