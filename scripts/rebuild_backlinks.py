#!/usr/bin/env python3
"""Rebuild meta/BACKLINKS.json from current wiki pages.

Usage:
  python3 rebuild_backlinks.py /absolute/path/to/wiki
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

LINK_RE = re.compile(r'\[\[([^\]]+)\]\]')


def rebuild_backlinks(root: Path) -> Path:
    wiki_paths = list((root / 'mind').rglob('*.md')) + list((root / 'world').rglob('*.md'))
    forward: dict[str, list[str]] = {}
    reverse: dict[str, list[str]] = {}

    for path in wiki_paths:
        rel = str(path.relative_to(root)).replace('.md', '')
        links = sorted(set(LINK_RE.findall(path.read_text(encoding='utf-8'))))
        forward[rel] = links
        for link in links:
            reverse.setdefault(link, []).append(rel)

    data = {
        'forward_links': {k: sorted(v) for k, v in sorted(forward.items())},
        'backlinks': {k: sorted(set(v)) for k, v in sorted(reverse.items())},
    }
    out = root / 'meta' / 'BACKLINKS.json'
    out.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    return out


def main() -> int:
    if len(sys.argv) != 2:
        print('Usage: python3 rebuild_backlinks.py /absolute/path/to/wiki', file=sys.stderr)
        return 1
    root = Path(sys.argv[1]).expanduser().resolve()
    out = rebuild_backlinks(root)
    print(json.dumps({'backlinks_path': str(out)}, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
