# 02 — Tool calling and smolagents

Course alignment: the implemented subset of official Unit 2.1—[Tools](https://huggingface.co/learn/agents-course/en/unit2/smolagents/tools) and [Tool Calling Agents](https://huggingface.co/learn/agents-course/en/unit2/smolagents/tool_calling_agents). CodeAgent, retrieval, vision, multi-agent notebooks, LlamaIndex, and LangGraph are intentionally not marked complete.

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

## Implementation, parameters and edge cases

`search_flights(flights, origin, destination, date)` in `challenges/00-first-tool/search_flights.py` validates three-letter ASCII city codes, normalizes case, rejects same-city routes, validates an exact calendar date, skips malformed provider records, and returns matching mock records. `search_flights_tool` exposes that function through smolagents. `rank_flights(flights, exclude_overnight=True)` rejects malformed/non-finite prices, optionally removes overnight connections, and sorts by price.

Run `python challenges/00-first-tool/search_flights.py`, `python challenges/00-first-tool/smolagents_tool.py` (requires the `agents` extra), and `python challenges/01-flight-filtering/flight_ranker.py`. Common failures include natural-language or impossible dates, Unicode/digit city codes, malformed records, negative/boolean/NaN prices, invalid timestamps, and a departure before layover arrival. Suggested exercises: add currency conversion outside the ranker, add a duration tie-breaker, and define a typed provider-response schema without weakening the deterministic checks.
