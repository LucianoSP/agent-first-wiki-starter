#!/usr/bin/env python3
"""Create starter router config files for an agent-first wiki.

Usage:
  python3 bootstrap_router.py /absolute/path/to/wiki
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

CONFIG_TEMPLATE = {
    "provider": "openai-codex",
    "model": "gpt-5.4",
    "hermes_agent_path": "/root/.hermes/hermes-agent",
    "hermes_python": "/root/.hermes/hermes-agent/venv/bin/python",
    "api_key_env": "WIKI_ROUTER_API_KEY",
    "base_url": "https://chatgpt.com/backend-api/codex",
    "temperature": 0,
    "max_output_tokens": 900,
}

README = """# Router setup

This wiki expects LLM routing.

## Recommended default
Use `openai-codex` with `gpt-5.4` when Hermes is installed locally with working OAuth.

## Minimal setup
1. Run this script after `bootstrap_wiki.py`.
2. Keep `provider` as `openai-codex` if you want to use the same GPT-5.4 path as Hermes.
3. Confirm `hermes_agent_path` and `hermes_python` point to a real Hermes installation.
4. Test with a real raw entry and run `scripts/absorb.py`.

## Alternative setup
If you want a normal OpenAI-compatible endpoint instead, switch:
- `provider` to `openai_compatible`
- `model` to the desired model
- `base_url` to the provider base URL
- `api_key_env` to the environment variable containing the API key

## Failure policy
If routing fails, the entry must move to manual review or failed state with visible artifacts under `meta/ROUTER/`.
"""


def main() -> int:
    if len(sys.argv) != 2:
        print('Usage: python3 bootstrap_router.py /absolute/path/to/wiki', file=sys.stderr)
        return 1
    root = Path(sys.argv[1]).expanduser().resolve()
    if not root.exists():
        print(f'Wiki root does not exist: {root}', file=sys.stderr)
        return 2

    router_dir = root / 'meta' / 'ROUTER'
    router_dir.mkdir(parents=True, exist_ok=True)
    config_path = router_dir / 'router_config.json'
    readme_path = router_dir / 'README.md'

    if not config_path.exists():
        config_path.write_text(json.dumps(CONFIG_TEMPLATE, indent=2) + '\n', encoding='utf-8')
    if not readme_path.exists():
        readme_path.write_text(README, encoding='utf-8')

    print(json.dumps({
        'config_path': str(config_path),
        'readme_path': str(readme_path),
    }, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
