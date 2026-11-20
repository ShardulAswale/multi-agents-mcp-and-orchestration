"""Unit 2.1 custom knowledge-base retrieval checkpoint."""
from __future__ import annotations

from collections import Counter
import math
import re

from smolagents import CodeAgent, OpenAIModel, Tool

LOCAL_MODEL_ID = "qwen2.5:3b"
OLLAMA_BASE_URL = "http://127.0.0.1:11434/v1"
MAX_STEPS = 3

KNOWLEDGE_BASE = [
    {
        "source": "changes-policy",
        "text": "Mock flight bookings may be changed before departure. Fare differences apply; this training project never modifies real bookings.",
    },
    {
        "source": "baggage-policy",
        "text": "The mock economy fare includes one cabin bag. Checked baggage is not represented in the fixture data.",
    },
    {
        "source": "check-in-policy",
        "text": "For the training scenario, check-in opens 24 hours before departure and closes 60 minutes before departure.",
    },
    {
        "source": "scope-policy",
        "text": "All flight records are deterministic fixtures for learning. They are not live availability and cannot be purchased.",
    },
]


def _tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.casefold())


class KnowledgeBaseTool(Tool):
    name = "search_travel_knowledge"
    description = "Retrieve source-labelled passages from the local mock-travel knowledge base."
    inputs = {
        "query": {
            "type": "string",
            "description": "A concise search query about the mock travel policies.",
        }
    }
    output_type = "string"

    def __init__(self, documents=None, limit: int = 3):
        if type(limit) is not int or not 1 <= limit <= 5:
            raise ValueError("limit must be between 1 and 5")
        self.documents = list(KNOWLEDGE_BASE if documents is None else documents)
        if not self.documents or any(
            not isinstance(item, dict)
            or not isinstance(item.get("source"), str)
            or not isinstance(item.get("text"), str)
            or not item["source"].strip()
            or not item["text"].strip()
            for item in self.documents
        ):
            raise ValueError("documents must contain non-empty source and text fields")
        self.limit = limit
        super().__init__()

    def forward(self, query: str) -> str:
        if not isinstance(query, str) or not 1 <= len(query.strip()) <= 200:
            raise ValueError("query must be between 1 and 200 characters")
        query_terms = Counter(_tokens(query))
        document_terms = [Counter(_tokens(item["text"])) for item in self.documents]
        frequencies = Counter(
            term for terms in document_terms for term in query_terms if term in terms
        )
        ranked = []
        for index, terms in enumerate(document_terms):
            score = sum(
                query_count * terms[term]
                * (math.log((len(self.documents) + 1) / (frequencies[term] + 1)) + 1)
                for term, query_count in query_terms.items()
                if term in terms
            )
            if score:
                ranked.append((score, index))
        ranked.sort(key=lambda item: (-item[0], item[1]))
        if not ranked:
            return "No relevant local passage found."
        return "\n\n".join(
            f"SOURCE: {self.documents[index]['source']}\n{self.documents[index]['text']}"
            for _, index in ranked[: self.limit]
        )


def build_local_agent():
    """Construct the retrieval agent without contacting a provider."""
    model = OpenAIModel(
        model_id=LOCAL_MODEL_ID,
        api_base=OLLAMA_BASE_URL,
        api_key="ollama-local",
        client_kwargs={"timeout": 120, "max_retries": 0},
        max_tokens=256,
        temperature=0.0,
    )
    return CodeAgent(
        tools=[KnowledgeBaseTool()],
        model=model,
        max_steps=MAX_STEPS,
        additional_authorized_imports=[],
        executor_type="local",
    )


if __name__ == "__main__":
    answer = build_local_agent().run(
        "Use the knowledge-base tool. When does check-in close? Cite the source identifier."
    )
    print(answer)
