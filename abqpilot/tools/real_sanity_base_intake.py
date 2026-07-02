from __future__ import annotations

import json
import re
from pathlib import Path


HEAT_INPUT_KEYWORDS = {"*dsflux", "*cflux", "*dflux"}
MARKER_ID = "HF_REAL_SANITY_BASE_001"
START_MARKER = f"** ABQPILOT_EDITABLE_HEAT_FLUX_START id={MARKER_ID}"
END_MARKER = f"** ABQPILOT_EDITABLE_HEAT_FLUX_END id={MARKER_ID}"
NUMBER_RE = re.compile(
    r"^(?P<prefix>.*,\s*)(?P<value>[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[Ee][+-]?\d+)?)(?P<suffix>\s*)$"
)


def detect_heat_input(source_inp_path: str | Path) -> dict:
    path = Path(source_inp_path)
    report = _base_report(path)
    if not path.exists():
        report["verdict"] = "FAIL_NO_HEAT_INPUT_FOUND"
        report["errors"].append("source INP does not exist")
        return report

    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    if any("ABQPILOT_EDITABLE_HEAT_FLUX" in line for line in lines):
        report["verdict"] = "FAIL_UNSUPPORTED_HEAT_INPUT_FORMAT"
        report["errors"].append("source INP already contains an AbqPilot heat flux marker")
        return report

    heat_keyword_indices = [
        idx for idx, line in enumerate(lines) if _keyword_name(line) in HEAT_INPUT_KEYWORDS
    ]
    if not heat_keyword_indices:
        report["verdict"] = "FAIL_NO_HEAT_INPUT_FOUND"
        return report

    candidates = []
    unsupported = []
    for keyword_idx in heat_keyword_indices:
        data_indices = _heat_data_indices(lines, keyword_idx)
        if len(data_indices) != 1:
            unsupported.append(
                {
                    "keyword_line_index": keyword_idx,
                    "keyword": lines[keyword_idx].strip(),
                    "data_line_count": len(data_indices),
                }
            )
            continue
        data_idx = data_indices[0]
        data_text = lines[data_idx].rstrip("\r\n")
        match = NUMBER_RE.match(data_text)
        if not match:
            unsupported.append(
                {
                    "keyword_line_index": keyword_idx,
                    "keyword": lines[keyword_idx].strip(),
                    "data_line_index": data_idx,
                    "data_line": data_text,
                    "reason": "data line did not end with a numeric magnitude",
                }
            )
            continue
        candidates.append(
            {
                "keyword": lines[keyword_idx].strip(),
                "keyword_line_index": keyword_idx,
                "data_line_index": data_idx,
                "data_line": data_text,
                "original_magnitude": float(match.group("value")),
                "magnitude_token": match.group("value"),
                "marker_id": MARKER_ID,
            }
        )

    report["candidates"] = candidates
    report["unsupported_candidates"] = unsupported

    if len(candidates) == 1 and not unsupported:
        report.update(
            {
                "verdict": "HEAT_INPUT_DETECTED",
                "ok": True,
                "selected_candidate": candidates[0],
            }
        )
        return report
    if len(candidates) > 1:
        report["verdict"] = "FAIL_AMBIGUOUS_HEAT_INPUT_CANDIDATES"
        return report
    if unsupported:
        report["verdict"] = "FAIL_UNSUPPORTED_HEAT_INPUT_FORMAT"
        return report

    report["verdict"] = "FAIL_NO_HEAT_INPUT_FOUND"
    return report


