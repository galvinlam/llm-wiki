from __future__ import annotations

import json
import os
import subprocess
import time
from collections import defaultdict
from pathlib import Path

from llm_wiki.automation import cache_answer, process_ingest, process_lint, process_query
from llm_wiki.config import Settings
from llm_wiki.fs import append_log, ensure_dirs, load_json, parse_markdown_note
from llm_wiki.jobs import count_jobs, create_ingest_job, create_lint_job, move_job, next_job
from llm_wiki.telegram import send_message


settings = Settings()


def load_scheduler_state(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def save_scheduler_state(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def source_batch_bucket(path: Path) -> tuple[int, str]:
    frontmatter, _body = parse_markdown_note(path)
    content_type = str(frontmatter.get("content_type") or "").lower()
    review_status = str(frontmatter.get("review_status") or "").lower()
    promotion_ready = str(frontmatter.get("promotion_ready") or "").lower()
    tags = {str(tag).lower() for tag in (frontmatter.get("tags") or [])}
    stem = path.stem.lower()

    if review_status == "needs_enrichment" or promotion_ready == "false" or "bundle" in stem or content_type.endswith("_bundle"):
        return (0, "bundle-needs-enrichment")
    if content_type.startswith("x_") or content_type.startswith("reddit_") or content_type.startswith("linkedin_") or {"x", "reddit", "social"} & tags:
        return (1, "social-clusters")
    if content_type in {"github_repo", "project_repo", "repo_doc"} or {"repo", "repository", "runbook", "ops"} & tags:
        return (2, "repositories-docs")
    if "pdf" in content_type or content_type in {"document", "glossary", "operator_manual", "runbook"}:
        return (3, "documents-pdfs")
    if content_type in {"youtube_video", "recipe_video"} or stem.startswith("youtube-playlist"):
        return (4, "youtube-corpus")
    return (5, "general-sources")


def plan_lint_batches(settings: Settings) -> list[tuple[str, list[str]]]:
    buckets: dict[tuple[int, str], list[str]] = defaultdict(list)
    for path in sorted(settings.wiki_sources_dir.glob("*.md")):
        rel = path.relative_to(settings.app_root).as_posix()
        buckets[source_batch_bucket(path)].append(rel)

    batches: list[tuple[str, list[str]]] = []
    batch_size = max(1, settings.lint_batch_size)
    for (_priority, label), paths in sorted(buckets.items(), key=lambda item: item[0]):
        if label == "bundle-needs-enrichment":
            # Keep the highest-risk pages together so mouse can repair wrappers first.
            batches.append((label, paths))
            continue
        for idx in range(0, len(paths), batch_size):
            chunk = paths[idx : idx + batch_size]
            chunk_label = label if len(paths) <= batch_size else f"{label}-{idx // batch_size + 1}"
            batches.append((chunk_label, chunk))
    return batches


def enqueue_scheduled_lint_batches(settings: Settings) -> list[dict[str, object]]:
    planned = plan_lint_batches(settings)
    if not planned:
        return []

    state = load_scheduler_state(settings.lint_scheduler_state_file)
    cursor = int(state.get("cursor", 0))
    jobs_to_queue = min(max(1, settings.lint_batches_per_interval), len(planned))
    queued: list[dict[str, object]] = []

    for offset in range(jobs_to_queue):
        label, focus_paths = planned[(cursor + offset) % len(planned)]
        create_lint_job(
            settings,
            origin="scheduler-sharded",
            requested_by=None,
            focus_paths=focus_paths,
            mode="targeted",
            batch_label=label,
        )
        queued.append({"label": label, "count": len(focus_paths)})

    save_scheduler_state(
        settings.lint_scheduler_state_file,
        {
            "cursor": (cursor + jobs_to_queue) % len(planned),
            "planned_batches": len(planned),
            "queued_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        },
    )
    return queued


def maybe_autocommit() -> None:
    if not settings.auto_commit_enabled:
        return
    subprocess.run(["/bin/bash", "ops/scripts/git-autocommit.sh"], cwd=settings.app_root, check=False)


def process_query_job() -> bool:
    pending = next_job(settings.query_pending_dir)
    if pending is None:
        return False
    running = move_job(pending, settings.query_running_dir, "running")
    payload = load_json(running)
    try:
        result = process_query(settings, running)
        done = move_job(running, settings.query_done_dir, "done", extra={"result": result})
        if payload.get("chat_id"):
            reply = result["reply_markdown"]
            citations = result.get("citations", [])
            if citations:
                reply += "\n\nSources: " + ", ".join(str(item) for item in citations)
            send_message(settings, str(payload["chat_id"]), reply[:3500])
            cache_answer(settings, str(payload["chat_id"]), str(payload["question"]), result)
        maybe_autocommit()
        return done.exists()
    except Exception as exc:
        failed = move_job(running, settings.query_failed_dir, "failed", extra={"error": str(exc)})
        if payload.get("chat_id"):
            send_message(settings, str(payload["chat_id"]), f"Query failed: {exc}")
        return failed.exists()


def process_ingest_job() -> bool:
    pending = next_job(settings.ingest_pending_dir)
    if pending is None:
        return False
    running = move_job(pending, settings.ingest_running_dir, "running")
    payload = load_json(running)
    try:
        result = process_ingest(settings, running)
        done = move_job(running, settings.ingest_done_dir, "done", extra={"result": result})
        focus_paths: list[str] = []
        for item in result.get("processed", []):
            for key in ("source_note", "wiki_note", "processed_note"):
                value = item.get(key)
                if isinstance(value, str) and value not in focus_paths:
                    focus_paths.append(value)
            for linked in item.get("linked_pages", []) or []:
                if isinstance(linked, str) and linked not in focus_paths:
                    focus_paths.append(linked)
        if settings.auto_lint_enabled and focus_paths:
            create_lint_job(settings, origin="ingest-handoff", requested_by=payload.get("requested_by"), focus_paths=focus_paths, mode="targeted")
            append_log(
                settings,
                "maintenance",
                "targeted lint queued",
                [f"- queued follow-up lint for {len(focus_paths)} path(s) after ingest handoff"],
            )
        if payload.get("requested_by"):
            send_message(settings, str(payload["requested_by"]), result["summary"])
        maybe_autocommit()
        return done.exists()
    except Exception as exc:
        failed = move_job(running, settings.ingest_failed_dir, "failed", extra={"error": str(exc)})
        if payload.get("requested_by"):
            send_message(settings, str(payload["requested_by"]), f"Ingest failed: {exc}")
        return failed.exists()


def process_lint_job() -> bool:
    pending = next_job(settings.lint_pending_dir)
    if pending is None:
        return False
    running = move_job(pending, settings.lint_running_dir, "running")
    payload = load_json(running)
    try:
        result = process_lint(settings, running)
        done = move_job(running, settings.lint_done_dir, "done", extra={"result": result})
        if payload.get("requested_by"):
            send_message(settings, str(payload["requested_by"]), result["summary"])
        maybe_autocommit()
        return done.exists()
    except Exception as exc:
        failed = move_job(running, settings.lint_failed_dir, "failed", extra={"error": str(exc)})
        if payload.get("requested_by"):
            send_message(settings, str(payload["requested_by"]), f"Lint failed: {exc}")
        return failed.exists()


def maybe_enqueue_scheduled_ingest(last_ingest_request_at: float) -> float:
    if not settings.auto_ingest_enabled:
        return last_ingest_request_at
    now_ts = time.time()
    if now_ts - last_ingest_request_at < settings.maintainer_interval_seconds:
        return last_ingest_request_at
    if not any(settings.inbox_dir.glob("*.md")):
        return last_ingest_request_at
    if count_jobs(settings.ingest_pending_dir) or count_jobs(settings.ingest_running_dir):
        return last_ingest_request_at
    create_ingest_job(settings, origin="scheduler", requested_by=None)
    append_log(
        settings,
        "maintenance",
        "scheduled ingest queued",
        [f"- scheduler detected pending inbox items and queued an ingest run at {time.strftime('%Y-%m-%d %H:%M:%S %Z')}"],
    )
    return now_ts


def maybe_enqueue_scheduled_lint(last_lint_request_at: float) -> float:
    if not settings.auto_lint_enabled:
        return last_lint_request_at
    now_ts = time.time()
    if now_ts - last_lint_request_at < settings.lint_interval_seconds:
        return last_lint_request_at
    if count_jobs(settings.lint_pending_dir) or count_jobs(settings.lint_running_dir):
        return last_lint_request_at
    if not any(settings.wiki_sources_dir.glob("*.md")):
        return last_lint_request_at
    queued = enqueue_scheduled_lint_batches(settings)
    if not queued:
        return last_lint_request_at
    summary = ", ".join(f"{item['label']} ({item['count']})" for item in queued)
    append_log(
        settings,
        "maintenance",
        "scheduled sharded lint queued",
        [
            f"- scheduler queued {len(queued)} targeted lint batch(es) at {time.strftime('%Y-%m-%d %H:%M:%S %Z')}",
            f"- batches: {summary}",
        ],
    )
    return now_ts


def main() -> None:
    ensure_dirs(settings)
    last_ingest_request_at = 0.0
    last_lint_request_at = 0.0
    while True:
        did_work = False
        last_ingest_request_at = maybe_enqueue_scheduled_ingest(last_ingest_request_at)
        last_lint_request_at = maybe_enqueue_scheduled_lint(last_lint_request_at)
        did_work = process_query_job() or did_work
        did_work = process_ingest_job() or did_work
        did_work = process_lint_job() or did_work
        if not did_work:
            time.sleep(settings.query_poll_seconds)


if __name__ == "__main__":
    main()
