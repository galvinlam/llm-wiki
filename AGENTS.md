# LLM Wiki Agent Contract

This repository is a persistent wiki maintained by LLM agents on behalf of humans.

Before making changes, agents should read:

1. `README.md`
2. `.codex/README.md`
3. `.codex/MEMORY.yaml`
4. `wiki/index.md`
5. `wiki/log.md`

## Current project intent

Build a low-maintenance VPS-hosted knowledge system with:

- browser chat through Open WebUI
- browser wiki editing through SilverBullet
- mobile capture through a simple share form
- messaging capture through Telegram first
- optional WhatsApp capture through Twilio webhook
- filesystem-first durable state

Prefer simple local files and small services over platform-heavy architecture.

## Ownership rules

- Humans may add content to `raw/inbox/`, `raw/imports/`, and `raw/assets/`.
- Agents may read everything in the repository.
- Agents may write to `wiki/`, `wiki/log.md`, `wiki/index.md`, and `raw/imports/`.
- Agents must not mutate or delete files in `raw/sources/` after they are accepted.
- Agents should avoid rewriting human-authored docs in `docs/` and project ops files unless explicitly asked.

## Development rules

- Keep the stack small and maintainable.
- Prefer editing existing files over introducing new subsystems.
- Do not add a database, queue, or vector store unless the user explicitly asks for it.
- Do not build custom mobile apps for this project.
- Treat Telegram as the default chat integration.
- Treat WhatsApp as optional and operationally heavier than Telegram.
- New code should preserve the `raw/ -> wiki/ -> git` workflow.
- If durable behavior is added, document it in `.codex/MEMORY.yaml`.

## Startup workflow for new sessions

On a fresh session:

1. Read `.codex/README.md` and `.codex/MEMORY.yaml`.
2. Inspect the current project tree and any uncommitted changes.
3. Read `wiki/log.md` for the latest operational history.
4. If implementing an intake or agent workflow, confirm it still follows the ownership rules above.
5. Prefer concrete artifacts over abstract planning.

## Required ingest workflow

When processing a new item:

1. Read the newest entries in `wiki/log.md` and scan `wiki/index.md`.
2. Select one or more unprocessed files from `raw/inbox/` or `raw/imports/`.
3. De-batch the item into atomic units before promoting durable wiki pages:
   - a link bundle becomes one durable source page per URL or per clearly justified cluster
   - a playlist becomes one durable source page per video
   - a multi-link note becomes one durable source page per source item
   - a repository stays one durable source page per repository unless there is a justified project split
   - a document stays one durable source page per document unless section-level pages are clearly justified
4. Normalize each atomic unit:
   - preserve source URL, retrieval date, source language, and content type
   - preserve uploaded files and raw note provenance
   - assign explicit `evidence_level`, `review_status`, and `promotion_ready`
5. Dedupe before writing:
   - merge with existing source pages if the URL or source identity already exists
   - merge with existing entity/concept/project pages if the new unit adds no net new durable knowledge
   - link to existing syntheses instead of creating thin duplicate pages
6. Move or copy accepted source material into `raw/sources/`.
7. Update the wiki:
   - add or update atomic source pages in `wiki/sources/`
   - update relevant entity/concept/project/repository/recipe pages
   - create or update synthesis pages when repeated themes appear
   - update `wiki/index.md`
   - append an entry to `wiki/log.md`
8. If the source contradicts existing pages, explicitly note the contradiction.
9. If the source is low quality or irrelevant, log the rejection instead of forcing it into the wiki.

When processing inbound items from Telegram, WhatsApp, or the share form:

- preserve original message text and URLs
- preserve uploaded files under `raw/assets/`
- create one markdown intake note per inbound event in `raw/inbox/`
- avoid irreversible transformation at capture time
- defer scraping, OCR, transcript extraction, and summarization to later ingest passes

## Knowledge processing model

Durable knowledge should follow this shape:

1. `raw/inbox/` contains capture artifacts and batch wrappers
2. `raw/sources/` contains accepted immutable source notes
3. `wiki/sources/` contains one durable page per atomic source unit whenever possible
4. `wiki/entities/`, `wiki/concepts/`, `wiki/projects/`, `wiki/repositories/`, `wiki/recipes/`, and `wiki/syntheses/` contain compiled knowledge

Bundles are useful for capture, not for long-term knowledge.

Agents should therefore:

- treat playlists, bundles, and multi-link notes as temporary wrappers
- decompose them into atomic source units
- categorize those units
- dedupe them against existing wiki pages
- cluster repeated themes into synthesis pages
- split synthesis pages when one page starts carrying multiple distinct lanes that would be clearer as separate durable pages
- leave weak or incomplete material visibly marked instead of silently promoting it

## Query workflow

When answering questions:

1. Read `wiki/index.md` first.
2. Open only the relevant wiki pages and source notes.
3. Prefer answering from the wiki, not from latent memory.
4. Cite page paths in the answer.
5. If the answer creates durable value, write it to `wiki/answers/` or `wiki/syntheses/` and log it.

## Wiki conventions

- Markdown only.
- Use short YAML frontmatter when helpful:

```yaml
---
title: Example Page
kind: concept
status: draft
updated: 2026-04-04
sources:
  - raw/sources/2026-04-04-example.md
---
```

- Prefer one topic per page.
- Prefer links between pages instead of repeating large blocks of text.
- Keep claims tied to specific sources.
- Preserve uncertainty explicitly.
- Prefer explicit quality markers over silent ambiguity.

Useful frontmatter fields for source and synthesized pages:

```yaml
evidence_level: title|description|transcript|fulltext|multi_source
review_status: draft|accepted|needs_enrichment|rejected
promotion_ready: true|false
batch_parent: wiki/sources/example-bundle.md
duplicate_of: wiki/sources/canonical-page.md
cluster_topics:
  - example-topic
```

## Logging format

Each log entry must start with:

```md
## [YYYY-MM-DD] type | title
```

Valid `type` values:

- `ingest`
- `query`
- `lint`
- `reject`
- `maintenance`

## Lint workflow

Periodically check for:

- orphan pages
- stale claims
- missing backlinks
- duplicated concepts
- unsupported claims
- unanswered high-value questions
- batch artifacts that should have been decomposed
- atomic source pages that should have been merged
- repeated clusters that deserve a synthesis
- promoted pages whose evidence level is too weak for their page type

Write findings into `wiki/log.md` and update pages directly where appropriate.
