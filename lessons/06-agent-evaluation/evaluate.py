"""Lesson 6: evaluate the actual Lesson 5 coordinator with mock data.

Run: python lessons/06-agent-evaluation/evaluate.py
All results are offline fixtures, not live flight availability.
"""
from dataclasses import dataclass
import importlib.util
from pathlib import Path
import sys
import time

# Reuse the actual implementation from Lesson 5; do not reimplement it.
COORDINATOR_PATH = Path(__file__).resolve().parents[1] / "05-multi-agent-coordination/coordinator.py"
spec = importlib.util.spec_from_file_location("lesson06_coordinator_dependency", COORDINATOR_PATH)
agent_module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = agent_module
spec.loader.exec_module(agent_module)
Flight = agent_module.Flight


@dataclass(frozen=True)
class Case:
    name: str
    request: dict
    inventory: tuple[Flight, ...]
    expected_status: str
    expected_codes: tuple[str, ...]


CASES = (
    Case("cheapest_direct", {"direct_only": True},
         (Flight("CONNECT", 50, False), Flight("DIRECT", 90, True)),
         "success", ("DIRECT",)),
    Case("sort_by_price", {"direct_only": False},
         (Flight("EXPENSIVE", 200, True), Flight("CHEAP", 80, False)),
         "success", ("CHEAP", "EXPENSIVE")),
    Case("empty_inventory", {}, (), "no_flights_found", ()),
    Case("no_matching_direct", {"direct_only": True},
         (Flight("CONNECT", 50, False),), "no_flights_found", ()),
    Case("invalid_flag", {"direct_only": "yes"},
         (Flight("DIRECT", 90, True),), "invalid_request", ()),
)


def evaluate_case(case: Case, model_directed: bool = False) -> dict:
    """Use independent expectations as ground truth, not the agent's own output."""
    search = agent_module.SearchAgent(list(case.inventory))
    ranker = agent_module.RankingAgent()
    if model_directed:
        agent = agent_module.LLMDrivenCoordinator(search, ranker, agent_module.demo_router)
    else:
        agent = agent_module.DeterministicCoordinator(search, ranker)
    start = time.perf_counter()
    result = agent.run(case.request)
    elapsed_ms = (time.perf_counter() - start) * 1000
    codes = tuple(f.code for f in result["flights"])
    # Objective assertions take priority over a subjective LLM judge.
    status_ok = result["status"] == case.expected_status
    ranking_ok = codes == case.expected_codes
    direct_ok = not case.request.get("direct_only") or all(f.direct for f in result["flights"])
    # Invalid requests and empty inventories must not invoke the ranking tool.
    skip_ranking = case.expected_status != "success"
    calls_ok = not skip_ranking or ranker.calls == 0
    passed = status_ok and ranking_ok and direct_ok and calls_ok
    return {"case": case.name, "passed": passed, "status_ok": status_ok,
            "ranking_ok": ranking_ok, "direct_ok": direct_ok,
            "calls_ok": calls_ok, "search_calls": search.calls,
            "rank_calls": ranker.calls, "latency_ms": elapsed_ms}


def evaluate_suite(cases=CASES, model_directed=False) -> dict:
    """Aggregate task success and constraint satisfaction with clear denominators."""
    results = [evaluate_case(case, model_directed) for case in cases]
    total = len(results)
    return {"total": total,
            "passed": sum(r["passed"] for r in results),
            "task_success_rate": sum(r["passed"] for r in results) / total if total else 0.0,
            "constraint_satisfaction_rate": sum(r["direct_ok"] for r in results) / total if total else 0.0,
            "tool_calls": sum(r["search_calls"] + r["rank_calls"] for r in results),
            "results": results}


if __name__ == "__main__":
    for model_directed in (False, True):
        report = evaluate_suite(model_directed=model_directed)
        label = "Simulated model-directed" if model_directed else "Deterministic"
        print(f"{label}: {report['passed']}/{report['total']} passed; "
              f"task success={report['task_success_rate']:.1%}; "
              f"constraints={report['constraint_satisfaction_rate']:.1%}; "
              f"tool calls={report['tool_calls']}")
        for result in report["results"]:
            print("  ", result["case"], "PASS" if result["passed"] else "FAIL",
                  f"latency={result['latency_ms']:.3f} ms")
