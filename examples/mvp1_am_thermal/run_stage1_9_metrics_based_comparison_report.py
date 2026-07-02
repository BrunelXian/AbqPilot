from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from abqpilot.analysis import build_agent_observation, build_comparison_report
from abqpilot.analysis.metrics_comparator import render_markdown_report


RUN_DIR = PROJECT_ROOT / "runs" / "stage1_9_metrics_based_comparison_report"
SOURCE_METRICS = PROJECT_ROOT / "runs" / "stage1_8_gated_odb_metrics_extraction" / "odb_metrics_pair.json"
FINAL_PASS = "PASS_ABQPILOT_V2_STAGE1_9_METRICS_BASED_COMPARISON_REPORT_READY"


def main() -> int:
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    metrics_pair = _read_json(SOURCE_METRICS)
    comparison_report = build_comparison_report(metrics_pair, SOURCE_METRICS)
    agent_observation = build_agent_observation(comparison_report)
    markdown = render_markdown_report(comparison_report)

    _write_json(RUN_DIR / "comparison_report.json", comparison_report)
    (RUN_DIR / "comparison_report.md").write_text(markdown, encoding="utf-8")
    _write_json(RUN_DIR / "agent_observation.json", agent_observation)

    final = {
        "verdict": FINAL_PASS,
        "source_metrics_path": str(SOURCE_METRICS),
        "artifacts_written": [
            str(RUN_DIR / "comparison_report.json"),
            str(RUN_DIR / "comparison_report.md"),
            str(RUN_DIR / "agent_observation.json"),
            str(RUN_DIR / "trace.json"),
            str(RUN_DIR / "trace.md"),
            str(RUN_DIR / "final_verdict.json"),
        ],
        "key_ratios": {
            "NT_max": comparison_report["metric_comparisons"].get("NT_max", {}).get("ratio"),
            "S_Mises_max": comparison_report["metric_comparisons"].get("S_Mises_max", {}).get("ratio"),
        },
        "interpretation_summary": comparison_report["interpretation"]["summary"],
    }
    trace = {
        "source_metrics_path": str(SOURCE_METRICS),
        "metrics_pair": metrics_pair,
        "comparison_report": comparison_report,
        "agent_observation": agent_observation,
        "final_verdict": final,
    }
    _write_json(RUN_DIR / "trace.json", trace)
    _write_trace_md(final, comparison_report)
    _write_json(RUN_DIR / "final_verdict.json", final)

    print(f"verdict={FINAL_PASS}")
    print(f"source_metrics={SOURCE_METRICS}")
    print(f"comparison_report={RUN_DIR / 'comparison_report.json'}")
    print(f"agent_observation={RUN_DIR / 'agent_observation.json'}")
    print(f"NT_max_ratio={final['key_ratios']['NT_max']}")
    print(f"S_Mises_max_ratio={final['key_ratios']['S_Mises_max']}")
    for item in final["interpretation_summary"]:
        print(f"interpretation={item}")
    return 0


def _write_trace_md(final: dict, comparison_report: dict) -> None:
    lines = [
        "# Stage 1.9 Metrics-Based Comparison Report",
        "",
        f"- Verdict: {final['verdict']}",
        f"- Source metrics: {final['source_metrics_path']}",
        f"- NT_max ratio: {final['key_ratios']['NT_max']}",
        f"- S_Mises_max ratio: {final['key_ratios']['S_Mises_max']}",
        "",
        "## Interpretation",
    ]
    for item in comparison_report["interpretation"]["summary"]:
        lines.append(f"- {item}")
    (RUN_DIR / "trace.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
