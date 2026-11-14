# Lesson 4 — Memory and planning

**Goal:** distinguish ephemeral conversation state, explicit durable preferences, and a plan of tool actions.

Run `python lessons/04-memory-and-planning/memory.py`. The example stores an aisle-seat preference **only when explicitly provided**, scoped by user ID and key, with a 30-day expiry. `recall` returns `None` after expiration; `forget` deletes the entry.

The planner first requests missing information. With complete inputs it returns a deterministic sequence ending in an approval gate; it does not execute tools or purchase tickets.

Important interfaces: `PreferenceStore.remember(user_id, key, value, now, ttl, source)` accepts only explicit preferences, a timezone-aware clock and positive TTL; `recall(..., now=...)` deletes expired values; `forget` handles deletion; `plan_flight_search` either returns one `ask_user` action or the complete safe plan. Conversation history is not persisted by this example, so the store demonstrates long-term preference semantics while function arguments represent short-term state.

Try: ask for a plan without a date; advance the clock beyond the TTL; store preferences for two users; call `forget`; attempt to persist an inferred preference. In production, use an authenticated durable store, encryption, retention controls and an audit trail; do not place personal data in logs.

Common failures are naive timestamps, non-positive TTLs, inferred preferences, missing plan inputs and stale values. Exercises: add per-user deletion, serialize only non-sensitive preferences, test two timezones representing the same instant, and add consent/audit metadata.
