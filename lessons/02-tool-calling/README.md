# 02 — Tool calling and smolagents

A tool has a name, description, typed inputs, and an implementation. The model chooses arguments; Python validates and executes them.

## Example pseudocode
```text
LLM extracts origin, destination, date and constraints
if required inputs missing: request clarification
call search_and_rank_flights(parameters)
tool searches, validates, filters and ranks
LLM explains only the returned eligible options
```

## Architecture notes
- CodeAgent generates executable Python; run only with appropriate sandboxing and permissions.
- ToolCallingAgent emits structured tool calls.
- Keep search and ranking modular internally; expose a combined tool when predictable execution matters.
- Avoid secrets in logs and source control.
