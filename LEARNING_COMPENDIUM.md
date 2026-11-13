# AI Agent Engineering — Learning Compendium

This is the navigation hub for the existing Hugging Face AI Agents course work and the planned production-grade flight assistant. **Existing source files are preserved at their original paths.** The links below distinguish implemented code from conceptual material.

## How to study
For each stage: read the concept, inspect the linked Python code, run the test or example, change one parameter, observe the failure, and record what you learned. Never mistake mock flight records for live availability.

| Stage | Concept | Existing material | Status | Next exercise |
|---|---|---|---|---|
| 1 | Agent loop, prompts, configuration | [fundamentals](lessons/01-agent-fundamentals/README.md), [first tool](challenges/00-first-tool/run_agent.py) | Notes and runnable LLM example (requires HF_TOKEN) | Compare LLM versus deterministic routing |
| 2 | Typed tools, validation, ranking | [tool notes](lessons/02-tool-calling/README.md), [search](challenges/00-first-tool/search_flights.py), [ranker](challenges/01-flight-filtering/flight_ranker.py) | Implemented | Test invalid dates, missing inputs and direct-flight constraints |
| 3 | Reliability, retries, approval | [architecture](architecture/stage-03-reliability.md), [Python workflow](lessons/03-reliable-workflows/workflow.py), [guide](lessons/03-reliable-workflows/README.md) | Runnable mock implementation | Add jitter, idempotency and live API integration |
| 4 | Memory and planning | [architecture](architecture/stage-04-memory-planning.md), [Python memory and planner](lessons/04-memory-and-planning/memory.py), [guide](lessons/04-memory-and-planning/README.md) | Runnable in-memory implementation | Add secure persistent storage |
| 5 | Multi-agent coordination | [architecture](architecture/stage-05-multi-agent.md), [Python coordinators](lessons/05-multi-agent-coordination/coordinator.py), [lesson guide](lessons/05-multi-agent-coordination/README.md) | Runnable deterministic coordinator and simulated model-directed routing | Connect a real LLM router, add policy checks and compare cost/latency |
| 6 | Evaluation and judge checks | [evaluation guide](docs/EVALUATION_AND_EDGE_CASES.md), [Python evaluator](lessons/06-agent-evaluation/evaluate.py), [lesson guide](lessons/06-agent-evaluation/README.md) | Runnable offline evaluation with reference cases and regression tests; no LLM judge yet | Add calibrated judge and live provider metrics |
| 7 | Observability and optimisation | [evaluation guide](docs/EVALUATION_AND_EDGE_CASES.md) | Learning guide, not implementation | Add traces, latency measurements and regression tests |
| 8 | Production deployment | [deployment guide](docs/PRODUCTION_CHECKLIST.md) | Learning guide, not implementation | Add queue, rate limit, async workers and load tests |

## Existing runnable code and tests
- [smolagents example](challenges/00-first-tool/run_agent.py): LLM invokes a mock flight tool. Needs network, Hugging Face inference access and `HF_TOKEN`.
- [smolagents tool wrapper](challenges/00-first-tool/smolagents_tool.py): exposes typed flight search.
- [mock flight search](challenges/00-first-tool/search_flights.py): inspect inputs and fixtures.
- [deterministic ranking](challenges/01-flight-filtering/flight_ranker.py): rejects invalid prices and optionally excludes overnight layovers.
- [ranking tests](tests/test_flight_ranker.py), [date tests](tests/test_stage_one_date_validation.py), and [workflow/memory tests](tests/test_workflow_and_memory.py).
- [architecture walkthrough](architecture/agent-walkthrough.html): interactive local HTML; GitHub does not execute its preview.
- [capstone placeholder](projects/flight-agent/README.md): future integration point.

## Run
```bash
python -m unittest discover -s tests -v
python challenges/01-flight-filtering/flight_ranker.py
python lessons/03-reliable-workflows/workflow.py
python lessons/04-memory-and-planning/memory.py
python lessons/05-multi-agent-coordination/coordinator.py
python lessons/06-agent-evaluation/evaluate.py
# Optional, requires Hugging Face access:
# pip install -e ".[agents]"
# export HF_TOKEN=...   # use environment or a local secret manager
# python challenges/00-first-tool/run_agent.py
```

## Engineering principles
1. Validate constraints in deterministic Python, not only an LLM or judge model.
2. Reproduce a failure before editing prompts; log request, tool name, parameters, response, errors and timings, without secrets.
3. Fix the highest-impact failure class, then add regression tests.
4. Cache only appropriately fresh data; flight price and inventory change.
5. Use bounded retries, idempotency, backpressure and human approval before purchases.
6. Compare changes on task success, constraint adherence, p95 latency, tool error rate, and cost per successful task.

See [edge cases](docs/EVALUATION_AND_EDGE_CASES.md) and [production checklist](docs/PRODUCTION_CHECKLIST.md). This repository is educational and **does not book real flights**.
