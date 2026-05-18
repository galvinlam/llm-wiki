from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from common import default_openclaw_exec, load_job, repo_root, write_output


def build_prompt(root: Path, job: dict) -> str:
    return f"""You are the OpenClaw telegram-query agent for the llm-wiki repository.

Repository root: {root}
Question: {job.get('question', '')}

Required behavior:
- Read AGENTS.md, .codex/README.md, .codex/MEMORY.yaml, wiki/index.md, and wiki/log.md first.
- Answer from repository files, not latent memory.
- Read relevant wiki pages first, then raw/sources/ only if needed.
- Keep the answer concise and cite repo paths.
- Do not modify the wiki unless explicitly asked by the user in the question.

Return JSON only with this shape:
{{
  "reply_markdown": "...",
  "citations": ["wiki/index.md"],
  "save_candidate": true
}}
"""


def main() -> int:
    root = repo_root()
    _, job = load_job()
    prompt = build_prompt(root, job)
    command = os.getenv("OPENCLAW_QUERY_EXEC_COMMAND", "").strip() or default_openclaw_exec()
    timeout_seconds = int(os.getenv("OPENCLAW_AGENT_TIMEOUT_SECONDS", "180"))
    env = os.environ.copy()
    env["LLM_WIKI_OPENCLAW_PROMPT"] = prompt
    env["LLM_WIKI_OPENCLAW_AGENT_ID"] = os.getenv("OPENCLAW_QUERY_AGENT_ID", "morpheus")
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=root,
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"OpenClaw query command timed out after {timeout_seconds} seconds") from exc
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "OpenClaw query command failed")
    stdout = result.stdout.strip()
    if stdout:
        try:
            write_output(json.loads(stdout))
            return 0
        except json.JSONDecodeError:
            pass
    if Path(os.environ["LLM_WIKI_OUTPUT_FILE"]).exists():
        return 0
    raise RuntimeError("OpenClaw query command did not produce JSON output")


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
