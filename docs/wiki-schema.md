# Wiki Schema

This repository is capture-first, but durable knowledge should not remain bundle-shaped.

## Durable unit model

- `raw/inbox/`
  - capture envelopes, bundles, playlists, pasted notes, and imported artifacts
- `raw/sources/`
  - immutable accepted source notes
- `wiki/sources/`
  - durable atomic source pages whenever possible
- `wiki/entities/`, `wiki/concepts/`, `wiki/projects/`, `wiki/repositories/`, `wiki/recipes/`, `wiki/syntheses/`
  - compiled knowledge pages

## Atomic source rule

Treat these as capture wrappers, not long-term source pages:

- multi-link notes
- X bundles
- YouTube playlists
- mixed note dumps

Preferred decomposition:

- one X or Reddit post per source page
- one YouTube video per source page
- one repository per source page
- one document per source page unless a section-level split is clearly justified

Keep the wrapper page only if it adds durable context such as playlist-level framing, bundle provenance, or operator notes.

## Required source frontmatter

```yaml
title: Example
kind: source
status: active
updated: 2026-04-17
created: 2026-04-17T10:00:00-07:00
source_type: url|file|repo|video|social
source_urls:
  - https://example.com
sources:
  - raw/sources/example.md
content_type: x_post|youtube_video|youtube_playlist|github_repo|pdf|web_page|note
source_language: en
translation_languages:
  - en
evidence_level: title|description|transcript|fulltext|multi_source
review_status: draft|accepted|needs_enrichment|rejected
promotion_ready: true|false
batch_parent: wiki/sources/example-bundle.md
duplicate_of: null
cluster_topics:
  - example-topic
```

## Evidence levels

- `title`
  - only title or headline-level evidence
- `description`
  - description, summary text, or metadata-rich evidence
- `transcript`
  - transcript or subtitle-backed evidence
- `fulltext`
  - strong document or page text extraction
- `multi_source`
  - synthesized from multiple corroborating sources

## Review status

- `draft`
  - newly captured or weakly processed
- `accepted`
  - durable and usable as a source page
- `needs_enrichment`
  - preserved, but still too weak for strong promotion
- `rejected`
  - not suitable for durable wiki inclusion

## Promotion rules

Promote a source into a higher-order page only if the evidence supports it.

Examples:

- Recipe page:
  - should have identifiable ingredients or inputs
  - should have usable method or workflow details
  - should not be created from title-only evidence
- Repository page:
  - should include enough README/docs/metadata to describe purpose and architecture
- Synthesis page:
  - should combine repeated themes across multiple atomic units
  - should not just paraphrase a single source note

## Deduplication rules

Before creating a new durable page:

- check whether the same URL or source identity already exists
- check whether the same repo or document already has a canonical page
- check whether the new content only extends an existing synthesis

If the content is not net-new durable knowledge:

- update the canonical page
- set `duplicate_of`
- link to the synthesis or canonical page instead of creating another thin page

## Synthesis rules

Synthesis should happen after atomic decomposition and deduplication.

Typical synthesis triggers:

- repeated claims or observations across 3 or more atomic units
- recurring project or repository themes
- repeated recipe or cooking patterns across related videos
- repeated social-media claims that deserve a single evidence-bounded narrative

The synthesis page should:

- name the cluster clearly
- summarize what is known
- preserve uncertainty
- link back to the atomic source pages
