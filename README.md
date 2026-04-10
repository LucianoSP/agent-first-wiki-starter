# create-agent-first-wiki

Reusable starter kit for creating a local-first, agent-operated wiki with:

- raw-entry ingestion
- mandatory LLM routing
- absorb/update flow into `mind/` and `world/`
- rebuildable index and backlinks
- daily and weekly maintenance scripts
- visible routing failures

## Contents

- `SKILL.md` — the reusable skill definition
- `templates/` — starter templates
- `scripts/` — bootstrap, routing, absorb, cleanup, daily and weekly scripts
- `references/` — example tree

## Quick start

```bash
python3 scripts/bootstrap_wiki.py /path/to/wiki
python3 /path/to/wiki/scripts/bootstrap_router.py /path/to/wiki
```

Then edit `/path/to/wiki/meta/ROUTER/router_config.json`, export the API key, create a test raw entry, and run the daily cycle.
