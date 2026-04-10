#!/usr/bin/env python3
"""Run basic integrity checks and write a cleanup report.

Usage:
  python3 cleanup.py /absolute/path/to/wiki
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

LINK_RE = re.compile(r'\[\[([^\]]+)\]\]')


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')


def collect_pages(root: Path) -> list[Path]:
    return sorted(list((root / 'mind').rglob('*.md')) + list((root / 'world').rglob('*.md')))


def has_frontmatter(text: str) -> bool:
    return text.startswith('---\n') and '\n---\n' in text


def main() -> int:
    if len(sys.argv) != 2:
        print('Usage: python3 cleanup.py /absolute/path/to/wiki', file=sys.stderr)
        return 1
    root = Path(sys.argv[1]).expanduser().resolve()
    pages = collect_pages(root)
    existing = {str(p.relative_to(root)).replace('.md', '') for p in pages}

    missing_frontmatter = []
    broken_links = []
    oversized = []
    orphans = []

    inbound: dict[str, int] = {key: 0 for key in existing}
    for path in pages:
        rel = str(path.relative_to(root)).replace('.md', '')
        text = path.read_text(encoding='utf-8')
        if not has_frontmatter(text):
            missing_frontmatter.append(rel)
        if len(text) > 15000:
            oversized.append({'page': rel, 'chars': len(text)})
        links = sorted(set(LINK_RE.findall(text)))
        valid_outbound = 0
        for link in links:
            if link in existing:
                inbound[link] = inbound.get(link, 0) + 1
                valid_outbound += 1
            elif not link.startswith('meta/'):
                broken_links.append({'page': rel, 'link': link})
        if valid_outbound == 0:
            orphans.append(rel)

    pending = len(list((root / 'raw' / 'entries').glob('*.md')))
    manual_review = len(list((root / 'inbox' / 'manual-review').glob('*.md')))
    failed = len(list((root / 'inbox' / 'failed').glob('*.md')))
    router_errors = len(list((root / 'meta' / 'ROUTER' / 'errors').glob('*.json')))

    report = {
        'generated_at': now_iso(),
        'pages_scanned': len(pages),
        'missing_frontmatter': missing_frontmatter,
        'broken_links': broken_links,
        'oversized_pages': oversized,
        'orphans': sorted(orphan for orphan, count in inbound.items() if count == 0 and orphan in orphans),
        'queues': {
            'pending_raw_entries': pending,
            'manual_review_entries': manual_review,
            'failed_entries': failed,
            'router_error_artifacts': router_errors,
        },
    }

    stamp = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    out = root / 'meta' / 'REPORTS' / f'cleanup-{stamp}.md'
    lines = [
        f'# Cleanup Report {stamp}',
        '',
        f'- generated_at: {report["generated_at"]}',
        f'- pages_scanned: {report["pages_scanned"]}',
        '',
        '## Queues',
        f'- pending_raw_entries: {pending}',
        f'- manual_review_entries: {manual_review}',
        f'- failed_entries: {failed}',
        f'- router_error_artifacts: {router_errors}',
        '',
        '## Missing frontmatter',
    ]
    lines.extend([f'- {item}' for item in missing_frontmatter] or ['- none'])
    lines.extend(['', '## Broken links'])
    lines.extend([f'- {item["page"]} -> [[{item["link"]}]]' for item in broken_links] or ['- none'])
    lines.extend(['', '## Oversized pages'])
    lines.extend([f'- {item["page"]}: {item["chars"]} chars' for item in oversized] or ['- none'])
    lines.extend(['', '## Orphans'])
    lines.extend([f'- {item}' for item in report['orphans']] or ['- none'])
    out.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(json.dumps({'report_path': str(out), 'summary': report}, indent=2, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
