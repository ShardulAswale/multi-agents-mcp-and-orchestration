# 01 — Agent fundamentals

Course alignment: official Unit 1, including [Introduction to Agents](https://huggingface.co/learn/agents-course/en/unit1/introduction), the [Thought–Action–Observation cycle](https://huggingface.co/learn/agents-course/en/unit1/agent-steps-and-structure), and the [first smolagents tutorial](https://huggingface.co/learn/agents-course/en/unit1/tutorial). The repository adapts the course’s generic examples to mock flight search and does not claim the quiz, Space publication, or certification on the learner’s behalf.

## Learning objectives
- Explain the agent loop: interpret → act → observe → decide → respond.
- Distinguish LLM reasoning from deterministic computation.
- Identify when clarification or human approval is required.

## Pseudocode
```text
receive user_request
extract requirements and missing constraints
if critical information missing:
    ask user for clarification
else:
    select permitted tool
    execute tool
    validate observation
    repeat if necessary within limits
    produce grounded response
```

## Reflection
Why should an agent validate tool results instead of assuming that HTTP 200 means the user's task succeeded?

## Runnable example and important parameters

`challenges/00-first-tool/run_agent.py` builds a `ToolCallingAgent` around a typed mock-flight tool. `MODEL_ID`, `PROVIDER`, `TIMEOUT_SECONDS`, `MAX_STEPS`, and `MAX_TOKENS` make the remote boundary explicit. `require_live_credentials` requires both `HF_TOKEN` and `HF_LIVE_INFERENCE=1`; `build_agent` creates the bounded agent. The model is real, but the flights are fixtures.

Install with `python -m pip install -e ".[agents]"`. Run only after reviewing possible provider charges: set the token in your shell without printing it, set `HF_LIVE_INFERENCE=1`, then run `python challenges/00-first-tool/run_agent.py`. The normal regression suite mocks configuration and makes no network calls.

Common failures are a missing/under-scoped token, unavailable provider/model, timeout, rate limit, malformed tool proposal, or exhausting the three-step budget. The top-level handler reports the exception class without logging tokens or raw provider payloads. Exercises: lower the step limit, inject a fake model in a test, compare a tool-calling model with deterministic routing, and add a final-answer constraint check.
