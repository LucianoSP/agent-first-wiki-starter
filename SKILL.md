---
name: create-agent-first-wiki
description: Create a reusable local-first, agent-operated personal wiki for any user, with raw ingestion, mandatory LLM routing, maintenance scripts, automation, and starter templates.
version: 1.2.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [wiki, personal-knowledge, obsidian, local-first, automation, llm, routing]
---

# Create Agent-First Wiki

Create a local-first wiki that the agent can run end-to-end: capture → route → absorb → maintain → automate.

Use this skill to create a new wiki system, not to document an existing notes folder.

## Use when

Use this when the user wants:
- a personal or project wiki on local disk
- minimal manual filing
- semantic placement decided by an LLM
- visible maintenance and diagnostics

Do not use this when:
- the user only wants a simple notes directory
- the canonical write backend must be cloud-first
- the user wants to classify notes manually

## Core stance

LLM routing is part of the base architecture.

Heuristics are acceptable only for scaffolding, benchmarking, or diagnostics. They should not be the main routing path.

## Non-negotiable rules

1. Local-first canonical store.
2. Every input becomes a raw entry before interpretation.
3. `mind/` and `world/` stay distinct.
4. Routing must be inspectable.
5. Routing failures must stay visible.
6. Index, backlinks, and logs must be rebuildable from filesystem state.

## Root layout

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

## Folder intent

- `raw/entries/`: normalized inputs before interpretation
- `mind/`: personal meaning, projects, people, patterns, decisions
- `world/`: external knowledge, entities, concepts, domains, sources
- `meta/`: rebuildable artifacts, reports, logs, router telemetry
- `inbox/`: entries awaiting review or marked failed

## What the starter kit already includes

The linked files already provide a practical starter kit:
- `scripts/bootstrap_wiki.py`
- `scripts/bootstrap_router.py`
- `scripts/write_entry.py`
- `scripts/absorb.py`
- `scripts/rebuild_index.py`
- `scripts/rebuild_backlinks.py`
- `scripts/cleanup.py`
- `scripts/run_daily.py`
- `scripts/run_weekly.py`
- `scripts/breakdown.py`
- `scripts/lib/router_contract.py`
- `scripts/lib/router_io.py`
- `scripts/lib/router.py`
- `templates/raw-entry.md`
- `templates/wiki-page.md`
- `templates/router-prompt.md`
- `references/example-tree.md`

`bootstrap_wiki.py` now copies the starter templates and scripts into the new wiki automatically.

## Recommended setup flow

1. Run `bootstrap_wiki.py /path/to/wiki`.
2. Run `bootstrap_router.py /path/to/wiki`.
3. Edit `meta/ROUTER/router_config.json`.
4. Export the API key named by `api_key_env`.
5. Create a test entry with `write_entry.py`.
6. Run `absorb.py`.
7. Run `run_daily.py`.

## Router contract

Return strict JSON only.

```json
{
  "confidence": "observed|inferred|speculative",
  "summary": "short routing summary",
  "create": [
    {
      "plane": "mind|world",
      "bucket": "projects|people|themes|patterns|decisions|timelines|syntheses|queries|entities|concepts|domains|comparisons|sources",
      "slug": "kebab-case",
      "reason": "why this page should exist"
    }
  ],
  "update_candidates": ["mind/projects/example"],
  "notes": ["optional notes"]
}
```

Validation rules:
- 1 to 3 create targets
- valid plane only
- valid bucket only
- non-empty slug and reason
- path-like `update_candidates`
- no extra keys

## Failure policy

Never hide routing failures.

If model call, parsing, or validation fails:
- save artifacts under `meta/ROUTER/errors/` and, when available, `meta/ROUTER/responses/`
- append an error event to `meta/LOG.md`
- move the raw entry to `needs_review` or `failed`
- make the issue visible in `status.py` and cleanup reports

## Daily and weekly operations

Daily cycle:
- absorb pending entries
- rebuild index
- rebuild backlinks
- run cleanup
- write status snapshot

Weekly cycle:
- run the daily cycle
- generate a simple breakdown report
- write weekly status snapshot

## Good defaults

- markdown for pages
- kebab-case slugs
- local scripts for core operations
- append-only operational log
- persisted router artifacts
- explicit provider/model recording during absorb

## Minimal verification checklist

A fresh setup is good enough when:
- bootstrap creates the tree and copies starter files
- router config exists after `bootstrap_router.py`
- `write_entry.py` creates a raw entry
- `absorb.py` either routes successfully or fails visibly
- `rebuild_index.py` and `rebuild_backlinks.py` run
- `cleanup.py` writes a report
- `run_daily.py` and `run_weekly.py` produce snapshots

## What to customize per user

Customize these without changing the architecture:
- root path
- source types
- naming conventions
- timezone semantics
- provider and model
- prompt wording
- page templates

## Pitfalls

- over-designing taxonomy before real ingestion
- asking the user to choose folders manually
- mixing personal interpretation and external facts in one bucket
- hiding routing errors behind fallback behavior
- making cloud storage the primary write path too early

## Short implementation order

1. Bootstrap the wiki.
2. Bootstrap the router.
3. Test capture with a raw entry.
4. Test routing and absorb.
5. Start the daily cycle.
6. Add deeper evaluation only if the wiki is actually being used.
