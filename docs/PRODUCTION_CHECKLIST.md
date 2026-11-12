# Production-readiness checklist (future implementation)

The current repository uses mock flight data. The items below are a **roadmap**, not claims that production features are already implemented.

- [ ] Define structured schemas and validate all tool parameters.
- [ ] Add per-request trace IDs, structured redacted logs and error classification.
- [ ] Introduce bounded retries with exponential backoff and jitter for transient errors; do not retry irreversible writes blindly.
- [ ] Implement request timeouts, circuit breakers and dependency health checks.
- [ ] Use asynchronous I/O for network calls, bounded queues and worker concurrency limits.
- [ ] Apply provider-aware rate limits and backpressure; communicate waiting or overload to users.
- [ ] Define cache TTLs and invalidate volatile flight prices/availability.
- [ ] Use deterministic constraint filters before ranking or presentation.
- [ ] Require explicit human confirmation for booking/payment; use idempotency keys.
- [ ] Isolate specialist agents and coordinate outputs with a common schema.
- [ ] Evaluate task success, parameter errors, p95 latency, queue depth, retry rates, cost and user corrections.
- [ ] Load-test realistic bursts; verify graceful degradation and recovery.
- [ ] Run regression tests on every change and compare accuracy before deploying optimisations.
- [ ] Protect secrets, minimise stored personal data and treat tool responses as untrusted.
