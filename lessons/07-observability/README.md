# Lesson 7 — Observability and optimisation

**Goal:** diagnose what an agent did, where time was spent, and which steps failed, without logging sensitive requests.

Run:
```bash
python lessons/07-observability/observability.py
python -m unittest discover -s tests -v
```

The example wraps the **actual Lesson 5** coordinator with instrumented search and ranking adapters. Each run gets a unique trace ID. Individual spans record operation name, elapsed milliseconds and success/error status. Structured JSON lines make the data easy to ingest into a monitoring system. Never record API tokens, passenger details or raw prompts by default.

Important interfaces: `Recorder.span(trace_id, name)` records success or error while preserving exceptions; `summary()` calculates count, error count and nearest-rank p50/p95/p99; `to_json_lines()` emits structured events; and `run_traced(request, inventory, recorder, model_directed=False)` attaches one unique trace ID to coordinator/search/rank spans. Negative clock deltas are clamped to zero.

**Key metrics:** p50/p95/p99 operation latency (nearest-rank percentile); error count; search/rank call counts; task success (from Lesson 6); and, in production, tokens, model cost, retry rate, queue depth and cost per successful task.

**Why p95?** A mean can hide slow tail requests. For example, nine 100 ms requests and one 2,000 ms request average 290 ms, yet one customer experiences a two-second delay. Small fixture samples cannot establish reliable production percentiles.

**Optimisation discipline:** record baseline -> locate expensive or failing span -> change one variable (cache, parallelise independent work, smaller model, reduce duplicate calls) -> rerun regression suite -> compare task success, p95 latency and cost. Never optimise by skipping hard constraints or booking approval.

**Exercises:** simulate a slow search agent; compare search versus ranking durations; inject a tool exception and verify the span records an error; instrument the simulated model router; implement a real metrics backend with bounded retention and sampling. This example does not connect to a hosted LLM or live flight inventory.

Common failures include logging raw requests/secrets, generating a new trace ID per span, swallowing exceptions, mixing milliseconds and seconds, and drawing conclusions from tiny percentile samples. Empty searches intentionally omit the rank span; invalid requests contain only the coordinator span.
