from __future__ import annotations

import json
from pathlib import Path


class TraceWriter:
    def __init__(self, run_dir: str | Path) -> None:
        self.run_dir = Path(run_dir)
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.events: list[dict] = []

    def record(self, step: str, state: str, payload: dict | None = None) -> None:
        self.events.append({"step": step, "state": state, "payload": payload or {}})

    def write(self, final_trace: dict) -> dict:
        trace = {"events": self.events, **final_trace}
        json_path = self.run_dir / "trace.json"
        md_path = self.run_dir / "trace.md"
        json_path.write_text(json.dumps(trace, indent=2, ensure_ascii=False), encoding="utf-8")
        md_path.write_text(_trace_markdown(trace), encoding="utf-8")
        return {"trace_json": str(json_path), "trace_md": str(md_path)}


def _trace_markdown(trace: dict) -> str:
    lines = ["# AbqPilot MVP-01 Trace", ""]
    final_verdict = trace.get("final_verdict", {})
    lines.append(f"- Final state: {final_verdict.get('final_state', 'UNKNOWN')}")
    lines.append(f"- Verdict: {final_verdict.get('verdict', 'UNKNOWN')}")
    lines.append("")
    lines.append("## Events")
    for event in trace.get("events", []):
        lines.append(f"- {event['step']}: {event['state']}")
    lines.append("")
    lines.append("## Trace JSON")
    lines.append("```json")
    lines.append(json.dumps(trace, indent=2, ensure_ascii=False))
    lines.append("```")
    return "\n".join(lines) + "\n"

