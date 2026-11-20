"""Unit 3 Agentic RAG checkpoint with offline and official live modes."""
from __future__ import annotations

import argparse
from collections.abc import Iterable, Mapping
from typing import Any

from smolagents import DuckDuckGoSearchTool, OpenAIModel, ToolCallingAgent, tool

LOCAL_MODEL_ID = "qwen2.5:3b"
OLLAMA_BASE_URL = "http://127.0.0.1:11434/v1"
MAX_STEPS = 3

GUESTS = {
    "ada lovelace": (
        "GUEST SOURCE: local-guest-ada\n"
        "Ada Lovelace is attending as a mathematics guest and enjoys discussing analytical engines."
    ),
    "george washington carver": (
        "GUEST SOURCE: local-guest-carver\n"
        "George Washington Carver is attending as an agricultural scientist and educator."
    ),
}

WEATHER_FIXTURES = {
    "london": "WEATHER SOURCE: local-fixture-london\nLondon fixture: cloudy, 14 C.",
    "paris": "WEATHER SOURCE: local-fixture-paris\nParis fixture: clear, 17 C.",
}

HONORIFICS = {"dr", "lady", "lord", "mr", "mrs", "ms", "prof", "sir"}
LIVE_INTENT_WORDS = {
    "current", "download", "latest", "model", "news", "search", "weather", "web"
}


def _clean(value: str, label: str) -> str:
    cleaned = value.strip()
    if not cleaned or len(cleaned) > 100:
        raise ValueError(f"{label} must be between 1 and 100 characters")
    return cleaned


def _name_tokens(value: str) -> tuple[str, ...]:
    words = (word.strip(".,").casefold() for word in value.split())
    return tuple(word for word in words if word and word not in HONORIFICS)


def load_official_guests(
    rows: Iterable[Mapping[str, Any]] | None = None,
) -> int:
    """Load the course invitee dataset into the local retrieval directory.

    Supplying rows keeps tests and private/offline use independent of the Hub.
    Without rows, this explicitly downloads ``agents-course/unit3-invitees``.
    """
    if rows is None:
        from datasets import load_dataset

        rows = load_dataset(
            "agents-course/unit3-invitees", split="train"
        )

    loaded = 0
    for row in rows:
        name = _clean(str(row.get("name", "")), "guest name")
        relation = str(row.get("relation", "")).strip()
        description = str(row.get("description", "")).strip()
        email = str(row.get("email", "")).strip()
        if not description:
            raise ValueError(f"guest {name!r} is missing a description")
        GUESTS[name.casefold()] = (
            "GUEST SOURCE: agents-course/unit3-invitees\n"
            f"Name: {name}\nRelation: {relation}\n"
            f"Description: {description}\nEmail: {email}"
        )
        loaded += 1
    return loaded


@tool
def retrieve_guest(name: str) -> str:
    """Retrieve a source-labelled guest record from the local course fixture.

    Args:
        name: Full guest name to look up.
    """
    cleaned = _clean(name, "name")
    direct = GUESTS.get(cleaned.casefold())
    if direct:
        return direct
    query_tokens = _name_tokens(cleaned)
    matches = [
        record for guest_name, record in GUESTS.items()
        if _name_tokens(guest_name) == query_tokens
    ]
    return matches[0] if len(matches) == 1 else "No matching guest record found."


def answer_guest_question(question: str) -> str | None:
    """Answer an unambiguous guest-only query without an LLM round trip."""
    cleaned = question.strip()
    if not cleaned or len(cleaned) > 1_000:
        raise ValueError("question must be between 1 and 1000 characters")
    question_tokens = set(_name_tokens(cleaned))
    if question_tokens & LIVE_INTENT_WORDS:
        return None
    matches = [
        record for name, record in GUESTS.items()
        if set(_name_tokens(name)).issubset(question_tokens)
    ]
    return matches[0] if len(matches) == 1 else None


@tool
def get_fixture_weather(city: str) -> str:
    """Return labelled training weather; this is not a live forecast.

    Args:
        city: City name for the local fixture lookup.
    """
    key = _clean(city, "city").casefold()
    return WEATHER_FIXTURES.get(key, "No local weather fixture found.")


@tool
def get_hub_stats(author: str) -> str:
    """Return the most-downloaded public Hugging Face model by an author.

    Args:
        author: Hugging Face username or organization to inspect.
    """
    from huggingface_hub import list_models

    cleaned = _clean(author, "author")
    models = list(
        list_models(author=cleaned, sort="downloads", direction=-1, limit=1)
    )
    if not models:
        return f"HUB SOURCE: huggingface.co/models?author={cleaned}\nNo models found."
    model = models[0]
    downloads = int(model.downloads or 0)
    return (
        f"HUB SOURCE: https://huggingface.co/{model.id}\n"
        f"The most downloaded model by {cleaned} is {model.id} "
        f"with {downloads:,} downloads."
    )


def build_local_agent():
    """Construct an agent that chooses between RAG and domain-specific tools."""
    model = OpenAIModel(
        model_id=LOCAL_MODEL_ID,
        api_base=OLLAMA_BASE_URL,
        api_key="ollama-local",
        client_kwargs={"timeout": 120, "max_retries": 0},
        max_tokens=256,
        temperature=0.0,
    )
    return ToolCallingAgent(
        tools=[retrieve_guest, get_fixture_weather],
        model=model,
        max_steps=MAX_STEPS,
        instructions=(
            "Use tools for guest or weather facts. Cite the returned source label. "
            "Weather values are training fixtures, never live forecasts."
        ),
    )


def build_official_agent():
    """Construct the complete official Unit 3 gala agent.

    The constructor itself is network-free. The search and Hub tools access
    public endpoints only if the model selects them during a run.
    """
    model = OpenAIModel(
        model_id=LOCAL_MODEL_ID,
        api_base=OLLAMA_BASE_URL,
        api_key="ollama-local",
        client_kwargs={"timeout": 120, "max_retries": 0},
        max_tokens=384,
        temperature=0.0,
    )
    return ToolCallingAgent(
        tools=[
            retrieve_guest,
            get_fixture_weather,
            get_hub_stats,
            DuckDuckGoSearchTool(max_results=5),
        ],
        model=model,
        max_steps=5,
        instructions=(
            "You are Alfred, the gala host. Select tools based on the question. "
            "Use guest retrieval for invitees, web search for current facts, the "
            "weather fixture only as labelled training data, and Hub stats for "
            "model popularity. Preserve source labels and never describe fixture "
            "weather as live. Every response must be a structured tool call. After "
            "receiving sufficient evidence, call final_answer exactly once; never "
            "emit unstructured prose."
        ),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the Unit 3 gala agent")
    parser.add_argument(
        "question", nargs="?", default="Tell me about Lady Ada Lovelace."
    )
    parser.add_argument(
        "--official-live",
        action="store_true",
        help="load the official guest dataset and enable public web/Hub tools",
    )
    args = parser.parse_args()
    if args.official_live:
        count = load_official_guests()
        print(f"Loaded {count} official guest records.")
        direct_answer = answer_guest_question(args.question)
        if direct_answer is not None:
            print(direct_answer)
            return 0
        agent = build_official_agent()
    else:
        agent = build_local_agent()
    print(agent.run(args.question))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
