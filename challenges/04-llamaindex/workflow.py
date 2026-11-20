"""Unit 2.2 LlamaIndex tool and event-driven workflow checkpoint."""
from __future__ import annotations

import asyncio
from collections import Counter
import hashlib
import math
import re
from typing import Any

from llama_index.core import Document, VectorStoreIndex
from llama_index.core.embeddings import BaseEmbedding
from llama_index.core.tools import FunctionTool
from llama_index.core.workflow import Event, StartEvent, StopEvent, Workflow, step

LOCAL_MODEL_ID = "qwen2.5:3b"
OLLAMA_BASE_URL = "http://127.0.0.1:11434"

DOCUMENTS = (
    ("travel-policy", "Mock reservations can be changed before departure; fare differences apply."),
    ("baggage-policy", "The mock economy fare includes one cabin bag and no checked bag."),
    ("check-in-policy", "Training check-in closes sixty minutes before departure."),
)


def _tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.casefold())


class HashEmbedding(BaseEmbedding):
    """Deterministic local bag-of-words embedding with no model download."""

    embed_dim: int = 128

    @classmethod
    def class_name(cls) -> str:
        return "course_hash_embedding"

    def _embed(self, text: str) -> list[float]:
        vector = [0.0] * self.embed_dim
        for token, count in Counter(_tokens(text)).items():
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.embed_dim
            sign = 1.0 if digest[4] & 1 else -1.0
            vector[index] += sign * count
        magnitude = math.sqrt(sum(value * value for value in vector))
        return [value / magnitude for value in vector] if magnitude else vector

    def _get_query_embedding(self, query: str) -> list[float]:
        return self._embed(query)

    def _get_text_embedding(self, text: str) -> list[float]:
        return self._embed(text)

    async def _aget_query_embedding(self, query: str) -> list[float]:
        return self._embed(query)


def build_document_index(records=DOCUMENTS) -> VectorStoreIndex:
    """Embed validated source-labelled documents entirely offline."""
    records = tuple(records)
    if not records or any(
        not isinstance(item, (tuple, list)) or len(item) != 2
        or not all(isinstance(value, str) and value.strip() for value in item)
        for item in records
    ):
        raise ValueError("records must contain non-empty (source, text) pairs")
    documents = [
        Document(text=text, metadata={"source": source}) for source, text in records
    ]
    return VectorStoreIndex.from_documents(documents, embed_model=HashEmbedding())


def build_query_engine(records=DOCUMENTS, llm: Any | None = None):
    """Create the course QueryEngine over locally embedded documents."""
    records = tuple(records)
    if llm is None:
        from llama_index.llms.ollama import Ollama
        llm = Ollama(
            model=LOCAL_MODEL_ID, base_url=OLLAMA_BASE_URL,
            request_timeout=120, temperature=0.0,
            additional_kwargs={"num_predict": 256, "repeat_penalty": 1.1},
        )
    return build_document_index(records).as_query_engine(
        llm=llm, similarity_top_k=min(3, len(records)),
        response_mode="tree_summarize",
    )


def build_local_rag_agent(records=DOCUMENTS):
    """Wrap the local QueryEngine as a tool selected by an Ollama agent."""
    from llama_index.core.agent.workflow import AgentWorkflow
    from llama_index.core.tools import QueryEngineTool
    from llama_index.llms.ollama import Ollama

    llm = Ollama(
        model=LOCAL_MODEL_ID, base_url=OLLAMA_BASE_URL,
        request_timeout=120, temperature=0.0,
        additional_kwargs={"num_predict": 256, "repeat_penalty": 1.1},
    )
    tool = QueryEngineTool.from_defaults(
        query_engine=build_query_engine(records, llm=llm),
        name="travel_policy_query",
        description="Answer questions using the source-labelled local travel policies.",
        return_direct=False,
    )
    return AgentWorkflow.from_tools_or_functions(
        [tool], llm=llm,
        system_prompt="Use travel_policy_query for policy facts and cite its source metadata.",
        timeout=120, verbose=False,
    )


def calculate_total(unit_price: float, quantity: int) -> float:
    """Calculate a fixture order total from a unit price and positive quantity."""
    if unit_price < 0 or type(quantity) is not int or quantity < 1:
        raise ValueError("unit_price must be non-negative and quantity must be positive")
    return round(unit_price * quantity, 2)


total_tool = FunctionTool.from_defaults(fn=calculate_total)


class ValidatedOrder(Event):
    unit_price: float
    quantity: int


class OrderWorkflow(Workflow):
    @step
    async def validate(self, ev: StartEvent) -> ValidatedOrder:
        price = float(ev.unit_price)
        quantity = int(ev.quantity)
        calculate_total(price, quantity)
        return ValidatedOrder(unit_price=price, quantity=quantity)

    @step
    async def total(self, ev: ValidatedOrder) -> StopEvent:
        return StopEvent(result=calculate_total(ev.unit_price, ev.quantity))


async def run_order_workflow(unit_price: float, quantity: int) -> float:
    return await OrderWorkflow(timeout=10, verbose=False).run(
        unit_price=unit_price, quantity=quantity
    )


def build_local_agent():
    """Construct a LlamaIndex tool agent backed by local Ollama."""
    from llama_index.core.agent.workflow import AgentWorkflow
    from llama_index.llms.ollama import Ollama

    llm = Ollama(
        model=LOCAL_MODEL_ID,
        base_url=OLLAMA_BASE_URL,
        request_timeout=120,
        temperature=0.0,
        additional_kwargs={"num_predict": 256, "repeat_penalty": 1.1},
    )
    return AgentWorkflow.from_tools_or_functions(
        [total_tool],
        llm=llm,
        system_prompt="Use calculate_total for arithmetic and return its result.",
        timeout=120,
        verbose=False,
    )


if __name__ == "__main__":
    print(asyncio.run(run_order_workflow(19.99, 2)))
