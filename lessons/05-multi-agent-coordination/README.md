# Lesson 5 — Multi-agent coordination

## Learning objectives
Understand specialist agents, coordinator control flow, dependency injection, early exits, model-directed routing, and validation of model-proposed actions.

## Run
```bash
python lessons/05-multi-agent-coordination/coordinator.py
python -m unittest discover -s tests -v
```

## Two approaches
- **DeterministicCoordinator:** Python always searches, checks for no results, then ranks. No model cost or unpredictable routing.
- **LLMDrivenCoordinator:** a router proposes one of `search`, `rank`, `finish`. Python enforces an allowlist, prerequisites, duplicate-call protection, and a step budget. The included `demo_router` is a **simulated router**, not an actual LLM call. To connect a real model, implement the `Router` callable with your provider SDK, parse its structured output, and keep the same validation checks. This avoids credentials and network dependency in the lesson.

Important interfaces: validated `Flight` records, `SearchAgent.run(request)`, `RankingAgent.run(flights)`, `DeterministicCoordinator.run`, and `LLMDrivenCoordinator(..., router, max_steps=4)`. Call counters expose unnecessary work to tests and evaluation. `direct_only` is the intentionally narrow request schema for this lesson.

## What can go wrong?
- **Empty search results:** return `no_flights_found` without ranking.
- **Invalid request flags:** reject before tool calls.
- **Hallucinated tool names:** reject `invalid_router_choice`.
- **Rank before search / finish too early:** reject invalid transitions.
- **Infinite agent loop:** bound the number of steps.
- **Duplicate calls:** reject repeated search/rank.
- **Production considerations:** validate model JSON schema, handle provider timeouts and retries, record safe traces, enforce cost budgets, isolate user data, and require explicit approval before any booking. Never trust an LLM as the final authority on prices, constraints or payments.

## Exercise
Replace `demo_router` with a real LLM adapter; compare task success, tool-call count, latency, cost and invalid-step rate against the deterministic baseline. Add a third policy-check agent and test its prerequisites. All flights here are mock records; no booking API is used.

Also exercise premature finish, non-mapping requests, NaN prices and a two-step budget. A real router should translate provider timeouts/rate limits into a documented status or fallback policy rather than inventing a route.
