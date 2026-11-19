# Multi-Agents, MCP and Orchestration

Hands-on learning repository following the official [Hugging Face AI Agents Course](https://huggingface.co/learn/agents-course/en/unit0/introduction). Official-course checkpoints have been completed through part of Unit 2.1. A separate, unassessed Unit 4 GAIA capstone implementation is also available. Flight records are fixtures: this repository does not search live inventory or book tickets.

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
- [ ] Remaining Unit 2.1 topics (CodeAgent, retrieval, vision, multi-agent course notebooks)
- [ ] Unit 2.2 LlamaIndex
- [ ] Unit 2.3 LangGraph
- [ ] Unit 3 Agentic RAG
- [ ] Unit 4 benchmark qualification/certification (agent code implemented; score not verified)

Those unchecked units are deliberately outside the current scope.

## Test boundaries

`tests/` is deterministic and never needs credentials or network access. `tests_live/` is separate and skipped unless `RUN_HF_LIVE_TESTS=1`; live execution additionally requires `HF_TOKEN` and `HF_LIVE_INFERENCE=1`. Provider calls may consume Hugging Face credits, so live tests are never run on push.

See the [audit report](docs/AUDIT_REPORT.md) for the module inventory, implementation status, fixed defects and validation commands. Do not commit credentials or personal data.
