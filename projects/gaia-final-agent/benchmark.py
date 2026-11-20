"""Official Unit 4 GAIA scoring API; no calls occur on import."""
from __future__ import annotations

from collections import Counter
from pathlib import Path
import re
import tempfile
from urllib.parse import quote, urlsplit

BASE = "https://agents-course-unit4-scoring.hf.space"
MAX_FILE_BYTES = 15_000_000
DEFAULT_LOCAL_ATTACHMENT_DIRECTORY = (
    Path(__file__).resolve().parents[2] / ".gaia-private" / "2023" / "validation"
)


class AttachmentDownloadError(RuntimeError):
    """The official scoring service could not provide an attachment."""


class AnswerValidationError(ValueError):
    """A generated answer is unsafe to treat as completed."""


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


def _validate_items(items: list[dict]) -> None:
    if not isinstance(items, list) or any(
        not isinstance(item, dict) or not item.get("task_id") or not item.get("question")
        for item in items
    ):
        raise ValueError("Unexpected GAIA question payload")


def _stream_file(url: str, path: Path) -> str:
    import requests
    try:
        with requests.get(url, timeout=60, stream=True) as response:
            response.raise_for_status()
            size = 0
            with path.open("wb") as output:
                for chunk in response.iter_content(chunk_size=65536):
                    size += len(chunk)
                    if size > MAX_FILE_BYTES:
                        path.unlink(missing_ok=True)
                        raise ValueError("GAIA attachment exceeds 15 MB")
                    output.write(chunk)
    except requests.HTTPError as error:
        path.unlink(missing_ok=True)
        status = getattr(error.response, "status_code", "unknown")
        raise AttachmentDownloadError(
            f"Official scoring attachment endpoint returned HTTP {status}") from error
    except (requests.ConnectionError, requests.Timeout) as error:
        path.unlink(missing_ok=True)
        raise AttachmentDownloadError(
            f"Official scoring attachment endpoint unavailable: {type(error).__name__}") from error
    return str(path)


def _attachment_name(file_name: str) -> str:
    if not isinstance(file_name, str):
        raise ValueError("Invalid attachment filename")
    name = file_name.replace("\\", "/").rsplit("/", 1)[-1]
    if name != file_name or name in {"", ".", ".."} or "\x00" in name:
        raise ValueError("Invalid attachment filename")
    return name


def _local_attachment(file_name: str, directory: str | Path) -> str | None:
    root = Path(directory).expanduser().resolve()
    candidate = (root / file_name).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as error:
        raise ValueError("Invalid local attachment path") from error
    if not candidate.is_file():
        return None
    if candidate.stat().st_size > MAX_FILE_BYTES:
        raise ValueError("GAIA attachment exceeds 15 MB")
    return str(candidate)


def attachment_for(
    task_id: str,
    file_name: str,
    directory: str,
    local_directory: str | Path = DEFAULT_LOCAL_ATTACHMENT_DIRECTORY,
) -> str:
    """Use a private local attachment, or fall back to the official endpoint."""
    if not re.fullmatch(r"[a-zA-Z0-9-]{1,80}", task_id):
        raise ValueError("Invalid GAIA task ID")
    name = _attachment_name(file_name)
    local = _local_attachment(name, local_directory)
    if local is not None:
        return local
    task_directory = Path(directory) / task_id
    task_directory.mkdir(parents=True, exist_ok=False)
    path = task_directory / name
    return _stream_file(f"{BASE}/files/{quote(task_id)}", path)


