# Evaluation, debugging and edge-case catalogue

## Example evaluation baseline
In a hypothetical 1,000-request run: 900 successes (90%); 60 incorrect tool parameters, 25 API failures and 15 incorrect rankings. Prioritise parameter failures initially if severity and repair effort are comparable. This is an illustrative dataset, **not a measured result**.

## Test matrix
| Case | Expected behaviour | Failure signal |
|---|---|---|
| "Cheapest direct flight" | Reject connecting flights even if cheaper | Constraint violation |
| Relative date / timezone / daylight saving | Resolve using user locale and explicit reference time | Wrong date |
| Missing origin or destination | Ask for clarification | Invalid tool arguments |
| Malformed price, negative price, boolean price | Reject invalid record | Ranking corruption |
| Overnight connection excluded | Reject flight crossing local date | Overnight filter failure |
| API 429 or 503 | Bounded backoff and retry when safe | Retry exhaustion |
| API timeout | Surface uncertainty; no fabricated availability | Timeout |
| Stale cached price | Refresh before recommendation/checkout | Stale data |
| Multiple agents disagree | Apply deterministic constraints; escalate consequential choices | Coordination conflict |
| Same booking request repeated | Idempotency key; never double-purchase | Duplicate booking |
| Malicious tool output / prompt injection | Treat external data as untrusted | Instruction-following breach |
| Missing or stale memory | Reconfirm preferences | Memory error |
| LLM judge disagrees with objective filter | Deterministic filter wins | Judge inconsistency |
| Optimisation changes ranking | Roll back and add regression test | Quality regression |
| Burst of 1,000 concurrent users | Bounded queue, rate limits, controlled degradation | Queue overflow |

## Trace fields
Record trace ID, request ID, stage, selected tool, validated arguments, redacted response summary, error class, retry count, start/end timestamps, latency, token counts, estimated cost, constraint-check outcome and final result. Never log API keys or unnecessary personal data.

## Metrics
- Task success rate = completed valid tasks / total tasks.
- Constraint satisfaction = outputs meeting all hard constraints / evaluated outputs.
- Tool-argument validity = valid tool calls / total tool calls.
- API error and retry rates; queue depth and queue wait.
- Latency p50/p95/p99 and cost per successful task.
- Human corrections, approval failures and duplicate-action incidents.

## Regression workflow
Reproduce -> isolate prompt/tool/data/ranking cause -> add failing test -> implement fix -> rerun unit and edge-case suite -> compare baseline metrics -> monitor after rollout. Do not use a judge LLM as the sole verifier of objective requirements.
