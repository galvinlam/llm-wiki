# Wiki Linter Skill

## Goal

Keep the knowledge base coherent, navigable, and cumulative.

## Read first

1. `AGENTS.md`
2. `.codex/README.md`
3. `.codex/MEMORY.yaml`
4. `wiki/index.md`
5. `wiki/log.md`

## Responsibilities

- find orphan pages
- find duplicated concepts or entities
- find duplicated atomic source pages
- find bundle-shaped source pages that should have been decomposed
- identify unsupported claims
- identify repeated answers that should become syntheses
- identify repeated atomic clusters that should become syntheses
- split overloaded syntheses into smaller topic-bounded syntheses when one page is carrying multiple distinct lanes
- propose or create weekly summaries
- improve internal linking and page discoverability
- mark weak pages as `needs_enrichment` instead of silently leaving them ambiguous

## Suggested cadence

- light pass daily
- deeper synthesis pass weekly

## Output expectations

If used through automation, write JSON summarizing:

```json
{
  "summary": "Linted the wiki, merged duplicate source units, and promoted 3 syntheses.",
  "touched": [
    "wiki/index.md",
    "wiki/syntheses/example.md"
  ],
  "clusters": [
    {
      "topic": "example-topic",
      "sources": [
        "wiki/sources/example-1.md",
        "wiki/sources/example-2.md"
      ],
      "synthesis": "wiki/syntheses/example-topic.md"
    }
  ]
}
```

## Avoid

- destructive restructuring without clear gain
- changing user intent or historical meaning
- removing source traceability
