from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path


def now_stamp() -> str:
    return datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')


def slugify(text: str) -> str:
    slug = re.sub(r'[^a-zA-Z0-9]+', '-', text.strip().lower()).strip('-')
    return slug or 'page'


def read_text(path: Path) -> str:
    return path.read_text(encoding='utf-8')


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding='utf-8')


def append_log(root: Path, message: str) -> None:
    path = root / 'meta' / 'LOG.md'
    if not path.exists():
        write_text(path, '# LOG\n\n')
    with path.open('a', encoding='utf-8') as fh:
        fh.write(f'- {datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')} {message}\n')


def save_json(path: Path, data: object) -> None:
    write_text(path, json.dumps(data, indent=2, ensure_ascii=False) + '\n')
