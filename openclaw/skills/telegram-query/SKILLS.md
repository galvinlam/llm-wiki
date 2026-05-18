# Telegram Query Skill

## Goal

Answer user questions from the repository and optionally produce durable writeback candidates.

## Read first

1. `AGENTS.md`
2. `.codex/README.md`
3. `.codex/MEMORY.yaml`
4. `wiki/index.md`
5. `wiki/log.md`

## Inputs

When used through the maintainer worker:

- read the job JSON at `LLM_WIKI_JOB_FILE`
- read and edit files under `LLM_WIKI_ROOT`
- write the result JSON to `LLM_WIKI_OUTPUT_FILE`

## Retrieval order

1. `wiki/index.md`
2. relevant pages under `wiki/`
3. relevant source notes under `raw/sources/`
4. raw assets only if required

## Requirements

- answer from the repo, not latent memory
- keep Telegram answers concise
- cite repo paths in `citations`
- do not write to the wiki unless explicitly instructed or the calling flow expects durable writeback

## Output JSON

```json
{
  "reply_markdown": "Short answer here.",
  "citations": ["wiki/index.md"],
  "save_candidate": true
}
```

## Save heuristics

Set `save_candidate` to `true` when the answer is:

- a comparison
- a synthesis
- a reusable explanation
- a decision summary

## Avoid

- broad speculative answers without citations
- mutating `raw/sources/`
- overlong Telegram responses
