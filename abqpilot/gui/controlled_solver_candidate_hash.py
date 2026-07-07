from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any


FORBIDDEN_CANDIDATE_NAMES = {
    ".env",
    "queue.json",
    "live_status.json",
}

FORBIDDEN_SUFFIXES = {
    ".cae",
    ".odb",
}


def compute_candidate_artifact_hash(path: str | Path | None, algorithm: str = "SHA256") -> dict[str, Any]:
    if path is None:
        return _result(None, algorithm, exists=False, blocked_reason="missing candidate artifact path")
    candidate = Path(path)
    blocked_reason = _blocked_reason(candidate)
    if blocked_reason:
        return _result(candidate, algorithm, exists=candidate.exists(), blocked_reason=blocked_reason)
    if algorithm.upper() != "SHA256":
        return _result(candidate, algorithm, exists=candidate.exists(), blocked_reason="unsupported hash algorithm")
    if not candidate.exists() or not candidate.is_file():
        return _result(candidate, algorithm, exists=False, blocked_reason="candidate artifact does not exist")
    digest = hashlib.sha256()
    with candidate.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return {
        "path": str(candidate),
        "algorithm": "SHA256",
        "hash": digest.hexdigest(),
        "exists": True,
        "blocked_reason": None,
        "source_sanity_base_candidate_blocked": False,
        "odb_hash_blocked": False,
        "env_hash_blocked": False,
    }


def _blocked_reason(path: Path) -> str | None:
    name = path.name.lower()
    lowered = str(path).lower()
    parts = {part.lower() for part in path.parts}
    if name in FORBIDDEN_CANDIDATE_NAMES:
        return f"forbidden candidate path: {path.name}"
    if ".env" in parts or name.endswith(".env"):
        return "forbidden candidate path: .env"
    if "runtime" in parts and "reports" in parts:
        return "forbidden candidate path: runtime/reports"
    if path.suffix.lower() in FORBIDDEN_SUFFIXES:
        return f"forbidden candidate suffix: {path.suffix}"
    if path.suffix.lower() == ".inp" and "sanity" in lowered and "base" in lowered:
        return "source sanity-base INP is not an allowed candidate artifact"
    return None


def _result(path: Path | None, algorithm: str, exists: bool, blocked_reason: str | None) -> dict[str, Any]:
    return {
        "path": str(path) if path else None,
        "algorithm": algorithm.upper(),
        "hash": None,
        "exists": exists,
        "blocked_reason": blocked_reason,
        "source_sanity_base_candidate_blocked": blocked_reason == "source sanity-base INP is not an allowed candidate artifact",
        "odb_hash_blocked": bool(path and path.suffix.lower() == ".odb"),
        "env_hash_blocked": blocked_reason == "forbidden candidate path: .env",
    }