def normalize_answer(question: str, answer: str) -> str:
    """Apply only formatting transformations explicitly requested by the prompt."""
    text = answer.strip().removeprefix("FINAL ANSWER:").strip()
    prompt = question.lower()
    if "response to the question" in prompt:
        quoted = re.findall(r'["“]([^"”]+)["”]', question)
        if quoted:
            words = re.findall(r"[^\W_]+", quoted[-1], flags=re.UNICODE)
            echoed = r"^\s*" + r"[\W_]+".join(map(re.escape, words)) + r"[\W_]*"
            remaining = re.sub(echoed, "", text, count=1, flags=re.IGNORECASE).strip()
            if remaining:
                text = remaining
    if "final numeric output" in prompt or prompt.lstrip().startswith("how many"):
        final = re.search(
            r"(?:\*\*)?final answer(?:\*\*)?\s*:\s*`?(-?\d+(?:\.\d+)?)`?(?:\*\*)?\s*$",
            text,
            flags=re.IGNORECASE,
        )
        if final:
            text = final.group(1)
    if "ioc" in prompt and ("country code" in prompt or "three-letter" in prompt):
        if re.fullmatch(r"[A-Za-z]{3}", text):
            text = text.upper()
    if "first name" in prompt and re.fullmatch(
            r"[^\W\d_]+(?:['’-][^\W\d_]+)*(?:\s+[^\W\d_]+(?:['’-][^\W\d_]+)*)+",
            text,
            flags=re.UNICODE):
        text = text.split()[0]
    if (("alphabetize" in prompt or "alphabetically" in prompt
         or "alphabetical order" in prompt)
            and ("list" in prompt or "ingredients" in prompt or "vegetables" in prompt)):
        items = [item.strip() for item in text.split(",") if item.strip()]
        if len(items) > 1:
            text = ", ".join(sorted(items, key=str.casefold))
    if "page numbers" in prompt and re.fullmatch(r"\s*\d+(?:\s*,\s*\d+)+\s*", text):
        text = ", ".join(str(number) for number in sorted(
            int(item.strip()) for item in text.split(",")))
    return text


def answer_issue(question: str, answer: str) -> str | None:
    """Return a general formatting or reliability failure for an exact answer."""
    text = answer.strip()
    if not text:
        return "answer is empty"
    if len(text) > 1000:
        return "answer exceeds 1,000 characters"
    words = re.findall(r"[A-Za-z0-9]+", text.lower())
    if len(words) >= 20:
        counts = Counter(words)
        trigrams = Counter(zip(words, words[1:], words[2:]))
        if max(counts.values()) > len(words) * 0.3 or max(trigrams.values(), default=0) >= 4:
            return "answer contains excessive repetition"
    lowered = text.lower()
    if any(phrase in lowered for phrase in (
            "provided information does not", "information provided does not",
            "provided evidence does not", "evidence provided does not",
            "i cannot determine", "i can't determine", "insufficient information",
            "not enough information", "unable to determine", "cannot be determined",
            "does not contain the specific information")):
        return "answer states that it could not determine a result"
    if re.search(r"\b(?:probably|possibly|perhaps|appears to be|likely)\b", lowered):
        return "answer contains an unsupported uncertainty claim"
    prompt = question.lower()
    asks_ioc_code = "ioc" in prompt and ("country code" in prompt or "three-letter" in prompt)
    if asks_ioc_code and not re.fullmatch(r"[A-Z]{3}", text):
        return "answer is not an uppercase three-letter IOC code"
    if ("final numeric output" in prompt or prompt.lstrip().startswith("how many")):
        if not re.fullmatch(r"-?\d+(?:\.\d+)?", text.replace(",", "")):
            return "answer is not numeric"
    if "how many at bats" in prompt and (not text.isdigit() or int(text) < 1):
        return "answer is not a positive at-bat count"
    if "express your answer in usd with two decimal places" in prompt:
        if not re.fullmatch(r"\$?\d[\d,]*\.\d{2}", text):
            return "answer is not a USD amount with two decimal places"
    if prompt.lstrip().startswith("who") and re.fullmatch(r"[-+]?\d+(?:\.\d+)?", text):
        return "answer is numeric where a person name is required"
    if "page numbers" in prompt:
        if not re.fullmatch(r"\d+(?:,\s*\d+)*", text):
            return "answer is not a comma-delimited page-number list"
        numbers = [int(item.strip()) for item in text.split(",")]
        if numbers != sorted(numbers) or len(numbers) != len(set(numbers)):
            return "page numbers are not unique and ascending"
    if (("alphabetize" in prompt or "alphabetically" in prompt
         or "alphabetical order" in prompt)
            and ("list" in prompt or "ingredients" in prompt or "vegetables" in prompt)):
        items = [item.strip() for item in text.split(",")]
        if len(items) < 2 or any(not item for item in items):
            return "answer is not a comma-separated list"
        if any("\n" in item or ":" in item or len(item.split()) > 6 for item in items):
            return "answer list contains prose instead of concise items"
        if len({item.casefold() for item in items}) != len(items):
            return "answer list contains duplicates"
        if items != sorted(items, key=str.casefold):
            return "answer list is not alphabetized"
    name = r"[^\W\d_]+(?:['’-][^\W\d_]+)*"
    if "first name" in prompt and not re.fullmatch(name, text):
        return "answer is not a single first name"
    if "surname" in prompt and not re.fullmatch(name, text):
        return "answer is not a single surname"
    if "last names only" in prompt:
        names = [item.strip() for item in text.split(",")]
        if len(names) != 2 or any(not re.fullmatch(name, item) for item in names):
            return "answer is not two comma-separated last names"
    if "algebraic notation" in prompt and not re.fullmatch(
            r"(?:[KQRBN])?[a-h]?[1-8]?x?[a-h][1-8](?:=[QRBN])?[+#]?|O-O(?:-O)?[+#]?", text):
        return "answer is not chess algebraic notation"
    return None


