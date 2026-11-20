"""Local GAIA evaluation CLI. Evaluation and submission are separate commands."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys

from dotenv import load_dotenv

from agent import GAIAAgent
from benchmark import answer_issue, evaluate_items, questions, submit


def load_environment() -> None:
    """Load repository-local settings without replacing explicit shell values."""
    repository_env = Path(__file__).resolve().parents[2] / ".env"
    load_dotenv(dotenv_path=repository_env, override=False)


def load_run(path: str) -> dict:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(data, list):
        data = {"results": data}
    if not isinstance(data, dict) or not isinstance(data.get("results"), list):
        raise ValueError("Answer file must contain a results list")
    return data


def save_run(path: str, results: list[dict]) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "format_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "results": results,
    }
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(destination)


def failed(result: dict) -> bool:
    return bool(result.get("error") or not str(result.get("submitted_answer", "")).strip())


def suspicious(result: dict) -> bool:
    return bool(result.get("review_warning") or answer_issue(
        str(result.get("question", "")), str(result.get("submitted_answer", ""))))


def show_progress(index: int, total: int, item: dict) -> None:
    print(f"[{index}/{total}] Running {item['task_id']}...", flush=True)


def build_agent(args):
    return GAIAAgent(model=getattr(args, "model", None))


def run_command(args) -> int:
    questions_file = getattr(args, "questions_file", None)
    attachments_dir = getattr(args, "attachments_dir", default_attachments_dir())
    skipped = set(getattr(args, "skip_task_id", None) or [])
    items = (json.loads(Path(questions_file).read_text(encoding="utf-8"))
             if questions_file else questions())
    known = {str(item.get("task_id")) for item in items}
    missing = skipped - known
    if missing:
        raise ValueError(f"Unknown task ID(s): {', '.join(sorted(missing))}")
    selected = [item for item in items if str(item.get("task_id")) not in skipped][:args.limit]
    agent = build_agent(args)
    results = []
    for index, item in enumerate(selected, start=1):
        show_progress(index, len(selected), item)
        results.extend(evaluate_items(
            agent, [item], attachment_directory=attachments_dir))
        save_run(args.output, results)
    failures = sum(failed(item) for item in results)
    print(f"Saved {len(results)} answers to {args.output}; {failures} failed.")
    return 1 if failures else 0


def review_command(args) -> int:
    results = load_run(args.answers)["results"]
    if args.failed_only:
        shown = [item for item in results if failed(item)]
    elif args.suspicious_only:
        shown = [item for item in results if suspicious(item)]
    else:
        shown = results
    for item in shown:
        status = "FAILED" if failed(item) else "ANSWERED"
        print(f"[{status}] {item.get('task_id', '<missing>')}: {item.get('question', '')}")
        if failed(item):
            print(f"  {item.get('error', 'Error')}: {item.get('error_message', 'No details recorded')}")
            if item.get("candidate_answer"):
                print(f"  REJECTED ANSWER: {item['candidate_answer']}")
        else:
            print(f"  {item.get('submitted_answer', '')}")
            issue = item.get("review_warning") or answer_issue(
                str(item.get("question", "")), str(item.get("submitted_answer", "")))
            if issue:
                print(f"  REVIEW: {issue}")
    print(f"Reviewed {len(shown)} of {len(results)} records.")
    return 1 if any(failed(item) for item in results) else 0


def retry_command(args) -> int:
    results = load_run(args.answers)["results"]
    requested = set(args.task_id or [])
    known = {str(item.get("task_id")) for item in results}
    missing = requested - known
    if missing:
        raise ValueError(f"Unknown task ID(s): {', '.join(sorted(missing))}")
    retry_records = [item for item in results if (
        str(item.get("task_id")) in requested if requested else
        failed(item) or (args.suspicious and suspicious(item)))]
    if not retry_records:
        print("No failed or empty answers to retry.")
        return 0

    if any(not item.get("question") for item in retry_records):
        official = {str(item["task_id"]): item for item in questions()}
        retry_records = [official[str(item["task_id"])] for item in retry_records]
    retried = evaluate_items(
        build_agent(args), retry_records, on_progress=show_progress,
        attachment_directory=getattr(args, "attachments_dir", default_attachments_dir()))
    previous = {str(item.get("task_id")): item for item in results}
    replacements = {}
    for item in retried:
        old = previous[item["task_id"]]
        history = list(old.get("attempt_history", []))
        snapshot = {key: old[key] for key in (
            "submitted_answer", "candidate_answer", "error", "error_message", "review_warning")
                    if old.get(key) not in (None, "")}
        if snapshot:
            history.append(snapshot)
        if history:
            item["attempt_history"] = history
        replacements[item["task_id"]] = item
    updated = [replacements.get(str(item.get("task_id")), item) for item in results]
    destination = args.output or args.answers
    save_run(destination, updated)
    failures = sum(failed(item) for item in updated)
    print(f"Retried {len(retried)} records and saved {destination}; {failures} still failed.")
    return 1 if failures else 0


def fetch_command(args) -> int:
    items = questions()
    destination = Path(args.output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(items, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Saved {len(items)} official questions to {destination}.")
    return 0


def default_attachments_dir() -> str:
    return os.environ.get(
        "GAIA_ATTACHMENTS_DIR",
        str(Path(__file__).resolve().parents[2] / ".gaia-private" / "2023" / "validation"),
    )


def submit_command(args) -> int:
    if not args.confirm_submit:
        raise ValueError("Submission requires --confirm-submit")
    results = load_run(args.answers)["results"]
    response = submit(args.username, args.code_url, results)
    print(json.dumps(response, indent=2, ensure_ascii=False))
    return 0


def parser() -> argparse.ArgumentParser:
    command = argparse.ArgumentParser(description=__doc__)
    subcommands = command.add_subparsers(dest="command", required=True)

    fetch = subcommands.add_parser("fetch", help="save the official question metadata")
    fetch.add_argument("--output", default="gaia-questions.json")
    fetch.set_defaults(handler=fetch_command)

    run = subcommands.add_parser("run", help="generate answers locally; never submits")
    run.add_argument("--limit", type=int, choices=range(1, 21), default=20,
                     metavar="1..20", help="use 1 for a trial run; default is all 20")
    run.add_argument("--output", default="gaia-answers.json")
    run.add_argument("--questions-file", help="use metadata previously saved by fetch")
    run.add_argument("--skip-task-id", action="append",
                     help="skip this task for the local run; repeatable")
    run.add_argument("--model", help="override GAIA_MODEL for this local run")
    run.add_argument("--attachments-dir", default=default_attachments_dir(),
                     help="private local GAIA attachment directory")
    run.set_defaults(handler=run_command)

    review = subcommands.add_parser("review", help="display saved answers and failures")
    review.add_argument("--answers", default="gaia-answers.json")
    review.add_argument("--failed-only", action="store_true")
    review.add_argument("--suspicious-only", action="store_true")
    review.set_defaults(handler=review_command)

    retry = subcommands.add_parser("retry", help="rerun only failed or empty answers")
    retry.add_argument("--answers", default="gaia-answers.json")
    retry.add_argument("--output", help="defaults to updating --answers atomically")
    retry.add_argument("--task-id", action="append",
                       help="retry this task even if it was recorded as answered; repeatable")
    retry.add_argument("--suspicious", action="store_true",
                       help="also retry answers flagged by conservative validation")
    retry.add_argument("--model", help="override GAIA_MODEL for this local retry")
    retry.add_argument("--attachments-dir", default=default_attachments_dir(),
                       help="private local GAIA attachment directory")
    retry.set_defaults(handler=retry_command)

    send = subcommands.add_parser("submit", help="explicitly submit locally valid reviewed answers")
    send.add_argument("--answers", default="gaia-answers.json")
    send.add_argument("--username", required=True)
    send.add_argument("--code-url", required=True,
                      help="public Hugging Face Space URL ending in /tree/main")
    send.add_argument("--confirm-submit", action="store_true",
                      help="confirm the official score/leaderboard POST")
    send.set_defaults(handler=submit_command)
    return command


def main(argv=None) -> int:
    load_environment()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    try:
        args = parser().parse_args(argv)
        return args.handler(args)
    except (OSError, ValueError, RuntimeError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
