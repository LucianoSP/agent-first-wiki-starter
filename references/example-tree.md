# Example wiki tree

```text
wiki/
  meta/
    SCHEMA.md
    INDEX.md
    LOG.md
    BACKLINKS.json
    ABSORB_LOG.json
    INGEST_SOURCES.md
    REPORTS/
    ROUTER/
      prompts/
      responses/
      errors/
      benchmarks/
  inbox/
    pending/
    failed/
    manual-review/
  raw/
    entries/
    assets/
    imports/
  mind/
    projects/
    people/
    themes/
    patterns/
    decisions/
    timelines/
    syntheses/
    queries/
  world/
    entities/
    concepts/
    domains/
    comparisons/
    sources/
    syntheses/
    queries/
  archive/
  scripts/
    lib/
  templates/
```

## Notes

- `mind/` is for the user's own meaning, plans, decisions, projects, and interpreted patterns.
- `world/` is for external knowledge and source-grounded material.
- `raw/entries/` is the only entry point for ingestion.
- `meta/ROUTER/` stores routing artifacts for inspection and debugging.
- `inbox/manual-review/` is where entries land when routing or absorb cannot finish cleanly.
