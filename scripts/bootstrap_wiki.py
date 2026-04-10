#!/usr/bin/env python3
"""Bootstrap an agent-first wiki skeleton.

Usage:
  python3 bootstrap_wiki.py /absolute/path/to/wiki
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

DIRS = [
    "meta/REPORTS",
    "meta/ROUTER/prompts",
    "meta/ROUTER/responses",
    "meta/ROUTER/errors",
    "meta/ROUTER/benchmarks",
    "inbox/pending",
    "inbox/failed",
    "inbox/manual-review",
    "raw/entries",
    "raw/assets",
    "raw/imports",
    "mind/projects",
    "mind/people",
    "mind/themes",
    "mind/patterns",
    "mind/decisions",
    "mind/timelines",
    "mind/syntheses",
    "mind/queries",
    "world/entities",
    "world/concepts",
    "world/domains",
    "world/comparisons",
    "world/sources",
    "world/syntheses",
    "world/queries",
    "archive",
    "scripts/lib",
    "templates",
]

STARTER_FILES = [
    ('templates/raw-entry.md', 'templates/raw-entry.md'),
    ('templates/wiki-page.md', 'templates/wiki-page.md'),
    ('templates/router-prompt.md', 'templates/router-prompt.md'),
    ('scripts/bootstrap_router.py', 'scripts/bootstrap_router.py'),
    ('scripts/write_entry.py', 'scripts/write_entry.py'),
    ('scripts/absorb.py', 'scripts/absorb.py'),
    ('scripts/cleanup.py', 'scripts/cleanup.py'),
    ('scripts/run_daily.py', 'scripts/run_daily.py'),
    ('scripts/run_weekly.py', 'scripts/run_weekly.py'),
    ('scripts/breakdown.py', 'scripts/breakdown.py'),
    ('scripts/rebuild_index.py', 'scripts/rebuild_index.py'),
    ('scripts/rebuild_backlinks.py', 'scripts/rebuild_backlinks.py'),
    ('scripts/lib/router_contract.py', 'scripts/lib/router_contract.py'),
    ('scripts/lib/router_io.py', 'scripts/lib/router_io.py'),
    ('scripts/lib/router.py', 'scripts/lib/router.py'),
]

SCHEMA_MD = """# SCHEMA

This wiki is agent-operated.

## Planes
- `mind/`: personal meaning, projects, decisions, patterns, and interpretations
- `world/`: external knowledge, entities, concepts, domains, and source-grounded material

## Ingestion rule
Every input becomes a raw entry before interpretation.

## Routing rule
LLM routing is mandatory. Routing failures must remain visible.

## Final raw-entry states
- `absorbed`
- `skipped`
- `needs_review`
- `failed`
"""

INDEX_MD = """# INDEX

## Main areas
- [[mind/projects]]
- [[mind/people]]
- [[mind/themes]]
- [[world/entities]]
- [[world/concepts]]
- [[world/domains]]

## Reports
- [[meta/REPORTS]]
"""

LOG_MD = """# LOG

"""

INGEST_SOURCES_MD = """# INGEST SOURCES

List here the sources that are allowed to feed this wiki.

Examples:
- chat sessions
- pasted text
- URLs
- local files
- exported documents
"""

STATUS_PY = """#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path


def count_md(path: Path) -> int:
    return sum(1 for p in path.rglob('*.md') if p.is_file()) if path.exists() else 0


def count_json(path: Path) -> int:
    return sum(1 for p in path.rglob('*.json') if p.is_file()) if path.exists() else 0


def main() -> int:
    if len(sys.argv) != 2:
        print('Usage: python3 status.py /absolute/path/to/wiki', file=sys.stderr)
        return 1
    root = Path(sys.argv[1]).expanduser().resolve()
    if not root.exists():
        print(json.dumps({'error': f'{root} does not exist'}, indent=2))
        return 2
    data = {
        'root': str(root),
        'raw_entries': count_md(root / 'raw' / 'entries'),
        'mind_pages': count_md(root / 'mind'),
        'world_pages': count_md(root / 'world'),
        'manual_review_entries': count_md(root / 'inbox' / 'manual-review'),
        'failed_entries': count_md(root / 'inbox' / 'failed'),
        'reports': count_md(root / 'meta' / 'REPORTS'),
        'router_prompt_artifacts': count_md(root / 'meta' / 'ROUTER' / 'prompts'),
        'router_response_artifacts': count_json(root / 'meta' / 'ROUTER' / 'responses'),
        'router_error_artifacts': count_json(root / 'meta' / 'ROUTER' / 'errors'),
        'router_config_present': (root / 'meta' / 'ROUTER' / 'router_config.json').exists(),
    }
    print(json.dumps(data, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
"""


def write_if_missing(path: Path, content: str) -> None:
    if not path.exists():
        path.write_text(content, encoding='utf-8')


def copy_starter_files(root: Path) -> list[str]:
    copied = []
    skill_root = Path(__file__).resolve().parents[1]
    for source_rel, target_rel in STARTER_FILES:
        source = skill_root / source_rel
        target = root / target_rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if source.exists() and not target.exists():
            shutil.copy2(source, target)
            copied.append(str(target))
    return copied


def main() -> int:
    if len(sys.argv) != 2:
        print('Usage: python3 bootstrap_wiki.py /absolute/path/to/wiki', file=sys.stderr)
        return 1

    root = Path(sys.argv[1]).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)

    for rel in DIRS:
        (root / rel).mkdir(parents=True, exist_ok=True)

    write_if_missing(root / 'meta' / 'SCHEMA.md', SCHEMA_MD)
    write_if_missing(root / 'meta' / 'INDEX.md', INDEX_MD)
    write_if_missing(root / 'meta' / 'LOG.md', LOG_MD)
    write_if_missing(root / 'meta' / 'INGEST_SOURCES.md', INGEST_SOURCES_MD)
    write_if_missing(root / 'meta' / 'BACKLINKS.json', '{}\n')
    write_if_missing(root / 'meta' / 'ABSORB_LOG.json', '[]\n')
    write_if_missing(root / 'scripts' / 'status.py', STATUS_PY)
    copied = copy_starter_files(root)

    print(json.dumps({
        'root': str(root),
        'created_dirs': len(DIRS),
        'status_script': str(root / 'scripts' / 'status.py'),
        'starter_files_copied': copied,
    }, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
