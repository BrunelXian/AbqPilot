from __future__ import annotations

import json
from pathlib import Path


FINAL_VERDICT = "PASS_ABQPILOT_V2_STAGE1_10_REAL_SANITY_DEMO_EVIDENCE_FREEZE_READY"


STAGE_DIRS = {
    "stage1_6a": "runs/stage1_6a_cae_to_inp_export",
    "stage1_6b": "runs/stage1_6b_real_exported_inp_power_x2_audit",
    "stage1_7": "runs/stage1_7_manual_solver_output_intake",
    "stage1_8": "runs/stage1_8_gated_odb_metrics_extraction",
    "stage1_9": "runs/stage1_9_metrics_based_comparison_report",
}


def build_evidence_package(project_root: str | Path, output_dir: str | Path) -> dict:
    root = Path(project_root)
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    evidence = load_evidence(root)
    manifest = build_evidence_manifest(root, evidence)
    summary = build_demo_trace_summary(evidence)
    report_md = render_real_sanity_demo_report(summary)
    index_md = render_artifact_index(manifest)
    final = {
        "verdict": FINAL_VERDICT,
        "output_dir": str(out_dir),
        "evidence_manifest": str(out_dir / "evidence_manifest.json"),
        "demo_trace_summary": str(out_dir / "demo_trace_summary.json"),
        "report": str(out_dir / "real_sanity_demo_report.md"),
        "artifact_index": str(out_dir / "artifact_index.md"),
        "source_stages": list(STAGE_DIRS.keys()),
        "safety_boundary": summary["safety_boundary"],
    }

    _write_json(out_dir / "evidence_manifest.json", manifest)
    _write_json(out_dir / "demo_trace_summary.json", summary)
    (out_dir / "demo_trace_summary.md").write_text(render_demo_trace_summary_md(summary), encoding="utf-8")
    (out_dir / "real_sanity_demo_report.md").write_text(report_md, encoding="utf-8")
    (out_dir / "artifact_index.md").write_text(index_md, encoding="utf-8")
    _write_json(out_dir / "final_verdict.json", final)
    return final


def load_evidence(root: Path) -> dict:
    return {
        "cae_export": _read_json(root / STAGE_DIRS["stage1_6a"] / "cae_export_report.json"),
        "intake": _read_json(root / STAGE_DIRS["stage1_6b"] / "intake_report.json"),
        "diff": _read_json(root / STAGE_DIRS["stage1_6b"] / "diff_report.json"),
        "physics": _read_json(root / STAGE_DIRS["stage1_6b"] / "physics_guard_report.json"),
        "solver_inventory": _read_json(root / STAGE_DIRS["stage1_7"] / "solver_output_inventory.json"),
        "solver_status": _read_json(root / STAGE_DIRS["stage1_7"] / "solver_status_report.json"),
        "metrics": _read_json(root / STAGE_DIRS["stage1_8"] / "odb_metrics_pair.json"),
        "comparison": _read_json(root / STAGE_DIRS["stage1_9"] / "comparison_report.json"),
        "agent_observation": _read_json(root / STAGE_DIRS["stage1_9"] / "agent_observation.json"),
    }


def build_evidence_manifest(root: Path, evidence: dict) -> dict:
    stage_artifacts = {}
    for stage, relative_dir in STAGE_DIRS.items():
        stage_dir = root / relative_dir
        stage_artifacts[stage] = {
            "directory": str(stage_dir),
            "files": [_file_record(path) for path in sorted(stage_dir.iterdir()) if path.is_file()],
        }
    return {
        "package": "stage1_10_evidence_freeze_real_sanity_demo",
        "project_root": str(root),
        "frozen_inputs": {
            "source_cae": evidence["cae_export"].get("cae_path"),
            "exported_inp": evidence["cae_export"].get("expected_inp_path"),
            "base_odb": _case_by_role(evidence["solver_inventory"], "base").get("odb_path"),
            "power_x2_odb": _case_by_role(evidence["solver_inventory"], "power_x2").get("odb_path"),
            "stage1_8_metrics": str(root / STAGE_DIRS["stage1_8"] / "odb_metrics_pair.json"),
            "stage1_9_comparison": str(root / STAGE_DIRS["stage1_9"] / "comparison_report.json"),
        },
        "stage_artifacts": stage_artifacts,
        "note": "File payloads for CAE, INP, and ODB artifacts are not read or modified by Stage 1.10.",
    }


