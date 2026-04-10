#!/usr/bin/env python3
"""Rebuild meta/INDEX.md from current wiki pages.

Usage:
  python3 rebuild_index.py /absolute/path/to/wiki
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


MIND_BUCKETS = ['projects', 'people', 'themes', 'patterns', 'decisions', 'timelines', 'syntheses', 'queries']
WORLD_BUCKETS = ['entities', 'concepts', 'domains', 'comparisons', 'sources', 'syntheses', 'queries']


def rebuild_index(root: Path) -> Path:
    lines = ['# INDEX', '', '## Mind']
    for bucket in MIND_BUCKETS:
        bucket_paths = sorted((root / 'mind' / bucket).glob('*.md'))
        if bucket_paths:
            lines.append(f'### {bucket}')
            for path in bucket_paths:
                lines.append(f'- [[mind/{bucket}/{path.stem}]]')
    lines.extend(['', '## World'])
    for bucket in WORLD_BUCKETS:
        bucket_paths = sorted((root / 'world' / bucket).glob('*.md'))
        if bucket_paths:
            lines.append(f'### {bucket}')
            for path in bucket_paths:
                lines.append(f'- [[world/{bucket}/{path.stem}]]')
    lines.extend(['', '## System', '- [[meta/LOG]]', '- [[meta/REPORTS]]'])
    out = root / 'meta' / 'INDEX.md'
    out.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    return out


def main() -> int:
    if len(sys.argv) != 2:
        print('Usage: python3 rebuild_index.py /absolute/path/to/wiki', file=sys.stderr)
        return 1
    root = Path(sys.argv[1]).expanduser().resolve()
    out = rebuild_index(root)
    print(json.dumps({'index_path': str(out)}, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
