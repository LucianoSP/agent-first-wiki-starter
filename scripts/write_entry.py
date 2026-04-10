#!/usr/bin/env python3
"""Create a raw entry in the wiki.

Usage:
  python3 write_entry.py /absolute/path/to/wiki --title 'My note' --text 'Body'
  echo 'Body' | python3 write_entry.py /absolute/path/to/wiki --title 'My note' --source-type text
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

URL_RE = re.compile(r'https?://[^\s)]+')


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')


def slugify(text: str) -> str:
    slug = re.sub(r'[^a-zA-Z0-9]+', '-', text.strip().lower()).strip('-')
    return slug or 'entry'


def extract_urls(text: str) -> list[str]:
    return sorted(set(URL_RE.findall(text or '')))


def append_log(root: Path, message: str) -> None:
    log_path = root / 'meta' / 'LOG.md'
    if not log_path.exists():
        log_path.write_text('# LOG\n\n', encoding='utf-8')
    with log_path.open('a', encoding='utf-8') as fh:
        fh.write(f'- {now_iso()} {message}\n')


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('root')
    parser.add_argument('--title', required=True)
    parser.add_argument('--text')
    parser.add_argument('--source-type', default='text')
    parser.add_argument('--source-ref', default='manual')
    parser.add_argument('--tags', default='')
    args = parser.parse_args()

    body = args.text if args.text is not None else sys.stdin.read()
    if not body.strip():
        print('Entry body is empty.', file=sys.stderr)
        return 2

    root = Path(args.root).expanduser().resolve()
    entries_dir = root / 'raw' / 'entries'
    entries_dir.mkdir(parents=True, exist_ok=True)

    created_at = now_iso()
    entry_id = created_at.replace(':', '-').replace('.', '-') + '-' + slugify(args.title)
    tags = [t.strip() for t in args.tags.split(',') if t.strip()]
    urls = extract_urls(body)
    summary = body.strip().splitlines()[0][:180]

    content = (
        '---\n'
        f'id: {entry_id}\n'
        'kind: raw_entry\n'
        'status: pending\n'
        f'title: {args.title}\n'
        f'source_type: {args.source_type}\n'
        f'source_ref: {args.source_ref}\n'
        f'created_at: {created_at}\n'
        f'urls: {urls}\n'
        f'tags: {tags}\n'
        '---\n\n'
        '# Summary\n\n'
        f'{summary}\n\n'
        '# Content\n\n'
        f'{body.rstrip()}\n'
    )

    path = entries_dir / f'{entry_id}.md'
    path.write_text(content, encoding='utf-8')
    append_log(root, f'capture raw_entry id={entry_id} path={path}')
    print(path)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
