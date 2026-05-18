from __future__ import annotations

import json
import os
import shlex
import sys
from pathlib import Path
from typing import Any


def require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"{name} is not set")
    return value


def load_job() -> tuple[Path, dict[str, Any]]:
    job_path = Path(require_env("LLM_WIKI_JOB_FILE"))
    return job_path, json.loads(job_path.read_text(encoding="utf-8"))


def output_path() -> Path:
    return Path(require_env("LLM_WIKI_OUTPUT_FILE"))


def repo_root() -> Path:
    return Path(require_env("LLM_WIKI_ROOT"))


def write_output(payload: dict[str, Any]) -> None:
    path = output_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def default_openclaw_exec() -> str:
    script = Path(__file__).with_name('run_openclaw_exec.py')
    return f"{shlex.quote(sys.executable)} {shlex.quote(str(script))}"
