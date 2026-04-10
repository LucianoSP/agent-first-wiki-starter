#!/usr/bin/env python3
"""Run the daily wiki maintenance cycle.

Usage:
  python3 run_daily.py /absolute/path/to/wiki
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def run_step(command: list[str]) -> dict:
    proc = subprocess.run(command, capture_output=True, text=True)
    return {
        'command': command,
        'exit_code': proc.returncode,
        'stdout': proc.stdout.strip(),
        'stderr': proc.stderr.strip(),
    }


def main() -> int:
    if len(sys.argv) != 2:
        print('Usage: python3 run_daily.py /absolute/path/to/wiki', file=sys.stderr)
        return 1

    root = Path(sys.argv[1]).expanduser().resolve()
    scripts = root / 'scripts'
    steps = [
        ['python3', str(scripts / 'absorb.py'), str(root)],
        ['python3', str(scripts / 'rebuild_index.py'), str(root)],
        ['python3', str(scripts / 'rebuild_backlinks.py'), str(root)],
        ['python3', str(scripts / 'cleanup.py'), str(root)],
        ['python3', str(scripts / 'status.py'), str(root)],
    ]

    results = [run_step(step) for step in steps]
    overall_ok = all(item['exit_code'] == 0 for item in results)
    stamp = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    snapshot = root / 'meta' / 'REPORTS' / f'status-daily-{stamp}.md'

    lines = [f'# Daily Status {stamp}', '']
    for item in results:
        lines.append(f'## {Path(item["command"][1]).name}')
        lines.append(f'- exit_code: {item["exit_code"]}')
        lines.append('- stdout:')
        lines.append('```')
        lines.append(item['stdout'] or '(empty)')
        lines.append('```')
        if item['stderr']:
            lines.append('- stderr:')
            lines.append('```')
            lines.append(item['stderr'])
            lines.append('```')
        lines.append('')
    snapshot.write_text('\n'.join(lines), encoding='utf-8')

    print(json.dumps({
        'ok': overall_ok,
        'status_snapshot': str(snapshot),
        'steps': results,
    }, indent=2, ensure_ascii=False))
    return 0 if overall_ok else 2


if __name__ == '__main__':
    raise SystemExit(main())
