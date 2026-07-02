from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from abqpilot.builders.heat_flux_patch_builder import HeatFluxPatchBuilder
from abqpilot.tools.diff_guard_tool import DiffGuard
from abqpilot.tools.physics_guard_tool import PhysicsGuard
from abqpilot.tools.real_sanity_base_intake import (
    MARKER_ID,
    detect_heat_input,
    write_manual_solver_handoff,
    write_marker_base,
    write_residual_stress_metrics_plan,
)
from abqpilot.tools.static_validator_tool import StaticValidator


SOURCE_INP = PROJECT_ROOT / "runs" / "stage1_6a_cae_to_inp_export" / "sanity_base_v01_export.inp"
RUN_DIR = PROJECT_ROOT / "runs" / "stage1_6b_real_exported_inp_power_x2_audit"


def main() -> int:
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    base_inp = RUN_DIR / "base_heatflux_marker.inp"
    generated_inp = RUN_DIR / "generated_power_x2.inp"

    intake_report = detect_heat_input(SOURCE_INP)
    _write_json(RUN_DIR / "intake_report.json", intake_report)
    if not intake_report.get("ok"):
        final = _final(intake_report["verdict"], intake_report)
        _write_final_and_trace(final, {"intake_report": intake_report})
        _print_result(final)
        return 1

    marker_report = write_marker_base(SOURCE_INP, base_inp, intake_report)
    if not marker_report.get("ok"):
        final = _final("FAIL_UNSUPPORTED_HEAT_INPUT_FORMAT", marker_report)
        _write_final_and_trace(final, {"intake_report": intake_report, "marker_report": marker_report})
        _print_result(final)
        return 1

    build_request = {
        "builder": "HeatFluxPatchBuilder",
        "heat_flux_scale": 2.0,
        "marker_id": MARKER_ID,
        "source_inp": str(base_inp),
        "output_inp": str(generated_inp),
        "base_inp_path": str(base_inp),
        "generated_inp_path": str(generated_inp),
        "parameters": {"heat_flux_scale": 2.0},
    }
    _write_json(RUN_DIR / "build_request.json", build_request)
    build_status = HeatFluxPatchBuilder().build(build_request)
    _write_json(RUN_DIR / "build_status.json", build_status)
    if not build_status.get("allowed"):
        final = _final("FAIL_UNSUPPORTED_HEAT_INPUT_FORMAT", build_status)
        _write_final_and_trace(final, {"intake_report": intake_report, "build_status": build_status})
        _print_result(final)
        return 1

    validation_report = _validate_thermo_mechanical(generated_inp)
    _write_json(RUN_DIR / "validation_report.json", validation_report)
    if not validation_report.get("passed"):
        final = _final("FAIL_STATIC_VALIDATION", validation_report)
        _write_final_and_trace(
            final,
            {
                "intake_report": intake_report,
                "build_request": build_request,
                "build_status": build_status,
                "validation_report": validation_report,
            },
        )
        _print_result(final)
        return 1

    diff_report = DiffGuard().compare(base_inp, generated_inp)
    _write_json(RUN_DIR / "diff_report.json", diff_report)
    physics_guard_report = PhysicsGuard().check(diff_report)
    _write_json(RUN_DIR / "physics_guard_report.json", physics_guard_report)
    if not physics_guard_report.get("passed"):
        final = _final("FAIL_PHYSICS_GUARD", physics_guard_report)
        _write_final_and_trace(
            final,
            {
                "intake_report": intake_report,
                "build_request": build_request,
                "build_status": build_status,
                "validation_report": validation_report,
                "diff_report": diff_report,
                "physics_guard_report": physics_guard_report,
            },
        )
        _print_result(final)
        return 1

    metrics_plan = write_residual_stress_metrics_plan(RUN_DIR / "residual_stress_metrics_plan.json")
    manual_handoff = write_manual_solver_handoff(
        RUN_DIR / "manual_solver_handoff.md",
        base_inp,
        generated_inp,
    )

    selected = intake_report["selected_candidate"]
    final = {
        "verdict": "PASS_ABQPILOT_V2_STAGE1_6B_REAL_EXPORTED_INP_POWER_X2_PAIR_AUDIT_READY",
        "source_inp": str(SOURCE_INP),
        "base_inp": str(base_inp),
        "generated_inp": str(generated_inp),
        "heat_input_keyword": selected["keyword"],
        "marker_id": MARKER_ID,
        "original_magnitude": build_status["original_magnitude"],
        "doubled_magnitude": build_status["updated_magnitude"],
        "validation_passed": validation_report["passed"],
        "diff_guard_allowed": diff_report["allowed"],
        "physics_guard_passed": physics_guard_report["passed"],
    }
    _write_final_and_trace(
        final,
        {
            "intake_report": intake_report,
            "marker_report": marker_report,
            "build_request": build_request,
            "build_status": build_status,
            "validation_report": validation_report,
            "diff_report": diff_report,
            "physics_guard_report": physics_guard_report,
            "residual_stress_metrics_plan": metrics_plan,
            "manual_solver_handoff_preview_only": "PREVIEW_ONLY_NOT_EXECUTED" in manual_handoff,
        },
    )
    _print_result(final)
    return 0


