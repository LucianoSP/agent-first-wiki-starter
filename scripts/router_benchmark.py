#!/usr/bin/env python3
"""Run a simple routing benchmark against the wiki router.

Usage:
  python3 router_benchmark.py /absolute/path/to/wiki /path/to/cases.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
LIB_DIR = SCRIPT_DIR / 'lib'
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from router import RouterError, route_entry  # type: ignore


def target_key(item) -> str:
    return f"{item.plane}/{item.bucket}"


def main() -> int:
    if len(sys.argv) != 3:
        print('Usage: python3 router_benchmark.py /absolute/path/to/wiki /path/to/cases.json', file=sys.stderr)
        return 1

    root = Path(sys.argv[1]).expanduser().resolve()
    cases_path = Path(sys.argv[2]).expanduser().resolve()
    cases = json.loads(cases_path.read_text(encoding='utf-8'))

    results = []
    success = 0
    must_hit = 0
    allowed_only = 0

    for case in cases:
        metadata = {
            'id': case['id'],
            'title': case['title'],
            'status': 'pending',
            'source_type': 'benchmark',
            'source_ref': 'router_benchmark',
        }
        expected = case['expected']
        try:
            decision, router_meta = route_entry(root, case['id'], metadata, case['body'])
            actual = [target_key(t) for t in decision.create]
            must_ok = all(x in actual for x in expected.get('must_include', []))
            allowed_ok = all(x in expected.get('allowed', []) for x in actual)
            if must_ok:
                must_hit += 1
            if allowed_ok:
                allowed_only += 1
            success += 1
            results.append({
                'id': case['id'],
                'status': 'ok',
                'summary': decision.summary,
                'actual': actual,
                'must_include': expected.get('must_include', []),
                'allowed': expected.get('allowed', []),
                'must_match': must_ok,
                'allowed_match': allowed_ok,
                'provider': router_meta.get('provider'),
                'model': router_meta.get('model'),
            })
        except Exception as exc:
            results.append({
                'id': case['id'],
                'status': 'error',
                'error_type': type(exc).__name__,
                'error': str(exc),
            })

    summary = {
        'cases': len(cases),
        'successful_calls': success,
        'must_match_cases': must_hit,
        'allowed_match_cases': allowed_only,
        'errors': len(cases) - success,
        'must_match_rate': round(must_hit / len(cases), 3) if cases else 0,
        'allowed_match_rate': round(allowed_only / len(cases), 3) if cases else 0,
    }
    out = {
        'summary': summary,
        'results': results,
    }
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0 if success == len(cases) else 2


if __name__ == '__main__':
    raise SystemExit(main())