def evaluate_items(
    agent,
    items: list[dict],
    on_progress=None,
    attachment_directory: str | Path = DEFAULT_LOCAL_ATTACHMENT_DIRECTORY,
) -> list[dict]:
    """Evaluate supplied official question records without submitting them."""
    _validate_items(items)
    results = []
    with tempfile.TemporaryDirectory(prefix="gaia-") as directory:
        for index, item in enumerate(items, start=1):
            if on_progress is not None:
                on_progress(index, len(items), item)
            task_id = str(item["task_id"])
            result = {
                "task_id": task_id,
                "question": item["question"],
                "file_name": item.get("file_name") or "",
                "submitted_answer": "",
            }
            try:
                attachment = (
                    attachment_for(
                        task_id, item["file_name"], directory, attachment_directory
                    )
                    if item.get("file_name") else None
                )
                answer = agent.answer(item["question"], attachment)
                if not isinstance(answer, str):
                    raise AnswerValidationError("answer is not text")
                answer = normalize_answer(item["question"], answer)
                issue = answer_issue(item["question"], answer)
                if issue:
                    result["candidate_answer"] = answer
                    raise AnswerValidationError(issue)
                result["submitted_answer"] = answer
            except Exception as error:
                result["error"] = type(error).__name__
                result["error_message"] = str(error) or type(error).__name__
            results.append(result)
    return results


def evaluate(
    agent,
    limit: int | None = None,
    on_progress=None,
    attachment_directory: str | Path = DEFAULT_LOCAL_ATTACHMENT_DIRECTORY,
) -> list[dict]:
    """Return answers and per-question errors; never silently submit."""
    if limit is not None and (type(limit) is not int or limit < 1 or limit > 20):
        raise ValueError("limit must be between 1 and 20")
    items = questions()
    return evaluate_items(
        agent,
        items[:limit],
        on_progress=on_progress,
        attachment_directory=attachment_directory,
    )


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
    if not isinstance(answers, list):
        raise ValueError("Answers must be a list")
    if any(not isinstance(a, dict) or not isinstance(a.get("task_id"), str)
           or not isinstance(a.get("submitted_answer", ""), str) for a in answers):
        raise ValueError("Invalid answer record")
    eligible = [a for a in answers if (
        a["submitted_answer"].strip() and not a.get("error")
        and not a.get("review_warning")
        and not answer_issue(str(a.get("question", "")), a["submitted_answer"])
    )]
    if not eligible:
        raise ValueError("No valid answers are available to submit")
    ids = [a["task_id"] for a in eligible]
    if len(set(ids)) != len(ids):
        raise ValueError("Duplicate GAIA task IDs")
    import requests
    payload = {"username": username, "agent_code": code_url, "answers": [
        {"task_id": a["task_id"], "submitted_answer": a["submitted_answer"]}
        for a in eligible
    ]}
    response = requests.post(f"{BASE}/submit", json=payload, timeout=90)
    response.raise_for_status()
    return response.json()
