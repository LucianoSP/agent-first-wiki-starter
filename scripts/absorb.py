#!/usr/bin/env python3
"""Absorb pending raw entries into wiki pages using the LLM router.

Usage:
  python3 absorb.py /absolute/path/to/wiki
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
LIB_DIR = SCRIPT_DIR / 'lib'
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from router import RouterError, route_entry, save_error_artifact  # type: ignore
from router_io import append_log, read_text, save_json, slugify, write_text  # type: ignore


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')


def parse_frontmatter(text: str) -> tuple[dict, str]:
    if not text.startswith('---\n'):
        raise ValueError('Missing frontmatter start')
    parts = text.split('\n---\n', 1)
    if len(parts) != 2:
        raise ValueError('Missing frontmatter end')
    raw_meta = parts[0][4:]
    body = parts[1]
    meta: dict[str, object] = {}
    for line in raw_meta.splitlines():
        if not line.strip() or ':' not in line:
            continue
        key, value = line.split(':', 1)
        value = value.strip()
        if value.startswith('[') and value.endswith(']'):
            items = [x.strip().strip("'\"") for x in value[1:-1].split(',') if x.strip()]
            meta[key.strip()] = items
        else:
            meta[key.strip()] = value
    return meta, body


def render_frontmatter(meta: dict) -> str:
    lines = ['---']
    for key, value in meta.items():
        if isinstance(value, list):
            lines.append(f'{key}: {json.dumps(value, ensure_ascii=False)}')
        else:
            lines.append(f'{key}: {value}')
    lines.append('---')
    return '\n'.join(lines)


def extract_section(body: str, heading: str) -> str:
    pattern = rf'(?ms)^# {re.escape(heading)}\s*\n+(.*?)(?=^# |\Z)'
    match = re.search(pattern, body)
    return match.group(1).strip() if match else ''


def page_path(root: Path, plane: str, bucket: str, slug: str) -> Path:
    return root / plane / bucket / f'{slugify(slug)}.md'


def update_existing_page(path: Path, target, decision_summary: str, body: str) -> None:
    text = read_text(path)
    now = now_iso()
    if text.startswith('---\n') and '\n---\n' in text:
        raw_meta, rest = text[4:].split('\n---\n', 1)
        lines = []
        updated = False
        for line in raw_meta.splitlines():
            if line.startswith('updated_at:'):
                lines.append(f'updated_at: {now}')
                updated = True
            else:
                lines.append(line)
        if not updated:
            lines.append(f'updated_at: {now}')
        text = '---\n' + '\n'.join(lines) + '\n---\n' + rest
    note_block = (
        f'\n\n## Update {now}\n\n'
        f'- Routing reason: {target.reason}\n'
        f'- Entry summary: {decision_summary}\n\n'
        f'{body.strip()}\n'
    )
    write_text(path, text.rstrip() + note_block)


def create_or_update_page(root: Path, target, entry_meta: dict, decision_summary: str, body: str) -> str:
    path = page_path(root, target.plane, target.bucket, target.slug)
    source_ref = entry_meta.get('source_ref', 'unknown')
    now = now_iso()
    if path.exists():
        update_existing_page(path, target, decision_summary, body)
        return str(path)

    title = target.slug.replace('-', ' ').title()
    content = (
        '---\n'
        f'title: {title}\n'
        f'type: {target.bucket[:-1] if target.bucket.endswith("s") else target.bucket}\n'
        'status: active\n'
        f'created_at: {now}\n'
        f'updated_at: {now}\n'
        f'source_refs: [{json.dumps(str(source_ref))[1:-1]}]\n'
        'tags: []\n'
        '---\n\n'
        '# Summary\n\n'
        f'{decision_summary}\n\n'
        '# Notes\n\n'
        f'{body.strip()}\n\n'
        '# Links\n\n'
        '- Related: \n'
    )
    write_text(path, content)
    return str(path)


def move_to_review(root: Path, src: Path, status: str) -> Path:
    if status == 'needs_review':
        dest = root / 'inbox' / 'manual-review' / src.name
    else:
        dest = root / 'inbox' / 'failed' / src.name
    dest.parent.mkdir(parents=True, exist_ok=True)
    src.replace(dest)
    return dest


def update_absorb_log(root: Path, event: dict) -> None:
    path = root / 'meta' / 'ABSORB_LOG.json'
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding='utf-8'))
            if not isinstance(data, list):
                data = []
        except Exception:
            data = []
    else:
        data = []
    data.append(event)
    save_json(path, data)


def run_script(script_path: Path, root: Path) -> None:
    proc = subprocess.run(['python3', str(script_path), str(root)], capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f'{script_path.name} failed: {proc.stderr or proc.stdout}')


def process_entry(root: Path, path: Path) -> dict:
    raw = read_text(path)
    meta, content = parse_frontmatter(raw)
    if meta.get('status') != 'pending':
        return {'entry': str(path), 'status': 'skipped_non_pending'}

    entry_id = str(meta.get('id', path.stem))
    body = extract_section(content, 'Content') or content.strip()
    try:
        decision, router_meta = route_entry(root, entry_id, meta, body)
        outputs = [create_or_update_page(root, target, meta, decision.summary, body) for target in decision.create]
        meta['status'] = 'absorbed'
        meta['absorbed_at'] = now_iso()
        updated = render_frontmatter(meta) + '\n\n' + content.lstrip()
        write_text(path, updated)
        event = {
            'entry_id': entry_id,
            'status': 'absorbed',
            'summary': decision.summary,
            'outputs': outputs,
            'update_candidates': decision.update_candidates,
            'notes': decision.notes,
            **router_meta,
        }
        update_absorb_log(root, event)
        append_log(root, f'absorb success entry={entry_id} outputs={outputs}')
        return event
    except Exception as exc:
        status = 'needs_review' if isinstance(exc, RouterError) else 'failed'
        error_payload = {
            'entry_id': entry_id,
            'error_type': type(exc).__name__,
            'error': str(exc),
            'source_entry': str(path),
        }
        error_path = save_error_artifact(root, entry_id, error_payload)
        meta['status'] = status
        meta['error_artifact'] = str(error_path)
        updated = render_frontmatter(meta) + '\n\n' + content.lstrip()
        write_text(path, updated)
        final_path = move_to_review(root, path, status)
        event = {
            'entry_id': entry_id,
            'status': status,
            'error': str(exc),
            'error_artifact': str(error_path),
            'final_path': str(final_path),
        }
        update_absorb_log(root, event)
        append_log(root, f'absorb error entry={entry_id} status={status} error={exc}')
        return event


def main() -> int:
    if len(sys.argv) != 2:
        print('Usage: python3 absorb.py /absolute/path/to/wiki', file=sys.stderr)
        return 1
    root = Path(sys.argv[1]).expanduser().resolve()
    entries = sorted((root / 'raw' / 'entries').glob('*.md'))
    results = [process_entry(root, path) for path in entries]
    run_script(SCRIPT_DIR / 'rebuild_index.py', root)
    run_script(SCRIPT_DIR / 'rebuild_backlinks.py', root)
    print(json.dumps(results, indent=2, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
