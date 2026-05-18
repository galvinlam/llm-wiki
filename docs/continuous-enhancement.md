# Continuous Enhancement

## Core idea

Agents should not merely answer questions from the repo. They should continuously improve the repo.

That happens through four loops:

1. capture loop
2. ingest loop
3. query-to-writeback loop
4. lint and synthesis loop

## 1. Capture loop

Humans add content through:

- Telegram
- the `/share` web form
- SilverBullet edits
- manual file drops

All of this lands in `raw/inbox/` and `raw/assets/`.

## 2. Ingest loop

The scheduled maintainer agent reads pending inbox items and converts them into:

- immutable accepted source notes in `raw/sources/`
- decomposed atomic source pages in `wiki/sources/`
- updates to entity, concept, and project pages in `wiki/`
- entries in `wiki/log.md`

This is how raw material becomes shared knowledge.

The ingest loop should not stop at bundle-shaped pages.

It should:

- de-batch playlists, link bundles, and mixed captures into atomic units
- assign evidence level and review status
- dedupe against existing canonical pages
- hand off atomic units to synthesis and lint passes

## 3. Query-to-writeback loop

When a user asks a question:

- the query agent answers from `wiki/` first
- if the answer is durable, it gets saved to `wiki/answers/` or `wiki/syntheses/`
- `wiki/index.md` and `wiki/log.md` are updated

This turns chat into compounding memory instead of disposable output.

## 4. Lint and synthesis loop

On a schedule, the linter or maintainer agent should:

- find orphan pages
- merge duplicated concepts
- identify unsupported claims
- merge duplicate atomic source pages
- decompose leftover bundle artifacts that should not remain durable pages
- promote repeated answers into syntheses
- cluster repeated themes across atomic units
- create weekly or topical summaries

This keeps the wiki from becoming a pile of unconnected notes.

## How agents make use of the knowledge

Agents should retrieve in this order:

1. `wiki/index.md`
2. relevant `wiki/` pages
3. `raw/sources/` notes
4. `raw/assets/` files only when necessary

That means agents mostly work from compiled knowledge rather than repeatedly re-reading raw captures.

## Compounding behavior

The system improves over time because:

- captures accumulate into source records
- source records get linked into topic pages
- topic pages improve query answers
- valuable query answers get saved back into the wiki
- lint passes clean up weak structure and missing links

The result is not just storage. It is ongoing curation.
