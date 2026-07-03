from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def write_json(path: str | Path, payload: dict[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def read_json(path: str | Path) -> dict[str, Any]:
    target = Path(path)
    if not target.exists():
        return {}
    return json.loads(target.read_text(encoding="utf-8"))


def write_text(path: str | Path, content: str) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def write_diagnosis_artifacts(job_dir: str | Path, request: dict[str, Any], result: dict[str, Any], summary_md: str) -> dict[str, str]:
    root = Path(job_dir)
    request_path = root / "job_odb_diagnosis_request.json"
    result_path = root / "job_odb_diagnosis_result.json"
    summary_path = root / "job_odb_diagnosis_summary.md"
    write_json(request_path, request)
    write_json(result_path, result)
    write_text(summary_path, summary_md)
    return {
        "request": str(request_path),
        "result": str(result_path),
        "summary": str(summary_path),
    }

