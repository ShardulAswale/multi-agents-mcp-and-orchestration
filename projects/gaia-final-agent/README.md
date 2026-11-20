---
title: GAIA Unit 4 Agent
emoji: "🧠"
colorFrom: blue
colorTo: indigo
sdk: static
app_file: index.html
short_description: Local Ollama agent for the GAIA Unit 4 workflow
---

# Unit 4 — GAIA certification agent

A bounded tool-calling agent for the official [Hugging Face Agents Course final assignment](https://huggingface.co/learn/agents-course/en/unit4/introduction). The scoring API evaluates 20 GAIA questions by exact match. This is an implementation, **not a completed assessment or a certificate claim**.

## Local setup

Install the optional dependencies from this folder with: `python -m pip install -r projects/gaia-final-agent/requirements.txt`.

Start Ollama and install the default model with `ollama pull qwen2.5:latest`. The CLI retrieves the official question list, downloads attachments when present, invokes the bounded agent, and writes JSON without submitting anything:

```text
python projects/gaia-final-agent/cli.py run --limit 1 --output gaia-trial.json
python projects/gaia-final-agent/cli.py review --answers gaia-trial.json
python projects/gaia-final-agent/cli.py run --output gaia-answers.json
python projects/gaia-final-agent/cli.py review --answers gaia-answers.json --failed-only
python projects/gaia-final-agent/cli.py retry --answers gaia-answers.json
python projects/gaia-final-agent/cli.py review --answers gaia-answers.json --suspicious-only
python projects/gaia-final-agent/cli.py retry --answers gaia-answers.json --task-id TASK_ID
python projects/gaia-final-agent/cli.py retry --answers gaia-answers.json --task-id TASK_ID --model qwen2:7b
```

`fetch` can save the official question metadata without running the model. A failed attachment, invalid answer, or unsupported format is recorded with its error message in the answer JSON. Retry updates the selected file atomically, keeps prior attempts in `attempt_history`, and runs only failed, selected, or explicitly suspicious records.

If the official hostname is temporarily unavailable after a successful `fetch`, reuse the saved metadata with `run --questions-file gaia-questions.json`. The runner first checks `.gaia-private/2023/validation/` for the metadata's exact `file_name`, then falls back to the official scoring API `/files/{task_id}` route. Override the private directory with `--attachments-dir` or `GAIA_ATTACHMENTS_DIR`. Paths are traversal-checked, and `.gaia-private/` is ignored by Git. HTTP denial or network failure is recorded accurately.

`AGENT_BACKEND=ollama` (default) uses local `qwen2.5:latest` on `http://127.0.0.1:11434/v1`; install/start Ollama first and optionally set `GAIA_MODEL` or use the GAIA CLI's `--model` option. `GAIA_MAX_TOKENS` (32–2048), `GAIA_MAX_STEPS` (3–12), `GAIA_TEMPERATURE` (0–1), `GAIA_REPEAT_PENALTY` (1–2), and `GAIA_TIMEOUT_SECONDS` (10–600) are configurable in the repository-root `.env`. Repetitive or generic model output is repaired once and then rejected. For Hugging Face inference, set `AGENT_BACKEND=hf`, configure `HF_TOKEN` privately, and **explicitly** set `HF_LIVE_INFERENCE=1`. Hugging Face provider calls may incur credits. Credentials must never be committed.

Evaluation and submission are separate commands. The submission command omits failed, empty, or review-flagged records and can send a partial answer set, matching the official API. The official score still uses all 20 questions as its denominator, so missing answers score as incorrect. Offline regression tests do not access the network: `python -m unittest discover -s tests -v`.

## Certification and zero-cost publication boundary

The official scorer accepts partial answers, a Hugging Face username, and a public Hugging Face Space code URL ending in `/tree/main`. It computes the score against all 20 questions and records the leaderboard result. The course introduction says 30% or higher qualifies, while its certificate page says above 30%; because those official pages conflict, target more than 30% before using the separate certificate claim flow. The course does not document a public GitHub repository as a substitute for the Space link.

Static Spaces are free for all accounts and this folder is configured as a source-only Static Space. It displays `index.html`; the agent itself continues to run locally with Ollama. The official course does not explicitly confirm whether a source-only Static Space will satisfy any manual verification, so this route is not guaranteed even though it supplies the requested public Space code URL. Creating a Gradio or Docker Space may require a paid plan, and no paid option is required or invoked by this project.

After manually creating a public **Static** Space, install the Hub CLI, authenticate, and upload this directory to its root:

```bash
hf upload YOUR_USERNAME/YOUR_SPACE_NAME projects/gaia-final-agent . --repo-type space --exclude "*__pycache__*"
```

Alternatively, use the manually triggered GitHub Action **Publish GAIA Space** after setting a repository `HF_TOKEN` secret with permission to write to the Space. Publishing does not run evaluation or submit answers.

Only after reviewing the locally valid answers, explicitly submit them with:

```text
python projects/gaia-final-agent/cli.py submit --answers gaia-answers.json --username YOUR_USERNAME --code-url https://huggingface.co/spaces/YOUR_USERNAME/YOUR_SPACE_NAME/tree/main --confirm-submit
```

The `--confirm-submit` flag is mandatory. This command performs the official scoring/leaderboard POST and cannot identify which individual answers were wrong.

Supported attachments: text, CSV, JSON, Python source (static analysis only), HTML, PDF, XLSX, DOCX, images and audio. Python attachments are never executed. Local media uses Faster-Whisper (`GAIA_WHISPER_MODEL`, `GAIA_WHISPER_DEVICE`), Ollama vision (`GAIA_VISION_MODEL`, default `qwen2.5vl:3b`), bounded YouTube downloads/frame sampling, and Stockfish when a chess FEN is validated. Configure `GAIA_STOCKFISH_PATH` if Stockfish is not on `PATH`. Search snippets are treated as leads; source pages must verify claims. Local model accuracy is not guaranteed. Never assume a passing score or certification.
