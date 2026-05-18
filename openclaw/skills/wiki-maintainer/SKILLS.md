# Wiki Maintainer Skill

## Goal

Continuously transform inbox captures into durable, connected knowledge.

## Read first

1. `AGENTS.md`
2. `.codex/README.md`
3. `.codex/MEMORY.yaml`
4. `wiki/index.md`
5. `wiki/log.md`

## Inputs

When used through the maintainer worker:

- read the job JSON at `LLM_WIKI_JOB_FILE`
- inspect pending files under `raw/inbox/`
- write output JSON to `LLM_WIKI_OUTPUT_FILE`

## Required workflow

1. select a small batch of inbox items
2. de-batch captures into atomic source units before creating durable wiki pages
3. normalize each accepted atomic unit into accepted source notes under `raw/sources/`
4. create or improve atomic source pages under `wiki/sources/`
5. assign explicit `evidence_level`, `review_status`, and `promotion_ready`
6. dedupe those units against existing source, concept, entity, project, repository, recipe, answer, and synthesis pages
7. update relevant entity, concept, project, answer, or synthesis pages
8. update `wiki/index.md`
9. append a durable entry to `wiki/log.md`
10. move or otherwise mark processed inbox items so they are not reprocessed

## Enhancement responsibility

Do not stop at copying captures into source notes.

The maintainer should also:

- fetch and inspect linked sources when needed
- perform extraction and research that would be cumbersome to hardcode
- turn bundles into atomic source notes instead of preserving bundle-shaped durable pages
- connect new material to existing wiki pages
- extract key claims and open questions
- note contradictions
- merge duplicate pages when justified
- create syntheses when repeated topics appear
- refuse promotion when evidence is too weak and mark the page `needs_enrichment` instead

The platform is intentionally thin. This role is expected to do the heavy lifting.

## Output JSON

```json
{
  "summary": "Processed 3 inbox items into 11 atomic source units.",
  "processed": [
    {
      "title": "Example",
      "source_note": "raw/sources/example.md",
      "wiki_note": "wiki/sources/example.md",
      "evidence_level": "description",
      "review_status": "accepted"
    }
  ],
  "debatched": [
    {
      "parent": "raw/inbox/example-bundle.md",
      "units_created": 5
    }
  ],
  "syntheses": [
    "wiki/syntheses/example-cluster.md"
  ]
}
```

## Avoid

- mutating accepted files in `raw/sources/`
- huge batch sizes that make review hard
- leaving `wiki/index.md` and `wiki/log.md` stale
