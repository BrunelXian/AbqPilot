from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def write_json(path: str | Path, payload: dict[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def write_text(path: str | Path, content: str) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def write_repair_artifacts(
    output_dir: str | Path,
    context: dict[str, Any],
    proposal: dict[str, Any],
    validation: dict[str, Any],
    summary_md: str,
) -> dict[str, str]:
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "context": root / "solver_failure_repair_context.json",
        "proposal": root / "solver_failure_repair_proposal.json",
        "validation": root / "solver_failure_repair_validation.json",
        "summary": root / "solver_failure_repair_summary.md",
    }
    write_json(paths["context"], context)
    write_json(paths["proposal"], proposal)
    write_json(paths["validation"], validation)
    write_text(paths["summary"], summary_md)
    return {key: str(value) for key, value in paths.items()}

