# Lesson 4 — Memory and planning

**Goal:** distinguish ephemeral conversation state, explicit durable preferences, and a plan of tool actions.

Run `python lessons/04-memory-and-planning/memory.py`. The example stores an aisle-seat preference **only when explicitly provided**, scoped by user ID and key, with a 30-day expiry. `recall` returns `None` after expiration; `forget` deletes the entry.

The planner first requests missing information. With complete inputs it returns a deterministic sequence ending in an approval gate; it does not execute tools or purchase tickets.

Try: ask for a plan without a date; advance the clock beyond the TTL; store preferences for two users; call `forget`; attempt to persist an inferred preference. In production, use an authenticated durable store, encryption, retention controls and an audit trail; do not place personal data in logs.
