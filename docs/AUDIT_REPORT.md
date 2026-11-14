# Repository audit and validation report

## Scope and inventory

The repository is a lesson collection rather than an importable application package. Python 3.10+ is required. Offline runtime dependencies are empty; the optional `agents` extra installs `smolagents>=1.22,<2` and its transitive Hugging Face client dependencies.

Python modules:

- `challenges/00-first-tool/search_flights.py`: deterministic mock search and parameter validation.
- `challenges/00-first-tool/smolagents_tool.py`: typed smolagents tool wrapper.
- `challenges/00-first-tool/run_agent.py`: explicit, opt-in Hugging Face `ToolCallingAgent` example.
- `challenges/01-flight-filtering/flight_ranker.py`: price and overnight-layover validation/ranking.
- `lessons/03-reliable-workflows/workflow.py`: validation, bounded retry, constraints and approval.
- `lessons/04-memory-and-planning/memory.py`: scoped expiring preferences and deterministic planning.
- `lessons/05-multi-agent-coordination/coordinator.py`: deterministic and simulated model-directed coordinators.
- `lessons/06-agent-evaluation/evaluate.py`: reference-case evaluation of the actual Lesson 5 code.
- `lessons/07-observability/observability.py`: structured spans, trace IDs and latency percentiles.

Offline test modules:

- `test_stage_one_date_validation.py`: dates, city codes, empty results and malformed records.
- `test_flight_ranker.py`: sorting, overnight filtering and invalid records/prices.
- `test_workflow_and_memory.py`: constraints, retries, approval, memory isolation/expiry and planning.
- `test_multi_agent_coordination.py`: early termination, invalid selection/order, duplicates and limits.
- `test_agent_evaluation.py`: metrics, independent references, failures and empty suites.
- `test_observability.py`: spans, errors, trace IDs, redaction and latency calculations.
- `test_hf_configuration.py`: mocked live-call gates and bounded model/agent configuration.

Optional framework tests in `tests_agents/test_smolagents_compatibility.py` execute the real decorated tool and construct the real agent without making a provider call. Push/PR CI runs these after installing the `agents` extra.

`tests_live/test_hf_inference.py` is a separate opt-in provider smoke test. Lessons 1–2 are primarily conceptual notes backed by the challenge modules; Lessons 3–7 are runnable. Architecture Markdown/HTML and the production checklist are documentation. `projects/flight-agent` is a capstone placeholder.

## Defects found and root causes

1. `pip install -e ".[agents]"` failed because setuptools interpreted multiple lesson/content directories as top-level namespace packages. `pyproject.toml` now declares a build backend and explicitly disables package discovery for this non-package lesson repository.
2. Live inference relied on changing model/provider defaults and a 120-second default timeout. It now fixes a valid public, ungated Hub model and its live `featherless-ai` provider mapping, plus a 30-second timeout, bounded rate-limit retries, token output, request rate and agent steps.
3. Possession of `HF_TOKEN` previously triggered a provider call. Live execution now also requires `HF_LIVE_INFERENCE=1`; CI requires a manual charge acknowledgement. This prevents surprise network/credit use.
4. Tool boundaries validated dates but not city codes or malformed provider records. Inputs are now normalized/validated and untrusted records cannot crash search.
5. Workflow validation did not enforce a boolean `direct_only`, and malformed search records could break sorting. Validation now occurs before search and records/IDs/stops/prices are checked independently.
6. NaN/infinite prices and malformed layovers were insufficiently covered. Rankers and `Flight` records reject non-finite, boolean, negative or structurally invalid values.
7. Memory write timestamps were checked, but naive recall timestamps raised an incidental Python comparison error. Both paths now raise a clear validation error.
8. The model-directed coordinator prevented duplicates but did not distinguish duplicate ranking in its status. Search and rank duplicates now have explicit outcomes and regression tests.
9. Evaluation omitted aggregate latency and failed-case names from the report. Both are now returned and printed.
10. Push CI did not install/validate project metadata, test the minimum Python version, run on pull requests, or compile sources. Offline CI now does all four without secrets; live inference has its own manual workflow.

## Architecture status

Implemented: request validation, mock search/ranking, deterministic coordination, bounded retries, fallback via empty-result early termination, duplicate prevention, step limits, approval gate, scoped memory, evaluation metrics and structured trace/latency recording.

Simulated: inventories, the Lesson 5 LLM router, booking boundary and evaluation workloads. The deterministic and simulated routers execute the same specialist logic, so equal fixture accuracy does not imply equal real-model quality.

Not implemented: live flight inventory, real booking/payment, durable memory, a real LLM Lesson 5 router, production telemetry backend, cost accounting, queueing/load shedding and the capstone application.

## Verification commands

```text
python -m pip install -e ".[agents]"
python -m unittest discover -s tests -v
python -m unittest discover -s tests_live -v
python lessons/03-reliable-workflows/workflow.py
python lessons/04-memory-and-planning/memory.py
python lessons/05-multi-agent-coordination/coordinator.py
python lessons/06-agent-evaluation/evaluate.py
python lessons/07-observability/observability.py
python -m compileall -q challenges lessons tests tests_live
```

The live suite should report one skipped test unless all three explicit requirements are present: `RUN_HF_LIVE_TESTS=1`, `HF_LIVE_INFERENCE=1`, and `HF_TOKEN`. Never print or commit the token.

## Final local results (2026-11-13)

- Python 3.13.14; editable installation with the `agents` extra succeeded; `pip check` found no broken requirements.
- Offline regression: 56/56 tests passed, including a second run with `python -S` to prove third-party packages are not needed.
- Lessons 3–7 and both deterministic challenge examples exited successfully; source/test compilation and `git diff --check` passed.
- Deterministic coordinator evaluation: 5/5 cases, 100% task success, 100% constraint satisfaction, 6 tool calls, no failed cases, 0.037 ms total fixture latency.
- Simulated model-directed evaluation: 5/5 cases, 100% task success, 100% constraint satisfaction, 6 tool calls, no failed cases, 0.018 ms total fixture latency.
- The latency values are single-run, in-process fixture measurements and do not establish a performance difference. The simulated router makes no LLM call, so these results say nothing about real model reliability, latency or cost.
- `HF_TOKEN` was absent locally. The live suite was therefore correctly skipped; no provider call or charge occurred. Public Hub metadata confirmed `Qwen/Qwen2.5-Coder-32B-Instruct` is a valid public, ungated text-generation model with a live `featherless-ai` conversational mapping at audit time.
- A high-confidence credential scan found no token, cloud key or private-key material. The tracked `.env.example` contains placeholders only; `.env` is ignored.