def write_marker_base(source_inp_path: str | Path, output_inp_path: str | Path, intake_report: dict) -> dict:
    source = Path(source_inp_path)
    output = Path(output_inp_path)
    report = {
        "source_inp_path": str(source),
        "output_inp_path": str(output),
        "marker_id": MARKER_ID,
        "ok": False,
        "errors": [],
    }
    if not intake_report.get("ok"):
        report["errors"].append("intake report did not contain exactly one supported heat input")
        return report

    selected = intake_report["selected_candidate"]
    lines = source.read_text(encoding="utf-8").splitlines(keepends=True)
    keyword_idx = selected["keyword_line_index"]
    data_idx = selected["data_line_index"]
    if data_idx != keyword_idx + 1:
        report["errors"].append("unsupported heat input block layout")
        return report

    original_data_line = lines[data_idx].rstrip("\r\n")
    marked_lines = (
        lines[:keyword_idx]
        + [_with_newline(START_MARKER, lines[keyword_idx])]
        + lines[keyword_idx : data_idx + 1]
        + [_with_newline(END_MARKER, lines[data_idx])]
        + lines[data_idx + 1 :]
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("".join(marked_lines), encoding="utf-8", newline="")

    written_lines = output.read_text(encoding="utf-8").splitlines()
    data_line_after = written_lines[data_idx + 1]
    report.update(
        {
            "ok": data_line_after == original_data_line,
            "keyword": selected["keyword"],
            "original_magnitude": selected["original_magnitude"],
            "data_line_before": original_data_line,
            "data_line_after": data_line_after,
            "inserted_marker_lines": [keyword_idx, data_idx + 2],
        }
    )
    if not report["ok"]:
        report["errors"].append("marker insertion changed the heat input data line")
    return report


def write_residual_stress_metrics_plan(path: str | Path) -> dict:
    plan = {
        "cooling_time_s": 100.0,
        "final_frame_metrics": [
            "NT11_max",
            "NT11_mean",
            "S_Mises_max",
            "S_Mises_mean_global",
            "S_Mises_mean_heated_region",
        ],
        "optional_metrics": [
            "S11_mean_heated_region",
            "S22_mean_heated_region",
            "S33_mean_heated_region",
            "U2_max",
            "PEEQ_max",
        ],
        "comparison": {
            "base_case": "base_heatflux_marker",
            "power_x2_case": "generated_power_x2",
            "purpose": "Compare temperature and residual stress response after doubling heat input while all other model definitions remain unchanged.",
        },
    }
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(plan, indent=2, ensure_ascii=False), encoding="utf-8")
    return plan


def write_manual_solver_handoff(path: str | Path, base_inp_path: str | Path, generated_inp_path: str | Path) -> str:
    text = f"""# Manual Solver Handoff

PREVIEW_ONLY_NOT_EXECUTED

Use these INP files for later manual Abaqus solving and residual-stress comparison:

- Base case: {Path(base_inp_path)}
- Power x2 case: {Path(generated_inp_path)}

Suggested manual workflow:

1. Review both INP files.
2. Run the base and power x2 cases manually in Abaqus using your normal solver workflow.
3. After both jobs complete, compare the final cooling-frame temperature and residual-stress metrics described in residual_stress_metrics_plan.json.

No command in this file was executed by AbqPilot.
"""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    return text


def _base_report(path: Path) -> dict:
    return {
        "tool": "RealSanityBaseIntake",
        "source_inp_path": str(path),
        "ok": False,
        "verdict": None,
        "candidates": [],
        "unsupported_candidates": [],
        "errors": [],
    }


def _keyword_name(line: str) -> str | None:
    stripped = line.strip().lower()
    if not stripped.startswith("*") or stripped.startswith("**"):
        return None
    return stripped.split(",", 1)[0]


def _heat_data_indices(lines: list[str], keyword_idx: int) -> list[int]:
    data_indices = []
    for idx in range(keyword_idx + 1, len(lines)):
        stripped = lines[idx].strip()
        if stripped.startswith("*"):
            break
        if not stripped or stripped.startswith("**"):
            continue
        data_indices.append(idx)
    return data_indices


def _with_newline(text: str, sibling_line: str) -> str:
    if sibling_line.endswith("\r\n"):
        return text + "\r\n"
    return text + "\n"
