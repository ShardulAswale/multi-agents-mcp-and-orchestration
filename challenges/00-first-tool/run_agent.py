"""Run a first LLM-driven flight search with smolagents.

Install: pip install -e ".[agents]"
Run: python challenges/00-first-tool/run_agent.py

Defaults to free local inference through Ollama. Set AGENT_BACKEND=hf only when
you explicitly want Hugging Face routed inference, which may consume credits.
The flights themselves are mock records, not live availability.
"""
import os
import importlib.util
import json
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

MODEL_ID = "Qwen/Qwen2.5-Coder-32B-Instruct"
# Verified against the public Hub inference-provider mapping for MODEL_ID.
PROVIDER = "featherless-ai"
TIMEOUT_SECONDS = 30
LOCAL_TIMEOUT_SECONDS = 120
MAX_STEPS = 3
MAX_TOKENS = 256
LOCAL_MODEL_ID = "qwen2.5:3b"
OLLAMA_BASE_URL = "http://127.0.0.1:11434/v1"

request = (
    "Find flights from London (LON) to Paris (PAR) on 2026-12-01. "
    "Only report results returned by the tool; these are mock flights, "
    "not bookable live flights. After searching, call final_answer with a "
    "concise summary of the returned flights. If there are no results, say so."
)


def require_live_credentials(environment=os.environ) -> str:
    """Require both a token and an explicit cost/network opt-in.

    A token alone is deliberately insufficient: inference provider calls can
    consume account credits. The token value is returned but never logged.
    """
    token = environment.get("HF_TOKEN")
    if not token:
        raise RuntimeError("HF_TOKEN is not set")
    if environment.get("HF_LIVE_INFERENCE") != "1":
        raise RuntimeError("Set HF_LIVE_INFERENCE=1 to opt in to a live provider call")
    return token


def _load_flight_tool():
    tool_path = Path(__file__).with_name("smolagents_tool.py")
    spec = importlib.util.spec_from_file_location("flight_tool_stage_one", tool_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.search_flights_tool


def build_agent(token: str):
    """Build a bounded, explicitly configured Hugging Face tool agent."""
    if not isinstance(token, str) or not token:
        raise ValueError("A non-empty Hugging Face token is required")

    from smolagents import InferenceClientModel, ToolCallingAgent

    model = InferenceClientModel(
        model_id=MODEL_ID,
        provider=PROVIDER,
        token=token,
        timeout=TIMEOUT_SECONDS,
        retry=True,  # smolagents bounds rate-limit retries internally.
        requests_per_minute=10,
        max_tokens=MAX_TOKENS,
        temperature=0.0,
    )
    return ToolCallingAgent(
        tools=[_load_flight_tool()],
        model=model,
        max_steps=MAX_STEPS,
    )


def build_local_agent():
    """Build a no-provider-charge agent against Ollama's local API."""
    from smolagents import OpenAIModel, ToolCallingAgent

    model = OpenAIModel(
        model_id=LOCAL_MODEL_ID,
        api_base=OLLAMA_BASE_URL,
        api_key="ollama-local",
        client_kwargs={"timeout": LOCAL_TIMEOUT_SECONDS, "max_retries": 0},
        max_tokens=MAX_TOKENS,
        temperature=0.0,
    )
    return ToolCallingAgent(
        tools=[_load_flight_tool()], model=model, max_steps=MAX_STEPS)


def require_local_model() -> None:
    """Give actionable setup errors before starting the agent loop."""
    try:
        with urlopen("http://127.0.0.1:11434/api/tags", timeout=3) as response:
            payload = json.load(response)
    except (OSError, URLError, TimeoutError, ValueError) as exc:
        raise RuntimeError("Ollama is not running; start it with: ollama serve") from exc
    names = {item.get("name") for item in payload.get("models", [])}
    if LOCAL_MODEL_ID not in names:
        raise RuntimeError(f"Local model is missing; install it with: ollama pull {LOCAL_MODEL_ID}")


def main() -> None:
    try:
        try:
            from dotenv import load_dotenv
        except ImportError as exc:
            raise RuntimeError('Install the agent dependencies with: pip install -e ".[agents]"') from exc
        # Prefer already-exported variables and load the ignored repository
        # .env only for local execution. Values are never printed.
        load_dotenv(Path(__file__).resolve().parents[2] / ".env", override=False)
        backend = os.environ.get("AGENT_BACKEND", "ollama").strip().lower()
        if backend == "ollama":
            require_local_model()
            result = build_local_agent().run(request)
        elif backend == "hf":
            token = require_live_credentials()
            result = build_agent(token).run(request)
        else:
            raise ValueError("AGENT_BACKEND must be 'ollama' or 'hf'")
    except (RuntimeError, ValueError) as exc:
        raise SystemExit(str(exc)) from exc
    except Exception as exc:
        # Provider exception messages can contain request metadata. Report only
        # the class and keep credentials/raw payloads out of logs.
        raise SystemExit(
            f"Agent inference failed ({type(exc).__name__}); no booking was attempted"
        ) from exc
    print(result)


if __name__ == "__main__":
    main()
