# Challenge 01 — Flight filtering and ranking

Implement a deterministic function that returns the cheapest eligible flight while excluding overnight layovers.

## Acceptance criteria
- Reject invalid or incomplete flight records.
- Exclude flights with overnight layovers.
- Rank eligible flights by price ascending.
- Return no recommendation when none qualify.
- Unit tests cover ties, invalid prices, and overnight layovers.

Run: `python -m unittest discover -s tests -v`.

The sample uses mock data; no external API or LLM key is required.
