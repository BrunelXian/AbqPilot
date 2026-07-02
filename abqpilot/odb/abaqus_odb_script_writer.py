from __future__ import annotations

from pathlib import Path


def write_odb_metrics_script(
    script_path: str | Path,
    contract_path: str | Path,
    output_json_path: str | Path,
) -> Path:
    script = build_odb_metrics_script(contract_path=contract_path, output_json_path=output_json_path)
    path = Path(script_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(script, encoding="utf-8")
    return path


def build_odb_metrics_script(contract_path: str | Path, output_json_path: str | Path) -> str:
    return f'''from odbAccess import openOdb
from abaqusConstants import MISES
import json

CONTRACT_PATH = r"{Path(contract_path)}"
OUTPUT_JSON_PATH = r"{Path(output_json_path)}"


def scalar_values(field):
    values = []
    for item in field.values:
        data = item.data
        if isinstance(data, (list, tuple)):
            if data:
                values.append(float(data[0]))
        else:
            values.append(float(data))
    return values


def stats(values):
    if not values:
        return None, None
    return max(values), sum(values) / float(len(values))


def mises_values(stress_field):
    try:
        scalar = stress_field.getScalarField(invariant=MISES)
        return scalar_values(scalar), None
    except Exception as exc:
        values = []
        for item in stress_field.values:
            try:
                values.append(float(item.mises))
            except Exception:
                pass
        if values:
            return values, None
        return [], str(exc)


def extract_case(case, temperature_candidates, stress_name):
    result = {{
        "case_id": case["case_id"],
        "role": case["role"],
        "odb_path": case["odb_path"],
        "status": "METRICS_EXTRACTED",
        "last_step": None,
        "last_frame_time": None,
        "temperature_field_used": None,
        "metrics": {{}},
        "missing_fields": [],
    }}
    odb = openOdb(path=case["odb_path"], readOnly=True)
    try:
        step_names = list(odb.steps.keys())
        if not step_names:
            result["status"] = "METRICS_EXTRACTED_WITH_MISSING_FIELDS"
            result["missing_fields"].append({{"field": "steps", "missing_reason": "no steps in ODB"}})
            return result
        step_name = step_names[-1]
        step = odb.steps[step_name]
        result["last_step"] = step_name
        if not step.frames:
            result["status"] = "METRICS_EXTRACTED_WITH_MISSING_FIELDS"
            result["missing_fields"].append({{"field": "frames", "missing_reason": "no frames in last step"}})
            return result
        frame = step.frames[-1]
        result["last_frame_time"] = float(frame.frameValue)
        fields = frame.fieldOutputs

        temp_field = None
        for candidate in temperature_candidates:
            if candidate in fields:
                temp_field = fields[candidate]
                result["temperature_field_used"] = candidate
                break
        if temp_field is None:
            result["missing_fields"].append({{"field": "NT11_OR_NT", "missing_reason": "temperature field not found"}})
        else:
            nt_values = scalar_values(temp_field)
            nt_max, nt_mean = stats(nt_values)
            if nt_max is None:
                result["missing_fields"].append({{"field": result["temperature_field_used"], "missing_reason": "no scalar values"}})
            else:
                result["metrics"]["NT_max"] = nt_max
                result["metrics"]["NT_mean_global"] = nt_mean

        if stress_name not in fields:
            result["missing_fields"].append({{"field": stress_name, "missing_reason": "stress field not found"}})
        else:
            mises, missing_reason = mises_values(fields[stress_name])
            mises_max, mises_mean = stats(mises)
            if mises_max is None:
                result["missing_fields"].append({{"field": "S_Mises", "missing_reason": missing_reason or "no Mises values"}})
            else:
                result["metrics"]["S_Mises_max"] = mises_max
                result["metrics"]["S_Mises_mean_global"] = mises_mean

        if result["missing_fields"]:
            result["status"] = "METRICS_EXTRACTED_WITH_MISSING_FIELDS"
        return result
    finally:
        odb.close()


def safe_delta(left, right):
    if left is None or right is None:
        return None
    return right - left


def safe_ratio(base, power):
    if base in (None, 0):
        return None
    return power / base


with open(CONTRACT_PATH, "r") as handle:
    contract = json.load(handle)

case_results = [
    extract_case(case, contract.get("temperature_field_candidates", ["NT11", "NT"]), contract.get("stress_field", "S"))
    for case in contract["cases"]
]

by_role = dict((case["role"], case) for case in case_results)
base_metrics = by_role.get("base", {{}}).get("metrics", {{}})
power_metrics = by_role.get("power_x2", {{}}).get("metrics", {{}})

comparison = {{
    "power_x2_minus_base": {{
        "NT_max_delta": safe_delta(base_metrics.get("NT_max"), power_metrics.get("NT_max")),
        "NT_mean_global_delta": safe_delta(base_metrics.get("NT_mean_global"), power_metrics.get("NT_mean_global")),
        "S_Mises_max_delta": safe_delta(base_metrics.get("S_Mises_max"), power_metrics.get("S_Mises_max")),
        "S_Mises_mean_global_delta": safe_delta(base_metrics.get("S_Mises_mean_global"), power_metrics.get("S_Mises_mean_global")),
    }},
    "power_x2_over_base": {{
        "NT_max_ratio": safe_ratio(base_metrics.get("NT_max"), power_metrics.get("NT_max")),
        "NT_mean_global_ratio": safe_ratio(base_metrics.get("NT_mean_global"), power_metrics.get("NT_mean_global")),
        "S_Mises_max_ratio": safe_ratio(base_metrics.get("S_Mises_max"), power_metrics.get("S_Mises_max")),
        "S_Mises_mean_global_ratio": safe_ratio(base_metrics.get("S_Mises_mean_global"), power_metrics.get("S_Mises_mean_global")),
    }},
}}

payload = {{"cases": case_results, "comparison": comparison}}
with open(OUTPUT_JSON_PATH, "w") as handle:
    json.dump(payload, handle, indent=2)
'''

