from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from abqpilot.odb import OdbMetricsExtractor


RUN_DIR = PROJECT_ROOT / "runs" / "stage1_8_gated_odb_metrics_extraction"
CONTRACT_PATH = PROJECT_ROOT / "runs" / "stage1_7_manual_solver_output_intake" / "odb_metrics_extraction_contract.json"
FINAL_PASS = "PASS_ABQPILOT_V2_STAGE1_8_GATED_ODB_METRICS_EXTRACTION_READY"


def main() -> int:
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    config = _load_runtime_config(PROJECT_ROOT / "abqpilot" / "configs" / "abaqus_runtime.yaml")
    extractor = OdbMetricsExtractor(
        abaqus_command=str(config["abaqus_command"]),
        allow_odb_read=bool(config["allow_odb_read"]),
        odb_read_mode=str(config["odb_read_mode"]),
        allow_solver_submit=bool(config["allow_solver_submit"]),
        allow_abqjobpilot=bool(config["allow_abqjobpilot"]),
        allow_llm=bool(config["allow_llm"]),
        timeout_s=600,
    )

    request = extractor.prepare_request(CONTRACT_PATH, RUN_DIR)
    report = extractor.extract(request)
    metrics = _read_json(Path(request["metrics_json_path"])) if Path(request["metrics_json_path"]).exists() else {}

    summary_md = _write_summary_md(metrics, report)
    final = {
        "verdict": report["verdict"],
        "executed": report["executed"],
        "metrics_json_path": request["metrics_json_path"],
        "report_path": str(RUN_DIR / "odb_metrics_extraction_report.json"),
        "case_count": len(metrics.get("cases", [])),
        "cases": [
            {
                "case_id": case.get("case_id"),
                "role": case.get("role"),
                "status": case.get("status"),
                "temperature_field_used": case.get("temperature_field_used"),
                "missing_fields": case.get("missing_fields", []),
                "metrics": case.get("metrics", {}),
            }
            for case in metrics.get("cases", [])
        ],
        "comparison": metrics.get("comparison", {}),
    }
    _write_json(RUN_DIR / "final_verdict.json", final)
    trace = {
        "contract_path": str(CONTRACT_PATH),
        "request": request,
        "report": report,
        "metrics": metrics,
        "metrics_comparison_summary": summary_md,
        "final_verdict": final,
    }
    _write_json(RUN_DIR / "trace.json", trace)
    _write_trace_md(final, request, report)

    print(f"verdict={report['verdict']}")
    print(f"executed={str(report['executed']).lower()}")
    print(f"command={report.get('command')}")
    print(f"metrics_json={request['metrics_json_path']}")
    print(f"report={RUN_DIR / 'odb_metrics_extraction_report.json'}")
    for case in metrics.get("cases", []):
        metric_text = ", ".join(f"{key}={value}" for key, value in case.get("metrics", {}).items())
        print(
            f"case={case.get('case_id')} status={case.get('status')} "
            f"temp={case.get('temperature_field_used')} {metric_text}"
        )
    return 0 if report["verdict"] == FINAL_PASS else 1


def _write_summary_md(metrics: dict, report: dict) -> str:
    lines = [
        "# Stage 1.8 ODB Metrics Comparison",
        "",
        f"- Verdict: {report['verdict']}",
        f"- Executed: {str(report['executed']).lower()}",
        "",
        "## Cases",
    ]
    for case in metrics.get("cases", []):
        lines.append(f"- {case.get('case_id')} ({case.get('role')}): {case.get('status')}")
        lines.append(f"  - Temperature field: {case.get('temperature_field_used')}")
        for key, value in case.get("metrics", {}).items():
            lines.append(f"  - {key}: {value}")
        for missing in case.get("missing_fields", []):
            lines.append(f"  - Missing {missing.get('field')}: {missing.get('missing_reason')}")

    comparison = metrics.get("comparison", {})
    lines.extend(["", "## Comparison"])
    for group_name, group in comparison.items():
        lines.append(f"- {group_name}")
        for key, value in group.items():
            lines.append(f"  - {key}: {value}")
    text = "\n".join(lines) + "\n"
    (RUN_DIR / "metrics_comparison_summary.md").write_text(text, encoding="utf-8")
    return text


def _write_trace_md(final: dict, request: dict, report: dict) -> None:
    lines = [
        "# Stage 1.8 Gated ODB Metrics Extraction",
        "",
        f"- Verdict: {final['verdict']}",
        f"- Executed: {str(final['executed']).lower()}",
        f"- Extract script: {request['script_path']}",
        f"- Metrics JSON: {request['metrics_json_path']}",
        f"- Command: {report.get('command')}",
        "",
        "## Cases",
    ]
    for case in final.get("cases", []):
        lines.append(f"- {case['case_id']}: status={case['status']}, metrics={case['metrics']}")
    (RUN_DIR / "trace.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _load_runtime_config(path: Path) -> dict:
    runtime: dict[str, object] = {}
    in_runtime = False
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        if raw_line.startswith("runtime:"):
            in_runtime = True
            continue
        if not in_runtime or not raw_line.startswith("  "):
            continue
        key, value = raw_line.strip().split(":", 1)
        runtime[key] = _parse_scalar(value.strip())
    return runtime


def _parse_scalar(value: str) -> object:
    lowered = value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    try:
        return int(value)
    except ValueError:
        return value


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