def _validate_thermo_mechanical(inp_path: Path) -> dict:
    text = inp_path.read_text(encoding="utf-8", errors="replace")
    nt11_present = "nt11" in text.lower()
    temperature_token = "NT11" if nt11_present else "NT" if _has_output_token(text, "NT") else None
    stress_present = _has_output_token(text, "S")
    required_tokens = ["*Heading", "*Step", "*End Step", "*Output"]
    if temperature_token:
        required_tokens.append(temperature_token)
    else:
        required_tokens.append("NT11_OR_NT")
    required_tokens.append("S")
    report = StaticValidator().validate(inp_path, target_region=None, required_tokens=required_tokens)
    if not stress_present and "S" not in report["missing"]:
        report["missing"].append("S")
    if temperature_token is None and "NT11_OR_NT" not in report["missing"]:
        report["missing"].append("NT11_OR_NT")
    report["NT11_literal_present"] = nt11_present
    report["temperature_output_token"] = temperature_token
    report["target_region_status"] = "TARGET_REGION_NOT_CONFIRMED"
    report["passed"] = not report["missing"] and not report["errors"]
    return report


def _has_output_token(text: str, token: str) -> bool:
    target = token.lower()
    for line in text.splitlines():
        if line.lstrip().startswith("*") or line.lstrip().startswith("**"):
            continue
        tokens = [part.strip().lower() for part in line.split(",")]
        if target in tokens:
            return True
    return False


def _final(verdict: str, details: dict) -> dict:
    selected = details.get("selected_candidate", {})
    return {
        "verdict": verdict,
        "source_inp": str(SOURCE_INP),
        "marker_id": MARKER_ID,
        "heat_input_keyword": selected.get("keyword"),
        "original_magnitude": selected.get("original_magnitude"),
    }


def _write_final_and_trace(final_verdict: dict, payload: dict) -> None:
    _write_json(RUN_DIR / "final_verdict.json", final_verdict)
    trace = {
        "final_verdict": final_verdict,
        "source_inp": str(SOURCE_INP),
        "run_dir": str(RUN_DIR),
        **payload,
    }
    _write_json(RUN_DIR / "trace.json", trace)
    md = [
        "# Stage 1.6B Real Exported INP Power x2 Pair Audit",
        "",
        f"- Verdict: {final_verdict['verdict']}",
        f"- Source INP: {SOURCE_INP}",
        f"- Marker ID: {MARKER_ID}",
        f"- Original magnitude: {final_verdict.get('original_magnitude')}",
        f"- Doubled magnitude: {final_verdict.get('doubled_magnitude')}",
        "",
        "PREVIEW_ONLY_NOT_EXECUTED",
    ]
    (RUN_DIR / "trace.md").write_text("\n".join(md) + "\n", encoding="utf-8")


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _print_result(final: dict) -> None:
    print(f"verdict={final['verdict']}")
    print(f"keyword={final.get('heat_input_keyword')}")
    print(f"original_magnitude={final.get('original_magnitude')}")
    print(f"doubled_magnitude={final.get('doubled_magnitude')}")
    print(f"run_dir={RUN_DIR}")


if __name__ == "__main__":
    raise SystemExit(main())
