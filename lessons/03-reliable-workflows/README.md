# Lesson 3 — Reliable workflows

**Goal:** separate the agent's proposed tool calls from deterministic enforcement of constraints.

Run `python lessons/03-reliable-workflows/workflow.py` from the repository root. The example uses an injected mock search and performs **no real booking**.

The flow is **validate → bounded retry of read-only search → filter hard constraints → rank → require explicit approval before any future purchase**. A cheaper connecting flight is correctly excluded when direct-only is requested.

Important interfaces: `Request` holds route/date/budget/direct-only constraints; `validate` rejects invalid values before search; `search_with_retry(search, request, attempts=3, sleep=...)` retries only `TransientSearchError`; `recommend` treats tool output as untrusted; and `require_booking_approval(approved)` is the human gate. The injected `sleep` keeps tests fast and deterministic.

Explore: change the budget to 50; make the search raise `TransientSearchError` twice; replace it with `ValueError` to observe that non-transient failures are not retried; change `direct_only` to false. Compare failure handling and retry counts.

**Edge cases:** malformed dates, matching origin and destination, boolean/NaN prices, wrong route, stale data, zero results, provider 429/503, and accidental double booking. This lesson demonstrates bounded retries but does not implement idempotent payments, jitter, or live API access.

Common failure signals are a `ValueError` before any tool call, a propagated permanent error, or retry exhaustion after the configured attempt count. Exercises: record attempt counts, add jitter with a seeded random source, add a total deadline, and design an idempotency key for a hypothetical booking call.
