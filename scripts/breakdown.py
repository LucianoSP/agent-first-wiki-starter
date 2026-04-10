#!/usr/bin/env python3
"""Create a simple weekly breakdown report for the wiki.

Usage:
  python3 breakdown.py /absolute/path/to/wiki
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

WORD_RE = re.compile(r"\b[a-zA-Z][a-zA-Z\-]{3,}\b")
STOPWORDS = {
    'this','that','with','from','have','were','will','your','about','into','after','before','where','there',
    'para','como','mais','esta','este','essa','esse','sobre','depois','antes','entre','quando','porque',
    'wiki','mind','world','notes','summary','links','status','active','related'
}


def top_terms(text: str, limit: int = 12) -> list[tuple[str, int]]:
    counts = Counter(word.lower() for word in WORD_RE.findall(text) if word.lower() not in STOPWORDS)
    return counts.most_common(limit)


def main() -> int:
    if len(sys.argv) != 2:
        print('Usage: python3 breakdown.py /absolute/path/to/wiki', file=sys.stderr)
        return 1
    root = Path(sys.argv[1]).expanduser().resolve()
    pages = sorted(list((root / 'mind').rglob('*.md')) + list((root / 'world').rglob('*.md')))
    corpus = []
    bucket_counts = Counter()
    for path in pages:
        rel = path.relative_to(root)
        parts = rel.parts
        if len(parts) >= 3:
            bucket_counts[f'{parts[0]}/{parts[1]}'] += 1
        text = path.read_text(encoding='utf-8', errors='replace')
        body = text.split('\n---\n', 1)[1] if '\n---\n' in text else text
        corpus.append(body)

    terms = top_terms('\n'.join(corpus))
    stamp = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    out = root / 'meta' / 'REPORTS' / f'breakdown-{stamp}.md'
    lines = [
        f'# Breakdown Report {stamp}',
        '',
        f'- pages_scanned: {len(pages)}',
        '',
        '## Bucket counts',
    ]
    lines.extend([f'- {bucket}: {count}' for bucket, count in sorted(bucket_counts.items())] or ['- none'])
    lines.extend(['', '## Frequent terms'])
    lines.extend([f'- {term}: {count}' for term, count in terms] or ['- none'])
    out.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(json.dumps({'report_path': str(out), 'pages_scanned': len(pages), 'top_terms': terms}, indent=2, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
