"""Run the Unit 2.1 flight tool with smolagents CodeAgent.

The model defaults to local Ollama. CodeAgent executes model-generated Python,
so this checkpoint uses a bounded local executor with no extra imports and only
the deterministic mock-flight tool.
"""
import importlib.util
import os
from pathlib import Path


def _load_stage_one():
    path = Path(__file__).with_name("run_agent.py")
    spec = importlib.util.spec_from_file_location("flight_tool_calling_checkpoint", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


stage_one = _load_stage_one()


def _code_agent(model):
    from smolagents import CodeAgent

    return CodeAgent(
        tools=[stage_one._load_flight_tool()],
        model=model,
        max_steps=stage_one.MAX_STEPS,
        additional_authorized_imports=[],
        executor_type="local",
    )


def build_local_agent():
    """Construct a bounded CodeAgent using the local Ollama endpoint."""
    from smolagents import OpenAIModel

    model = OpenAIModel(
        model_id=stage_one.LOCAL_MODEL_ID,
        api_base=stage_one.OLLAMA_BASE_URL,
        api_key="ollama-local",
        client_kwargs={"timeout": stage_one.LOCAL_TIMEOUT_SECONDS, "max_retries": 0},
        max_tokens=stage_one.MAX_TOKENS,
        temperature=0.0,
    )
    return _code_agent(model)


def build_hf_agent(token: str):
    """Construct the provider-backed variant after explicit credential checks."""
    if not isinstance(token, str) or not token:
        raise ValueError("A non-empty Hugging Face token is required")
    from smolagents import InferenceClientModel

    model = InferenceClientModel(
        model_id=stage_one.MODEL_ID,
        provider=stage_one.PROVIDER,
        token=token,
        timeout=stage_one.TIMEOUT_SECONDS,
        retry=True,
        requests_per_minute=10,
        max_tokens=stage_one.MAX_TOKENS,
        temperature=0.0,
    )
    return _code_agent(model)


def main() -> None:
    try:
        from dotenv import load_dotenv
        load_dotenv(Path(__file__).resolve().parents[2] / ".env", override=False)
        backend = os.environ.get("AGENT_BACKEND", "ollama").strip().lower()
        if backend == "ollama":
            stage_one.require_local_model()
            agent = build_local_agent()
        elif backend == "hf":
            agent = build_hf_agent(stage_one.require_live_credentials())
        else:
            raise ValueError("AGENT_BACKEND must be 'ollama' or 'hf'")
        print(agent.run(stage_one.request))
    except (ImportError, RuntimeError, ValueError) as exc:
        raise SystemExit(str(exc)) from exc
    except Exception as exc:
        raise SystemExit(
            f"CodeAgent inference failed ({type(exc).__name__}); no booking was attempted"
        ) from exc


if __name__ == "__main__":
    main()
