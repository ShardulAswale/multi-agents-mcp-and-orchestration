"""Lesson 7: safe tracing and latency analysis around the real Lesson 5 agent."""
from dataclasses import dataclass
from contextlib import contextmanager
import importlib.util
import json
from pathlib import Path
import statistics
import sys
import time
import uuid

p = Path(__file__).resolve().parents[1] / "05-multi-agent-coordination/coordinator.py"
spec = importlib.util.spec_from_file_location("lesson07_coordinator", p)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


@dataclass(frozen=True)
class Span:
    trace_id: str
    name: str
    duration_ms: float
    outcome: str


class Recorder:
    """Collect minimal structured events, never raw requests or secrets."""
    def __init__(self, clock=time.perf_counter):
        self.clock = clock
        self.spans: list[Span] = []

    @contextmanager
    def span(self, trace_id: str, name: str):
        started = self.clock()
        outcome = "ok"
        try:
            yield
        except Exception:
            outcome = "error"
            raise
        finally:
            self.spans.append(Span(trace_id, name,
                                   max(0.0, (self.clock() - started) * 1000),
                                   outcome))

    def summary(self) -> dict:
        durations = sorted(s.duration_ms for s in self.spans)
        def percentile(p):
            if not durations:
                return 0.0
            # Nearest-rank percentile: works for small, deterministic datasets.
            import math
            return durations[max(0, math.ceil(p * len(durations)) - 1)]
        return {"count": len(self.spans),
                "errors": sum(s.outcome == "error" for s in self.spans),
                "p50_ms": percentile(0.50),
                "p95_ms": percentile(0.95),
                "p99_ms": percentile(0.99)}

    def to_json_lines(self) -> str:
        return "\n".join(json.dumps(s.__dict__, sort_keys=True) for s in self.spans)


class TracedSearch:
    def __init__(self, delegate, recorder, trace_id):
        self.delegate, self.recorder, self.trace_id = delegate, recorder, trace_id

    def run(self, request):
        with self.recorder.span(self.trace_id, "search"):
            return self.delegate.run(request)


class TracedRanker:
    def __init__(self, delegate, recorder, trace_id):
        self.delegate, self.recorder, self.trace_id = delegate, recorder, trace_id

    def run(self, flights):
        with self.recorder.span(self.trace_id, "rank"):
            return self.delegate.run(flights)


def run_traced(request: dict, inventory: list, recorder: Recorder,
               model_directed: bool = False) -> dict:
    """Measure coordinator and specialist operations using one trace ID."""
    trace_id = uuid.uuid4().hex
    search = TracedSearch(mod.SearchAgent(inventory), recorder, trace_id)
    rank = TracedRanker(mod.RankingAgent(), recorder, trace_id)
    agent = (mod.LLMDrivenCoordinator(search, rank, mod.demo_router)
             if model_directed else mod.DeterministicCoordinator(search, rank))
    with recorder.span(trace_id, "coordinator"):
        result = agent.run(request)
    # Return status and trace ID, not private user data or raw request.
    return {"trace_id": trace_id, "status": result["status"],
            "flight_codes": [f.code for f in result["flights"]]}


if __name__ == "__main__":
    recorder = Recorder()
    flights = [mod.Flight("A1", 160, True), mod.Flight("B2", 90, False)]
    print(run_traced({"direct_only": True}, flights, recorder))
    print(recorder.to_json_lines())
    print(recorder.summary())
