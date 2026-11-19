---
title: GAIA Unit 4 Agent
emoji: "🧠"
colorFrom: blue
colorTo: indigo
sdk: gradio
app_file: app.py
python_version: "3.10"
hf_oauth: true
---

# Unit 4 — GAIA certification agent

A bounded tool-calling agent for the official [Hugging Face Agents Course final assignment](https://huggingface.co/learn/agents-course/en/unit4/introduction). The scoring API evaluates 20 GAIA questions by exact match. This is an implementation, **not a completed assessment or a certificate claim**.

## Local setup

Install the optional dependencies from this folder with: `python -m pip install -r projects/gaia-final-agent/requirements.txt`.

Run the Gradio app: `python projects/gaia-final-agent/app.py`.

`AGENT_BACKEND=ollama` (default) uses local `qwen2.5:3b` on `http://127.0.0.1:11434/v1`; install/start Ollama first and optionally set `GAIA_MODEL`. For Hugging Face inference, set `AGENT_BACKEND=hf`, configure `HF_TOKEN` privately, and **explicitly** set `HF_LIVE_INFERENCE=1`. Hugging Face provider calls may incur credits. Credentials must never be committed.

Run evaluation, review its answers, then use the separate submission button with your public Space code URL. Authentication is required for live HF evaluation and all submissions. An incomplete run cannot be submitted. Offline regression tests do not access the network: `python -m unittest discover -s tests -v`.

## Hugging Face Spaces deployment

Create a **public Gradio Space** on Hugging Face; on an eligible free account choose **ZeroGPU** hardware. This directory already contains the root-level Gradio/OAuth Space metadata in `README.md`. From the repository root, install the CLI (`python -m pip install huggingface_hub`), log in (`hf auth login`), then upload this directory to the **root** of your existing Space:

```bash
hf upload YOUR_USERNAME/YOUR_SPACE_NAME projects/gaia-final-agent . --repo-type space
```

Alternatively, use the manually triggered GitHub Action **Publish GAIA Space** after setting a repository `HF_TOKEN` secret with permission to write to the Space; enter your existing Space's `owner/name` and approve the publish confirmation. Publishing does not run evaluation or submit answers.

In the Space's **Settings → Variables and Secrets**, set `AGENT_BACKEND=hf` and `HF_LIVE_INFERENCE=1` as variables and `HF_TOKEN` as a **secret**. You may optionally set `GAIA_MODEL` to a compatible inference-provider model. The Space uses an external provider rather than the hosting GPU to run the model; ZeroGPU hosting does not make inference free. The provider can have separate quotas or fees. Use your public `https://huggingface.co/spaces/YOUR_USERNAME/YOUR_SPACE_NAME/tree/main` URL for assessment. The hosted Space cannot access Ollama running on your laptop. Confirm that the app starts and sign-in works before attempting evaluation.

Supported attachments: text, CSV, JSON, Python, HTML, PDF, XLSX and DOCX. Vision/audio/video formats and some complex PDF layouts are unsupported; the agent records a failure rather than pretending to have read them. Search uses DuckDuckGo snippets rather than full source verification. Local model/provider tool-calling compatibility and benchmark accuracy are **not verified** until live tests run. Never assume a passing score.