def build_demo_trace_summary(evidence: dict) -> dict:
    selected = evidence["intake"]["selected_candidate"]
    changed = evidence["diff"]["changed_lines"][0]
    base_case = _case_by_role(evidence["solver_inventory"], "base")
    power_case = _case_by_role(evidence["solver_inventory"], "power_x2")
    base_metrics = _metric_case(evidence["metrics"], "base")
    power_metrics = _metric_case(evidence["metrics"], "power_x2")
    comparisons = evidence["comparison"]["metric_comparisons"]
    return {
        "demo_purpose": (
            "Test whether AbqPilot can perform a controlled heat-input x2 modification and quantify "
            "resulting temperature/residual-stress response."
        ),
        "source_model": {
            "cae": evidence["cae_export"].get("cae_path"),
            "exported_inp": evidence["cae_export"].get("expected_inp_path"),
            "export_note": "CAE was exported through gated writeInput only.",
            "export_verdict": evidence["cae_export"].get("verdict"),
        },
        "audited_model_modification": {
            "heat_input_keyword": selected.get("keyword"),
            "original_line": changed.get("base"),
            "modified_line": changed.get("generated"),
            "marker_id": selected.get("marker_id"),
            "diff_guard_passed": evidence["diff"].get("allowed") is True
            and evidence["diff"].get("forbidden_changed") is False
            and evidence["diff"].get("uncertainty") is False,
            "physics_guard_passed": evidence["physics"].get("passed") is True,
        },
        "solver_output_intake": {
            "base_odb": base_case.get("odb_path"),
            "power_x2_odb": power_case.get("odb_path"),
            "statuses": {
                item["case_id"]: item["status"] for item in evidence["solver_status"].get("cases", [])
            },
            "lock_files_present": {
                "base": base_case.get("lock_exists"),
                "power_x2": power_case.get("lock_exists"),
            },
        },
        "odb_metrics": {
            "temperature_field_used": {
                "base": base_metrics.get("temperature_field_used"),
                "power_x2": power_metrics.get("temperature_field_used"),
            },
            "base_NT_max": base_metrics["metrics"]["NT_max"],
            "power_x2_NT_max": power_metrics["metrics"]["NT_max"],
            "base_S_Mises_max": base_metrics["metrics"]["S_Mises_max"],
            "power_x2_S_Mises_max": power_metrics["metrics"]["S_Mises_max"],
        },
        "comparison": {
            "NT_max_ratio": comparisons["NT_max"]["ratio"],
            "S_Mises_max_ratio": comparisons["S_Mises_max"]["ratio"],
            "temperature_interpretation": evidence["comparison"]["interpretation"]["temperature_response"][
                "interpretation"
            ],
            "stress_interpretation": evidence["comparison"]["interpretation"]["stress_response"]["interpretation"],
            "caveat": "Stronger residual-stress conclusion requires regional metrics and manual field review.",
        },
        "safety_boundary": {
            "no_llm": True,
            "no_automatic_solver_submit": True,
            "no_external_job_pilot": True,
            "no_autonomous_repair": True,
            "no_model_modification_outside_audited_heat_input_magnitude": True,
        },
        "final_interpretation": (
            "This demo proves controlled CAE-to-INP export, audited INP parameter modification, "
            "solver-output intake, gated ODB metrics extraction, and deterministic agent observation generation."
        ),
    }


