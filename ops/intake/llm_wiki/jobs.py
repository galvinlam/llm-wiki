from __future__ import annotations

from pathlib import Path
from typing import Any

from .config import Settings
from .fs import load_json, now, save_json, unique_stem


def _job_path(directory: Path, prefix: str) -> Path:
    return directory / f"{unique_stem(prefix)}.json"


def create_query_job(settings: Settings, question: str, origin: str, chat_id: str | None) -> Path:
    payload: dict[str, Any] = {
        "kind": "query",
        "status": "pending",
        "created": now().isoformat(),
        "origin": origin,
        "question": question,
        "chat_id": chat_id,
    }
    path = _job_path(settings.query_pending_dir, "query")
    save_json(path, payload)
    return path


def create_ingest_job(settings: Settings, origin: str, requested_by: str | None = None) -> Path:
    payload: dict[str, Any] = {
        "kind": "ingest",
        "status": "pending",
        "created": now().isoformat(),
        "origin": origin,
        "requested_by": requested_by,
    }
    path = _job_path(settings.ingest_pending_dir, "ingest")
    save_json(path, payload)
    return path


def create_lint_job(
    settings: Settings,
    origin: str,
    requested_by: str | None = None,
    focus_paths: list[str] | None = None,
    mode: str = "targeted",
    batch_label: str | None = None,
) -> Path:
    payload: dict[str, Any] = {
        "kind": "lint",
        "status": "pending",
        "created": now().isoformat(),
        "origin": origin,
        "requested_by": requested_by,
        "mode": mode,
        "focus_paths": focus_paths or [],
        "batch_label": batch_label,
    }
    path = _job_path(settings.lint_pending_dir, "lint")
    save_json(path, payload)
    return path


def next_job(directory: Path) -> Path | None:
    jobs = sorted(directory.glob("*.json"))
    return jobs[0] if jobs else None


def move_job(path: Path, target_dir: Path, status: str, extra: dict[str, Any] | None = None) -> Path:
    payload = load_json(path)
    payload["status"] = status
    payload[f"{status}_at"] = now().isoformat()
    if extra:
        payload.update(extra)
    target = target_dir / path.name
    save_json(target, payload)
    path.unlink()
    return target


def count_jobs(directory: Path) -> int:
    return len(list(directory.glob("*.json")))


def newest_job(directory: Path) -> dict[str, Any] | None:
    jobs = sorted(directory.glob("*.json"))
    if not jobs:
        return None
    return load_json(jobs[-1])
