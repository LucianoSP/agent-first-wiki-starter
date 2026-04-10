from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

VALID_PLANES = {'mind', 'world'}
VALID_BUCKETS = {
    'mind': {'projects', 'people', 'themes', 'patterns', 'decisions', 'timelines', 'syntheses', 'queries'},
    'world': {'entities', 'concepts', 'domains', 'comparisons', 'sources', 'syntheses', 'queries'},
}
VALID_CONFIDENCE = {'observed', 'inferred', 'speculative'}


@dataclass
class RouteTarget:
    plane: str
    bucket: str
    slug: str
    reason: str


@dataclass
class RoutingDecision:
    confidence: str
    summary: str
    create: list[RouteTarget]
    update_candidates: list[str]
    notes: list[str]


def parse_json_object(text: str) -> dict[str, Any]:
    data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError('Router output must be a JSON object.')
    return data


def validate_decision_dict(data: dict[str, Any]) -> RoutingDecision:
    allowed_keys = {'confidence', 'summary', 'create', 'update_candidates', 'notes'}
    extra = set(data.keys()) - allowed_keys
    if extra:
        raise ValueError(f'Unknown keys in routing JSON: {sorted(extra)}')

    confidence = data.get('confidence')
    summary = data.get('summary')
    create = data.get('create')
    update_candidates = data.get('update_candidates', [])
    notes = data.get('notes', [])

    if confidence not in VALID_CONFIDENCE:
        raise ValueError(f'Invalid confidence: {confidence}')
    if not isinstance(summary, str) or not summary.strip():
        raise ValueError('summary must be a non-empty string')
    if not isinstance(create, list) or not (1 <= len(create) <= 3):
        raise ValueError('create must be a list with 1 to 3 items')
    if not isinstance(update_candidates, list) or not all(isinstance(x, str) and x.strip() for x in update_candidates):
        raise ValueError('update_candidates must be a list of non-empty strings')
    if not isinstance(notes, list) or not all(isinstance(x, str) for x in notes):
        raise ValueError('notes must be a list of strings')

    targets: list[RouteTarget] = []
    for idx, item in enumerate(create):
        if not isinstance(item, dict):
            raise ValueError(f'create[{idx}] must be an object')
        item_keys = {'plane', 'bucket', 'slug', 'reason'}
        extra_item = set(item.keys()) - item_keys
        if extra_item:
            raise ValueError(f'Unknown keys in create[{idx}]: {sorted(extra_item)}')
        plane = item.get('plane')
        bucket = item.get('bucket')
        slug = item.get('slug')
        reason = item.get('reason')
        if plane not in VALID_PLANES:
            raise ValueError(f'Invalid plane in create[{idx}]: {plane}')
        if bucket not in VALID_BUCKETS[plane]:
            raise ValueError(f'Invalid bucket for plane {plane} in create[{idx}]: {bucket}')
        if not isinstance(slug, str) or not slug.strip():
            raise ValueError(f'Invalid slug in create[{idx}]')
        if not isinstance(reason, str) or not reason.strip():
            raise ValueError(f'Invalid reason in create[{idx}]')
        targets.append(RouteTarget(plane=plane, bucket=bucket, slug=slug.strip(), reason=reason.strip()))

    return RoutingDecision(
        confidence=confidence,
        summary=summary.strip(),
        create=targets,
        update_candidates=[x.strip() for x in update_candidates],
        notes=notes,
    )


def parse_and_validate(text: str) -> RoutingDecision:
    return validate_decision_dict(parse_json_object(text))
