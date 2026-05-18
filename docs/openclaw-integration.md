# OpenClaw Integration

## Purpose

This project is designed so OpenClaw can operate as the intelligent layer without owning the data layer.

The repo stays the source of truth. OpenClaw receives jobs, reads and edits files here, and writes structured output files for the worker.

This is the preferred architecture. The Python app should remain lightweight and deterministic, while OpenClaw performs the hard-to-codify work such as extraction, categorization, synthesis, and wiki enhancement.

## Integration points

The maintainer worker supports three external command hooks:

- `OPENCLAW_QUERY_COMMAND`
- `OPENCLAW_INGEST_COMMAND`
- `OPENCLAW_LINT_COMMAND`

Before each command runs, the worker exports:

- `LLM_WIKI_ROOT`
- `LLM_WIKI_JOB_FILE`
- `LLM_WIKI_OUTPUT_FILE`

The command should:

1. read the job JSON from `LLM_WIKI_JOB_FILE`
2. inspect and update the repo at `LLM_WIKI_ROOT`
3. write a JSON result to `LLM_WIKI_OUTPUT_FILE`

Adapter entrypoints now live in:

- `ops/openclaw/run_query_job.py`
- `ops/openclaw/run_ingest_job.py`
- `ops/openclaw/run_lint_job.py`

Reference contract files live in:

- `openclaw/contracts/`

If `OPENCLAW_*_EXEC_COMMAND` is left blank, the adapters default to:

```bash
python3 ops/openclaw/run_openclaw_exec.py
```

You can override that when your production OpenClaw setup needs a specific profile, container, or routing command.

The shared wrapper defaults to:

```bash
openclaw agent --agent "$LLM_WIKI_OPENCLAW_AGENT_ID" --message "$LLM_WIKI_OPENCLAW_PROMPT"
```

and extracts the last valid JSON object from noisy CLI output.

The role agent ids are configured through:

- `OPENCLAW_QUERY_AGENT_ID`
- `OPENCLAW_INGEST_AGENT_ID`
- `OPENCLAW_LINT_AGENT_ID`

Use the helper script to provision them:

```bash
bash ops/scripts/setup-openclaw-agents.sh
```

## Query output contract

The query command should write JSON like:

```json
{
  "reply_markdown": "Short answer here.",
  "citations": [
    "wiki/index.md",
    "wiki/answers/example.md"
  ],
  "save_candidate": true
}
```

The worker will:

- send `reply_markdown` back to Telegram when the job came from Telegram
- cache the reply for `/save`

## Ingest output contract

The ingest command should write JSON like:

```json
{
  "summary": "Processed 4 inbox items.",
  "processed": [
    {
      "title": "Example",
      "source_note": "raw/sources/2026-04-04-example.md",
      "wiki_note": "wiki/sources/2026-04-04-example.md"
    }
  ]
}
```

The worker will:

- mark the job done
- send the summary back to Telegram if the ingest was manually requested
- queue a follow-up lint/refinement pass when accepted source notes were created or refreshed

Recommended validation path:

```bash
bash ops/scripts/test-openclaw-ingest.sh
```

## Fallback behavior

If no command hook is configured:

- query jobs use local markdown search fallback
- ingest jobs create accepted source notes plus draft source wiki pages

This means the system is usable before OpenClaw is fully wired in, but OpenClaw should replace the fallback for the actual knowledge work.

## Lint output contract

The lint command should write JSON like:

```json
{
  "summary": "Refined 3 accepted sources.",
  "touched": [
    "wiki/sources/example.md",
    "wiki/syntheses/example.md"
  ]
}
```

The worker will:

- mark the job done
- send the summary back to Telegram if the lint/refinement pass was explicitly requested
- use lint jobs both for broad maintenance and for targeted second-stage refinement of accepted source notes

## Recommended OpenClaw topology

- `telegram-agent` for query and capture interaction
- `wiki-maintainer` for scheduled ingest
- `wiki-linter` for post-ingest refinement plus periodic cleanup and improvement passes

Their responsibilities are formalized in `openclaw/skills/`.
