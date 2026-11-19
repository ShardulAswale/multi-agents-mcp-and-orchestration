"""Official Unit 4 GAIA scoring API; no calls occur on import."""
from __future__ import annotations

from pathlib import Path
import re
import tempfile
from urllib.parse import quote, urlsplit

BASE = "https://agents-course-unit4-scoring.hf.space"
MAX_FILE_BYTES = 15_000_000


def questions() -> list[dict]:
    import requests
    response = requests.get(f"{BASE}/questions", timeout=30)
    response.raise_for_status()
    items = response.json()
    if not isinstance(items, list) or any(
        not isinstance(item, dict) or not item.get("task_id") or not item.get("question")
        for item in items
    ):
        raise ValueError("Unexpected GAIA question payload")
    return items


def attachment_for(task_id: str, file_name: str, directory: str) -> str:
    """Stream a GAIA attachment with size and path traversal protection."""
    if not re.fullmatch(r"[a-zA-Z0-9-]{1,80}", task_id):
        raise ValueError("Invalid GAIA task ID")
    name = file_name.replace("\\", "/").rsplit("/", 1)[-1]
    name = re.sub(r"[^a-zA-Z0-9_.-]", "_", name)
    if name in {"", ".", ".."}:
        raise ValueError("Invalid attachment filename")
    path = Path(directory) / f"{task_id}_{name}"
    import requests
    with requests.get(f"{BASE}/files/{quote(task_id)}", timeout=60, stream=True) as response:
        response.raise_for_status()
        size = 0
        with path.open("wb") as output:
            for chunk in response.iter_content(chunk_size=65536):
                size += len(chunk)
                if size > MAX_FILE_BYTES:
                    raise ValueError("GAIA attachment exceeds 15 MB")
                output.write(chunk)
    return str(path)


def evaluate(agent, limit: int | None = None) -> list[dict]:
    """Return answers and per-question errors; never silently submit."""
    if limit is not None and (type(limit) is not int or limit < 1 or limit > 20):
        raise ValueError("limit must be between 1 and 20")
    items = questions()
    results = []
    with tempfile.TemporaryDirectory(prefix="gaia-") as directory:
        for item in items[:limit]:
            task_id = str(item["task_id"])
            try:
                attachment = (
                    attachment_for(task_id, item["file_name"], directory)
                    if item.get("file_name") else None
                )
                answer = agent.answer(item["question"], attachment)
                if not isinstance(answer, str) or not answer.strip():
                    raise ValueError("Agent returned an empty answer")
                results.append({"task_id": task_id, "submitted_answer": answer.strip()})
            except Exception as error:
                results.append({
                    "task_id": task_id, "submitted_answer": "",
                    "error": type(error).__name__,
                })
    return results


def submit(username: str, code_url: str, answers: list[dict]) -> dict:
    """Validate an explicit user-requested submission before the POST."""
    if not isinstance(username, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,41}", username):
        raise ValueError("Invalid Hugging Face username")
    if not isinstance(code_url, str):
        raise ValueError("A public Hugging Face Space code URL is required")
    parsed = urlsplit(code_url)
    if (parsed.scheme != "https" or parsed.netloc != "huggingface.co" or
            parsed.query or parsed.fragment or
            not re.fullmatch(r"/spaces/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/tree/main/?", parsed.path)):
        raise ValueError("Provide a public Hugging Face Space /tree/main code URL")
    if not isinstance(answers, list) or len(answers) != 20:
        raise ValueError("A complete set of 20 answers is required")
    if any(not isinstance(a, dict) or not isinstance(a.get("task_id"), str)
           or not isinstance(a.get("submitted_answer"), str)
           or not a["submitted_answer"].strip() or a.get("error") for a in answers):
        raise ValueError("Failed or empty answers cannot be submitted")
    ids = [a["task_id"] for a in answers]
    if len(set(ids)) != len(ids):
        raise ValueError("Duplicate GAIA task IDs")
    import requests
    payload = {"username": username, "agent_code": code_url, "answers": [
        {"task_id": a["task_id"], "submitted_answer": a["submitted_answer"]}
        for a in answers
    ]}
    response = requests.post(f"{BASE}/submit", json=payload, timeout=90)
    response.raise_for_status()
    return response.json()
