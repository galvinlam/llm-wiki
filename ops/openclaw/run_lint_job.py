from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from common import default_openclaw_exec, load_job, repo_root, write_output


def build_prompt(root: Path, job: dict) -> str:
    return f"""You are the OpenClaw wiki-linter agent for the llm-wiki repository.

Repository root: {root}
Job: {json.dumps(job, indent=2)}

Required behavior:
- Read AGENTS.md, .codex/README.md, .codex/MEMORY.yaml, wiki/index.md, and wiki/log.md first.
- Find orphan pages, duplication, unsupported claims, and synthesis opportunities.
- Find bundle-shaped source pages that should have been decomposed into atomic units.
- Find duplicated atomic source pages and merge them into canonical pages when justified.
- Cluster repeated themes across any content type, not just recipes or playlists.
- When a cluster clearly contains multiple topic lanes, split it into multiple bounded syntheses instead of keeping one catch-all page.
- Prefer one synthesis per durable lane, such as weather claims, copy-trading claims, bot-tooling claims, dataset claims, or beginner-guide claims, unless the evidence genuinely belongs together.
- Improve internal linking and discoverability.
- Create or improve syntheses when repeated patterns appear across atomic units.
- Prefer updating existing syntheses over creating another thin page.
- Mark weak pages as needs_enrichment when they are preserved but still too shallow for promotion.
- Update wiki/index.md and wiki/log.md when you make durable changes.

Return JSON only with this shape:
{{
  "summary": "...",
  "touched": ["wiki/index.md", "wiki/syntheses/example.md"],
  "clusters": [
    {{
      "topic": "example-topic",
      "sources": [
        "wiki/sources/example-1.md",
        "wiki/sources/example-2.md"
      ],
      "synthesis": "wiki/syntheses/example-topic.md"
    }}
  ],
  "deduped": [
    {{
      "source": "wiki/sources/example-duplicate.md",
      "canonical": "wiki/sources/example-canonical.md"
    }}
  ]
}}
"""


def main() -> int:
    root = repo_root()
    _, job = load_job()
    prompt = build_prompt(root, job)
    command = os.getenv("OPENCLAW_LINT_EXEC_COMMAND", "").strip() or default_openclaw_exec()
    timeout_seconds = int(os.getenv("OPENCLAW_AGENT_TIMEOUT_SECONDS", "180"))
    env = os.environ.copy()
    env["LLM_WIKI_OPENCLAW_PROMPT"] = prompt
    env["LLM_WIKI_OPENCLAW_AGENT_ID"] = os.getenv("OPENCLAW_LINT_AGENT_ID", "mouse")
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
        raise RuntimeError(f"OpenClaw lint command timed out after {timeout_seconds} seconds") from exc
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "OpenClaw lint command failed")
    stdout = result.stdout.strip()
    if stdout:
        try:
            write_output(json.loads(stdout))
            return 0
        except json.JSONDecodeError:
            pass
    if Path(os.environ["LLM_WIKI_OUTPUT_FILE"]).exists():
        return 0
    raise RuntimeError("OpenClaw lint command did not produce JSON output")


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
