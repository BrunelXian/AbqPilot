from __future__ import annotations

import json
from pathlib import Path


def build_odb_metrics_contract(cases: list[dict]) -> dict:
    return {
        "cases": [
            {
                "case_id": case["case_id"],
                "role": case["expected_role"],
                "odb_path": case.get("odb_path"),
            }
            for case in cases
        ],
        "temperature_field_candidates": ["NT11", "NT"],
        "stress_field": "S",
        "heated_region_status": "TARGET_REGION_NOT_CONFIRMED",
        "frame_selection": {
            "preferred": "last_frame",
            "cooling_time_s": 100.0,
        },
        "metrics": [
            "NT_max",
            "NT_mean_global",
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
            "base_case": "base_power_1x",
            "power_x2_case": "power_x2",
            "purpose": "Quantify temperature and residual-stress differences caused by doubling the heat input while preserving all other model definitions.",
        },
        "default_behavior": "contract_only_no_odb_read",
    }


def write_odb_metrics_contract(path: str | Path, cases: list[dict]) -> dict:
    contract = build_odb_metrics_contract(cases)
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(contract, indent=2, ensure_ascii=False), encoding="utf-8")
    return contract


def write_odb_extractor_preview(path: str | Path, contract_path: str | Path) -> str:
    text = f'''# PREVIEW_ONLY_NOT_EXECUTED
# Future Abaqus Python noGUI script for Stage 1.7 metrics extraction.
# This file is generated as a contract preview only and must not be executed by
# the Stage 1.7 default runner.

from odbAccess import openOdb
import json

contract_path = r"{Path(contract_path)}"
output_path = "odb_metrics_pair.json"

with open(contract_path, "r") as handle:
    contract = json.load(handle)

results = {{"cases": []}}

for case in contract["cases"]:
    odb = openOdb(path=case["odb_path"], readOnly=True)
    try:
        step = list(odb.steps.values())[-1]
        frame = step.frames[-1]
        fields = frame.fieldOutputs
        temperature_name = "NT11" if "NT11" in fields else "NT"
        temperature = fields[temperature_name]
        stress = fields["S"]
        # Placeholder: compute global max/mean and optional region metrics here.
        results["cases"].append({{
            "case_id": case["case_id"],
            "role": case["role"],
            "temperature_field": temperature_name,
            "metrics_status": "PREVIEW_ONLY_NOT_EXECUTED",
        }})
    finally:
        odb.close()

with open(output_path, "w") as handle:
    json.dump(results, handle, indent=2)
'''
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    return text