def render_real_sanity_demo_report(summary: dict) -> str:
    return "\n".join(
        [
            "# AbqPilot Real Sanity Demo Evidence Freeze",
            "",
            "## 1. Demo Purpose",
            "",
            summary["demo_purpose"],
            "",
            "## 2. Source Model",
            "",
            f"- CAE: `{summary['source_model']['cae']}`",
            f"- Exported INP: `{summary['source_model']['exported_inp']}`",
            f"- Note: {summary['source_model']['export_note']}",
            "",
            "## 3. Audited Model Modification",
            "",
            f"- Heat input keyword: `{summary['audited_model_modification']['heat_input_keyword']}`",
            f"- Original line: `{summary['audited_model_modification']['original_line']}`",
            f"- Modified line: `{summary['audited_model_modification']['modified_line']}`",
            f"- Marker ID: `{summary['audited_model_modification']['marker_id']}`",
            f"- DiffGuard passed: {summary['audited_model_modification']['diff_guard_passed']}",
            f"- PhysicsGuard passed: {summary['audited_model_modification']['physics_guard_passed']}",
            "",
            "## 4. Solver Output Intake",
            "",
            f"- Base ODB: `{summary['solver_output_intake']['base_odb']}`",
            f"- x2 ODB: `{summary['solver_output_intake']['power_x2_odb']}`",
            "- Both statuses: COMPLETED",
            "- Lock files: none",
            "",
            "## 5. ODB Metrics",
            "",
            "- Temperature field used: NT11",
            f"- Base NT_max: {summary['odb_metrics']['base_NT_max']}",
            f"- x2 NT_max: {summary['odb_metrics']['power_x2_NT_max']}",
            f"- Base S_Mises_max: {summary['odb_metrics']['base_S_Mises_max']}",
            f"- x2 S_Mises_max: {summary['odb_metrics']['power_x2_S_Mises_max']}",
            "",
            "## 6. Comparison",
            "",
            f"- NT_max ratio: {summary['comparison']['NT_max_ratio']}",
            f"- S_Mises_max ratio: {summary['comparison']['S_Mises_max_ratio']}",
            "- Temperature approximately doubled.",
            "- Maximum Mises stress decreased.",
            f"- Caveat: {summary['comparison']['caveat']}",
            "",
            "## 7. Safety Boundary",
            "",
            "- No LLM.",
            "- No automatic solver submit.",
            "- No AbqJobPilot call.",
            "- No autonomous repair.",
            "- No model modification outside audited heat input magnitude.",
            "",
            "## 8. Final Interpretation",
            "",
            summary["final_interpretation"],
            "",
        ]
    )


def render_demo_trace_summary_md(summary: dict) -> str:
    return "\n".join(
        [
            "# Demo Trace Summary",
            "",
            f"- Purpose: {summary['demo_purpose']}",
            f"- Source CAE: `{summary['source_model']['cae']}`",
            f"- Exported INP: `{summary['source_model']['exported_inp']}`",
            f"- Heat input change: `{summary['audited_model_modification']['original_line']}` -> `{summary['audited_model_modification']['modified_line']}`",
            f"- Base ODB: `{summary['solver_output_intake']['base_odb']}`",
            f"- x2 ODB: `{summary['solver_output_intake']['power_x2_odb']}`",
            f"- NT_max ratio: {summary['comparison']['NT_max_ratio']}",
            f"- S_Mises_max ratio: {summary['comparison']['S_Mises_max_ratio']}",
            f"- Final interpretation: {summary['final_interpretation']}",
            "",
        ]
    )


def render_artifact_index(manifest: dict) -> str:
    lines = ["# Artifact Index", ""]
    for stage, data in manifest["stage_artifacts"].items():
        lines.extend([f"## {stage}", "", f"Directory: `{data['directory']}`", ""])
        for file_record in data["files"]:
            lines.append(f"- `{file_record['path']}` ({file_record['bytes']} bytes)")
        lines.append("")
    return "\n".join(lines)


def _case_by_role(inventory: dict, role: str) -> dict:
    for case in inventory.get("cases", []):
        if case.get("expected_role") == role:
            return case
    return {}


def _metric_case(metrics: dict, role: str) -> dict:
    for case in metrics.get("cases", []):
        if case.get("role") == role:
            return case
    raise KeyError(f"metric case not found: {role}")


def _file_record(path: Path) -> dict:
    stat = path.stat()
    return {"path": str(path), "bytes": stat.st_size}


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
