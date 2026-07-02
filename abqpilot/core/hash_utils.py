from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Iterable


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json(obj: dict, exclude_keys: Iterable[str] | None = None) -> str:
    cleaned = _without_keys(obj, set(exclude_keys or ()))
    return json.dumps(cleaned, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_json_obj(obj: dict, exclude_keys: Iterable[str] | None = None) -> str:
    return hashlib.sha256(canonical_json(obj, exclude_keys=exclude_keys).encode("utf-8")).hexdigest()


def _without_keys(value: Any, exclude_keys: set[str]) -> Any:
    if isinstance(value, dict):
        return {key: _without_keys(item, exclude_keys) for key, item in value.items() if key not in exclude_keys}
    if isinstance(value, list):
        return [_without_keys(item, exclude_keys) for item in value]
    return value
