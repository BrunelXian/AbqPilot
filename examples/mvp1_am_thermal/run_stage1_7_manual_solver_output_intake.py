from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from abqpilot.tools.odb_metrics_contract import (
    write_odb_extractor_preview,
    write_odb_metrics_contract,
)
from abqpilot.tools.solver_output_intake import inventory_solver_outputs
from abqpilot.tools.solver_status_classifier import classify_solver_status


RUN_DIR = PROJECT_ROOT / "runs" / "stage1_7_manual_solver_output_intake"
STAGE_16B_DIR = PROJECT_ROOT / "runs" / "stage1_6b_real_exported_inp_power_x2_audit"
RUNS_DIR = PROJECT_ROOT / "runs"
SANITY_BASE_DIR = PROJECT_ROOT / "CAE_model" / "sanity_base"


def main() -> int:
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    search_roots = [STAGE_16B_DIR, RUNS_DIR, SANITY_BASE_DIR]
    inventory = inventory_solver_outputs(search_roots)
    _write_json(RUN_DIR / "solver_output_inventory.json", inventory)

    status_report = {
        "tool": "SolverStatusClassifier",
        "cases": [classify_solver_status(case) for case in inventory.get("cases", [])],
    }
    _write_json(RUN_DIR / "solver_status_report.json", status_report)

    final_verdict = _decide_final_verdict(inventory, status_report)
    contract = {}
    preview_written = False
    if final_verdict not in {"FAIL_SOLVER_OUTPUT_PAIR_NOT_FOUND", "FAIL_ODB_PAIR_NOT_FOUND"}:
        contract_path = RUN_DIR / "odb_metrics_extraction_contract.json"
        contract = write_odb_metrics_contract(contract_path, inventory["cases"])
        write_odb_extractor_preview(RUN_DIR / "extract_stage1_7_odb_metrics_preview.py", contract_path)
        preview_written = True
    else:
        _write_json(RUN_DIR / "odb_metrics_extraction_contract.json", {})
        (RUN_DIR / "extract_stage1_7_odb_metrics_preview.py").write_text(
            "# PREVIEW_ONLY_NOT_EXECUTED\n# No complete ODB pair found.\n",
            encoding="utf-8",
        )

    manual_next_steps = _write_manual_next_steps(inventory, final_verdict)
    final = {
        "verdict": final_verdict,
        "cases_detected": len(inventory.get("cases", [])),
        "odb_pair_found": all(case.get("odb_exists") for case in inventory.get("cases", []))
        and len(inventory.get("cases", [])) == 2,
        "statuses": status_report["cases"],
        "preview_written": preview_written,
    }
    _write_json(RUN_DIR / "final_verdict.json", final)
    trace = {
        "source_roots": [str(root) for root in search_roots],
        "inventory": inventory,
        "solver_status_report": status_report,
        "odb_metrics_extraction_contract": contract,
        "manual_next_steps_preview_only": "PREVIEW_ONLY_NOT_EXECUTED" in manual_next_steps,
        "final_verdict": final,
    }
    _write_json(RUN_DIR / "trace.json", trace)
    _write_trace_md(final, inventory, status_report)

    print(f"verdict={final_verdict}")
    print(f"cases_detected={len(inventory.get('cases', []))}")
    for case in inventory.get("cases", []):
        status = next((item["status"] for item in status_report["cases"] if item["case_id"] == case["case_id"]), "UNKNOWN")
        print(
            f"case={case['case_id']} role={case['expected_role']} "
            f"odb_exists={str(case['odb_exists']).lower()} "
            f"lock_exists={str(case['lock_exists']).lower()} status={status}"
        )
    print(f"run_dir={RUN_DIR}")
    return 0 if final_verdict == "PASS_ABQPILOT_V2_STAGE1_7_MANUAL_SOLVER_OUTPUT_INTAKE_READY" else 1


def _decide_final_verdict(inventory: dict, status_report: dict) -> str:
    cases = inventory.get("cases", [])
    if len(cases) != 2:
        return "FAIL_SOLVER_OUTPUT_PAIR_NOT_FOUND"
    if not all(case.get("odb_exists") for case in cases):
        return "FAIL_ODB_PAIR_NOT_FOUND"
    if any(item["status"] == "FAILED" for item in status_report.get("cases", [])):
        return "FAIL_SOLVER_OUTPUT_FAILED"
    return "PASS_ABQPILOT_V2_STAGE1_7_MANUAL_SOLVER_OUTPUT_INTAKE_READY"


def _write_manual_next_steps(inventory: dict, verdict: str) -> str:
    lines = [
        "# Stage 1.7 Manual Next Steps",
        "",
        "PREVIEW_ONLY_NOT_EXECUTED",
        "",
        f"Verdict: {verdict}",
        "",
        "Next manual step: review `odb_metrics_extraction_contract.json` and the preview extractor before any future explicitly approved ODB extraction.",
        "",
        "Detected cases:",
    ]
    for case in inventory.get("cases", []):
        lines.append(f"- {case['case_id']} ({case['expected_role']}): {case.get('odb_path')}")
    text = "\n".join(lines) + "\n"
    (RUN_DIR / "manual_next_steps.md").write_text(text, encoding="utf-8")
    return text


def _write_trace_md(final: dict, inventory: dict, status_report: dict) -> None:
    lines = [
        "# Stage 1.7 Manual Solver Output Intake",
        "",
        f"- Verdict: {final['verdict']}",
        f"- Cases detected: {final['cases_detected']}",
        f"- ODB pair found: {final['odb_pair_found']}",
        "",
        "## Cases",
    ]
    for case in inventory.get("cases", []):
        status = next((item["status"] for item in status_report["cases"] if item["case_id"] == case["case_id"]), "UNKNOWN")
        lines.append(f"- {case['case_id']}: role={case['expected_role']}, status={status}, odb={case.get('odb_path')}")
    lines.append("")
    lines.append("PREVIEW_ONLY_NOT_EXECUTED")
    (RUN_DIR / "trace.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())

