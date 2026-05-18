from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from common import default_openclaw_exec, load_job, repo_root, write_output


def build_prompt(root: Path, job: dict) -> str:
    return f"""You are the OpenClaw wiki-maintainer agent for the llm-wiki repository.

Repository root: {root}
Job: {json.dumps(job, indent=2)}

Required behavior:
- Read AGENTS.md, .codex/README.md, .codex/MEMORY.yaml, wiki/index.md, and wiki/log.md first.
- Inspect pending inbox items under raw/inbox/.
- Perform the real knowledge work: fetch, extract, research, categorize, de-batch, dedupe, connect, and synthesize.
- Treat bundle-like captures as wrappers, not durable source pages, whenever decomposition is possible.
- De-batch all content types when justified:
  - link bundles -> one source page per URL or per clearly justified atomic unit
  - X/Reddit/social bundles -> one source page per post
  - YouTube playlists -> one source page per video
  - multi-link notes -> one source page per source item
  - repositories -> one source page per repository plus higher-order repository/project pages when justified
  - documents -> one source page per document unless section-level decomposition clearly adds durable value
- Create accepted source notes in raw/sources/.
- Create or improve atomic source pages in wiki/sources/.
- Every source page should explicitly carry or update:
  - evidence_level: title|description|transcript|fulltext|multi_source
  - review_status: draft|accepted|needs_enrichment|rejected
  - promotion_ready: true|false
- Dedupe against existing wiki content before creating new pages.
- Merge into existing canonical pages when the new unit adds no net-new durable knowledge.
- Update related concept, entity, project, repository, recipe, answer, or synthesis pages when justified.
- Create or update synthesis pages when repeated themes appear across atomic units.
- Do not promote weak evidence into recipe/repository/synthesis pages just to increase counts.
- Update wiki/index.md and wiki/log.md.
- Move or mark processed inbox items so they are not reprocessed.
- Keep source traceability intact.
- If evidence is weak, preserve the source page and mark it needs_enrichment rather than over-promoting it.

Return JSON only with this shape:
{{
  "summary": "...",
  "processed": [
    {{
      "title": "Example",
      "source_note": "raw/sources/example.md",
      "wiki_note": "wiki/sources/example.md",
      "linked_pages": ["wiki/concepts/example.md"],
      "evidence_level": "description",
      "review_status": "accepted"
    }}
  ],
  "debatched": [
    {{
      "parent": "raw/inbox/example-bundle.md",
      "units_created": 5
    }}
  ],
  "deduped_into": [
    "wiki/sources/example-canonical.md"
  ],
  "syntheses": [
    "wiki/syntheses/example-cluster.md"
  ]
}}
"""


def main() -> int:
    root = repo_root()
    _, job = load_job()
    prompt = build_prompt(root, job)
    command = os.getenv("OPENCLAW_INGEST_EXEC_COMMAND", "").strip() or default_openclaw_exec()
    timeout_seconds = int(os.getenv("OPENCLAW_AGENT_TIMEOUT_SECONDS", "180"))
    env = os.environ.copy()
    env["LLM_WIKI_OPENCLAW_PROMPT"] = prompt
    env["LLM_WIKI_OPENCLAW_AGENT_ID"] = os.getenv("OPENCLAW_INGEST_AGENT_ID", "apoc")
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
        raise RuntimeError(f"OpenClaw ingest command timed out after {timeout_seconds} seconds") from exc
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "OpenClaw ingest command failed")
    stdout = result.stdout.strip()
    if stdout:
        try:
            write_output(json.loads(stdout))
            return 0
        except json.JSONDecodeError:
            pass
    if Path(os.environ["LLM_WIKI_OUTPUT_FILE"]).exists():
        return 0
    raise RuntimeError("OpenClaw ingest command did not produce JSON output")


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
