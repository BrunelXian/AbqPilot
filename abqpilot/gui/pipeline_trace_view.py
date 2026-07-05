from __future__ import annotations

from pathlib import Path
from typing import Any

from abqpilot.pipeline_protocol.frontmatter import load_frontmatter


def build_pipeline_trace_view(task_dir: str | Path) -> dict[str, Any]:
    task = Path(task_dir)
    return {
        "runs": _records(task / "trace", "RUN_*.md", "run_id", "status"),
        "handoffs": _records(task / "handoffs", "HANDOFF_*.md", "handoff_id", "to_agent"),
        "gates": _records(task / "gates", "GATE_*.md", "gate_id", "decision"),
    }


def _records(folder: Path, pattern: str, id_key: str, status_key: str) -> list[dict[str, Any]]:
    if not folder.exists():
        return []
    records: list[dict[str, Any]] = []
    for path in sorted(folder.glob(pattern)):
        try:
            frontmatter = load_frontmatter(path)
        except (OSError, UnicodeDecodeError):
            frontmatter = {}
        records.append(
            {
                "path": str(path),
                "id": frontmatter.get(id_key) or path.stem,
                "status": frontmatter.get(status_key) or frontmatter.get("decision"),
                "agent": frontmatter.get("agent") or frontmatter.get("from_agent"),
                "doc_type": frontmatter.get("doc_type"),
            }
        )
    return records
