# Multi-Agents, MCP and Orchestration

Hands-on learning repository following the official [Hugging Face AI Agents Course](https://huggingface.co/learn/agents-course/en/unit0/introduction). Local checkpoints cover the core framework units, Agentic RAG architecture and optional bonus-unit equivalents, with external-execution boundaries recorded below. The Unit 4 GAIA capstone achieved an official 35% score. Flight records are fixtures: this repository does not search live inventory or book tickets.

## Structure
- `lessons/`: numbered learning notes and pseudocode
- `challenges/`: runnable implementations
- `tests/`: deterministic regression tests
- `projects/`: capstone agent applications, including the [Unit 4 GAIA agent](projects/gaia-final-agent/README.md)

## Start here
1. Create a Python 3.10+ virtual environment.
2. Run `python -m pip install -e .` for offline lessons, or `python -m pip install -e ".[agents]"` for the optional smolagents example.
3. Read [Agent fundamentals](lessons/01-agent-fundamentals/README.md) and [Tool calling](lessons/02-tool-calling/README.md).
4. Run `python -m unittest discover -s tests -v`.
5. Stop at the boundary in [COURSE_PROGRESS.md](COURSE_PROGRESS.md). Use the [Learning Compendium](LEARNING_COMPENDIUM.md) only if you want the repository-specific extensions.

The exact official-course mapping and stopping point are recorded in [COURSE_PROGRESS.md](COURSE_PROGRESS.md). The reliability, memory, coordination, evaluation, and observability lessons are repository extensions; they are not claims that later official course units are complete.

## Official course progress

- [x] Unit 0 orientation and local setup
- [x] Unit 1 fundamentals: agents, tools, Thought → Action → Observation
- [x] Unit 1 runnable checkpoint adapted to the mock flight domain
- [x] Unit 2.1 tools with `@tool`
- [x] Unit 2.1 `ToolCallingAgent` checkpoint
- [x] Unit 2.1 bounded local `CodeAgent` checkpoint
- [x] Unit 2.1 local custom knowledge-base retrieval checkpoint
- [x] Unit 2.1 bounded local manager/worker checkpoint
- [x] Unit 2.1 bounded local vision-agent checkpoint
- [x] Unit 2.2 LlamaIndex tool/workflow/query-engine/local-agent checkpoint
- [x] Unit 2.3 LangGraph routing, local ReAct and document-vision checkpoint
- [x] Unit 3 official Alfred Agentic RAG use case (local Ollama plus opt-in public integrations)
- [x] Unit 4 official qualification threshold (35%, 7/20; certificate not claimed)
- [x] Bonus Unit 1 validated LoRA/function-calling pipeline and local adapter training
- [x] Bonus Unit 2 local observability and offline evaluation checkpoint
- [x] Bonus Unit 3 bounded local Pokémon battle-advisor checkpoint

Hosted inference, external telemetry, adapter publication and online battle-server execution remain explicit opt-in activities.

## Test boundaries

`tests/` is deterministic and never needs credentials or network access. `tests_live/` is separate and skipped unless `RUN_HF_LIVE_TESTS=1`; live execution additionally requires `HF_TOKEN` and `HF_LIVE_INFERENCE=1`. Provider calls may consume Hugging Face credits, so live tests are never run on push.

See the [audit report](docs/AUDIT_REPORT.md) for the module inventory, implementation status, fixed defects and validation commands. Do not commit credentials or personal data.
