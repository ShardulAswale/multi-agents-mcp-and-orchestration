"""Lesson 5: deterministic and model-directed coordination (mock flights only).

Run: python lessons/05-multi-agent-coordination/coordinator.py
No external dependencies, API keys, purchases or network requests.
"""
from dataclasses import dataclass
import math
from collections.abc import Mapping
from typing import Callable, Literal


@dataclass(frozen=True)
class Flight:
    code: str
    price: float
    direct: bool

    def __post_init__(self) -> None:
        if not isinstance(self.code, str) or not self.code:
            raise ValueError("flight code must be a non-empty string")
        if (isinstance(self.price, bool) or not isinstance(self.price, (int, float)) or
                not math.isfinite(self.price) or self.price < 0):
            raise ValueError("flight price must be a non-negative finite number")
        if not isinstance(self.direct, bool):
            raise ValueError("direct must be a boolean")


def valid_request(request: object) -> bool:
    """Validate the narrow request schema before invoking any specialist."""
    return (isinstance(request, Mapping) and
            isinstance(request.get("direct_only", False), bool))


# Each specialist has one responsibility and a narrow, testable interface.
class SearchAgent:
    def __init__(self, flights: list[Flight]):
        self.flights = flights
        self.calls = 0

    def run(self, request: dict) -> list[Flight]:
        self.calls += 1
        # In production, replace fixtures with a validated flight-search API.
        return [f for f in self.flights if not request.get("direct_only") or f.direct]


class RankingAgent:
    def __init__(self):
        self.calls = 0

    def run(self, flights: list[Flight]) -> list[Flight]:
        self.calls += 1
        return sorted(flights, key=lambda f: (f.price, f.code))


class DeterministicCoordinator:
    """Fixed control flow: search -> early exit -> rank.

    Prefer this when the steps are known: fewer model calls, predictable
    execution, and simpler regression tests.
    """
    def __init__(self, search: SearchAgent, ranker: RankingAgent):
        self.search, self.ranker = search, ranker

    def run(self, request: dict) -> dict:
        if not valid_request(request):
            return {"status": "invalid_request", "flights": []}
        flights = self.search.run(request)
        if not flights:
            # Do NOT invoke ranking on empty results: fail early.
            return {"status": "no_flights_found", "flights": []}
        return {"status": "success", "flights": self.ranker.run(flights)}


# An LLM router returns a *proposal*, never executable Python or a tool name
# to invoke blindly. A production router could call a hosted LLM here.
Router = Callable[[dict, tuple[str, ...]], str]


class LLMDrivenCoordinator:
    """Model-selected next step, with Python enforcing a strict allowlist.

    The model can propose 'search', 'rank', or 'finish'. The coordinator
    validates each choice and prerequisites, limits steps, and prevents ranking
    without search results. The demo router below is simulated, not an LLM.
    """
    ALLOWED = ("search", "rank", "finish")

    def __init__(self, search: SearchAgent, ranker: RankingAgent,
                 router: Router, max_steps: int = 4):
        if max_steps < 1:
            raise ValueError("max_steps must be positive")
        self.search, self.ranker = search, ranker
        self.router, self.max_steps = router, max_steps

    def run(self, request: dict) -> dict:
        if not valid_request(request):
            return {"status": "invalid_request", "flights": []}
        flights = None
        ranked = None
        for _ in range(self.max_steps):
            # Never send credentials or sensitive customer data to a router.
            state = {"searched": flights is not None,
                     "has_flights": bool(flights),
                     "ranked": ranked is not None}
            choice = self.router(state, self.ALLOWED)
            if choice not in self.ALLOWED:
                return {"status": "invalid_router_choice", "flights": []}
            if choice == "search":
                if flights is not None:
                    return {"status": "duplicate_search", "flights": []}
                flights = self.search.run(request)
                if not flights:
                    return {"status": "no_flights_found", "flights": []}
            elif choice == "rank":
                if ranked is not None:
                    return {"status": "duplicate_rank", "flights": []}
                if not flights:
                    return {"status": "invalid_step_order", "flights": []}
                ranked = self.ranker.run(flights)
            else:  # finish
                if ranked is None:
                    return {"status": "premature_finish", "flights": []}
                return {"status": "success", "flights": ranked}
        return {"status": "step_limit_exceeded", "flights": []}


def demo_router(state: dict, allowed: tuple[str, ...]) -> str:
    """Offline stand-in for an LLM; swap with an actual model API adapter."""
    if not state["searched"]:
        return "search"
    if not state["ranked"]:
        return "rank"
    return "finish"


if __name__ == "__main__":
    fixtures = [Flight("AB101", 180, True), Flight("CD202", 120, False),
                Flight("EF303", 160, True)]
    for coordinator_type in ("deterministic", "model-directed demo"):
        search, ranker = SearchAgent(fixtures), RankingAgent()
        agent = (DeterministicCoordinator(search, ranker)
                 if coordinator_type == "deterministic"
                 else LLMDrivenCoordinator(search, ranker, demo_router))
        result = agent.run({"direct_only": True})
        print(coordinator_type, result["status"],
              [(f.code, f.price) for f in result["flights"]])
