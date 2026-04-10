from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path

from router_contract import RoutingDecision, parse_and_validate
from router_io import now_stamp, read_text, save_json, write_text


class RouterError(RuntimeError):
    pass


def load_router_config(root: Path) -> dict:
    path = root / 'meta' / 'ROUTER' / 'router_config.json'
    if not path.exists():
        raise RouterError(f'Missing router config: {path}')
    return json.loads(path.read_text(encoding='utf-8'))


def build_prompt(root: Path, metadata: dict, body: str) -> str:
    template_path = root / 'templates' / 'router-prompt.md'
    if not template_path.exists():
        raise RouterError(f'Missing router prompt template: {template_path}')
    template = read_text(template_path)
    return template.replace('{{entry_metadata}}', json.dumps(metadata, ensure_ascii=False, indent=2)).replace('{{entry_body}}', body)


def artifact_path(root: Path, kind: str, entry_id: str, suffix: str) -> Path:
    return root / 'meta' / 'ROUTER' / kind / f'{now_stamp()}-{entry_id}.{suffix}'


def save_prompt_preview(root: Path, entry_id: str, prompt: str) -> Path:
    path = artifact_path(root, 'prompts', entry_id, 'md')
    write_text(path, prompt)
    return path


def save_raw_response(root: Path, entry_id: str, response_text: str) -> Path:
    path = artifact_path(root, 'responses', entry_id, 'json')
    write_text(path, response_text)
    return path


def save_error_artifact(root: Path, entry_id: str, payload: dict) -> Path:
    path = artifact_path(root, 'errors', entry_id, 'json')
    save_json(path, payload)
    return path


def invoke_openai_compatible(prompt: str, config: dict) -> str:
    api_key_env = config.get('api_key_env', 'WIKI_ROUTER_API_KEY')
    api_key = os.environ.get(api_key_env)
    if not api_key:
        raise RouterError(f'Missing API key in environment variable: {api_key_env}')

    model = config.get('model')
    base_url = config.get('base_url', 'https://api.openai.com/v1').rstrip('/')
    if not model:
        raise RouterError('router_config.json is missing `model`')

    payload = {
        'model': model,
        'messages': [
            {'role': 'system', 'content': 'You must return strict JSON only.'},
            {'role': 'user', 'content': prompt},
        ],
        'temperature': config.get('temperature', 0),
        'max_tokens': config.get('max_output_tokens', 900),
    }
    req = urllib.request.Request(
        url=f'{base_url}/chat/completions',
        data=json.dumps(payload).encode('utf-8'),
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}',
        },
        method='POST',
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            raw = resp.read().decode('utf-8')
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode('utf-8', errors='replace')
        raise RouterError(f'HTTP {exc.code}: {detail}') from exc
    except urllib.error.URLError as exc:
        raise RouterError(f'Network error: {exc}') from exc

    data = json.loads(raw)
    try:
        return data['choices'][0]['message']['content']
    except Exception as exc:
        raise RouterError(f'Unexpected provider response shape: {raw}') from exc


def route_entry(root: Path, entry_id: str, metadata: dict, body: str) -> tuple[RoutingDecision, dict]:
    config = load_router_config(root)
    prompt = build_prompt(root, metadata, body)
    prompt_path = save_prompt_preview(root, entry_id, prompt)

    provider = config.get('provider', 'openai_compatible')
    if provider != 'openai_compatible':
        raise RouterError(f'Unsupported provider in starter kit: {provider}')

    raw_response = invoke_openai_compatible(prompt, config)
    response_path = save_raw_response(root, entry_id, raw_response)
    decision = parse_and_validate(raw_response)
    meta = {
        'provider': provider,
        'model': config.get('model'),
        'prompt_path': str(prompt_path),
        'response_path': str(response_path),
    }
    return decision, meta
