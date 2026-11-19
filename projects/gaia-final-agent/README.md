# Unit 4 — GAIA certification agent

A bounded tool-calling agent for the official [Hugging Face Agents Course final assignment](https://huggingface.co/learn/agents-course/en/unit4/introduction). The scoring API evaluates 20 GAIA questions by exact match. This is an implementation, **not a completed assessment or a certificate claim**.

## Local setup

Install the optional dependencies from this folder with: `python -m pip install -r projects/gaia-final-agent/requirements.txt`.

Run the Gradio app: `python projects/gaia-final-agent/app.py`.

`AGENT_BACKEND=ollama` (default) uses local `qwen2.5:3b` on `http://127.0.0.1:11434/v1`; install/start Ollama first and optionally set `GAIA_MODEL`. For Hugging Face inference, set `AGENT_BACKEND=hf`, configure `HF_TOKEN` privately, and **explicitly** set `HF_LIVE_INFERENCE=1`. Hugging Face provider calls may incur credits. Credentials must never be committed.

Run evaluation, review its answers, then use the separate submission button with your public Space code URL. Authentication is required for live HF evaluation and all submissions. An incomplete run cannot be submitted. Offline regression tests do not access the network: `python -m unittest discover -s tests -v`.

## Hugging Face Spaces deployment

Create a **public Gradio Space** with Hugging Face OAuth enabled. Copy `app.py`, `agent.py`, `benchmark.py` and `requirements.txt` into its root; use the Space's own `README.md` with Gradio YAML metadata (`sdk: gradio`, `app_file: app.py`, `hf_oauth: true`). Add `HF_TOKEN` as a **Space secret** and the backend/model/opt-in variables as Space configuration where applicable. Use its public `/tree/main` code URL for assessment. For Ollama, run the app locally; ordinary hosted Spaces cannot reach the Ollama service on your laptop.

Supported attachments: text, CSV, JSON, Python, HTML, PDF, XLSX and DOCX. Vision/audio/video formats and some complex PDF layouts are unsupported; the agent records a failure rather than pretending to have read them. Search uses DuckDuckGo snippets rather than full source verification. Local model/provider tool-calling compatibility and benchmark accuracy are **not verified** until live tests run. Never assume a passing score.
