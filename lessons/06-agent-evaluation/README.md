# Lesson 6 — Agent evaluation

## Objective
Evaluate the **actual Lesson 5 coordinator** against independent, deterministic reference cases. Distinguish a plausible answer from a correct, constraint-compliant result.

## Run
```bash
python lessons/06-agent-evaluation/evaluate.py
python -m unittest discover -s tests -v
```

## Metrics and denominators
- **Task success rate** = fully passing cases / all evaluated cases. A pass requires the expected status, exact ranked codes, hard constraints, and no unnecessary ranking on failed/empty requests.
- **Constraint satisfaction rate** = cases satisfying the direct-flight constraint / all evaluated cases. This is a separate metric; it can be high even when the task fails.
- **Tool calls** = search plus rank invocations. More calls can indicate waste.
- **Latency** = wall-clock duration per case in milliseconds. These tiny local mock runs are *not* representative of API/LLM production latency.
- **Cost** = not measured here; the offline examples have no paid model calls. Real LLM evaluation should record tokens and provider prices separately.

## What the fixtures test
Cheapest direct flight vs cheaper connection; ascending price ranking; empty inventory; no direct options; invalid flags. The simulated model-directed router is **not** a real LLM, so the results cannot establish model quality.

## Failure taxonomy
Incorrect tool parameters; provider timeout/429/503; invalid ranking; stale availability; violated hard constraints; hallucinated tool names; premature finish; duplicate tool calls; memory leakage; prompt injection; booking without approval.

## Evaluation strategy
1. Start with deterministic assertions for objective constraints, prices, ordering and statuses.
2. Add regression cases for each reproduced failure and compare baseline vs changed implementation.
3. For subjective qualities (clarity/helpfulness), a judge LLM can provide a secondary score with a rubric; calibrate against human labels and never let it override deterministic requirements.
4. On a larger test set, track p50/p95/p99 latency, failure categories, API error rate, token usage, cost per successful task, and human corrections.
5. Never treat mock flights as real-time bookability; purchases require explicit user confirmation and idempotency protection.

## Exercise
Introduce a deliberately incorrect ranking agent and observe the failure; then fix it and rerun tests. Add cases for malformed prices and provider timeouts. Compare both coordinator implementations using the same cases.

Important interfaces: `Case` stores independent ground truth; `evaluate_case(case, model_directed=False)` checks status, exact order, constraints, tool calls and latency; `evaluate_suite` aggregates rates, total calls, failed-case names and total latency. Run `python lessons/06-agent-evaluation/evaluate.py`. Empty suites return zero rates rather than dividing by zero. Common mistakes are self-grading against agent output, hiding denominators, treating constraint rate as task success, or describing the simulated router as real LLM performance. Exercises: add confidence intervals, repeated latency samples and a deliberately failing case taxonomy.
