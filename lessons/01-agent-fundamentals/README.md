# 01 — Agent fundamentals

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
