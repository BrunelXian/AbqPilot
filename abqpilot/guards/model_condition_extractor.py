from __future__ import annotations

import re
from pathlib import Path
from typing import Any


STEP_CREATE_RE = re.compile(r"\.(?P<kind>[A-Za-z_]*Step)\((?P<body>.*?)\)", re.DOTALL)
NAME_RE = re.compile(r"name\s*=\s*'([^']+)'")
PREVIOUS_RE = re.compile(r"previous\s*=\s*'([^']+)'")
LOAD_RE = re.compile(r"\.(?P<kind>BodyHeatFlux|[A-Za-z]*Load|[A-Za-z]*Flux)\((?P<body>.*?)\)", re.DOTALL)
CREATE_STEP_RE = re.compile(r"createStepName\s*=\s*'([^']+)'")
MAG_RE = re.compile(r"magnitude\s*=\s*([0-9.eE+-]+)")
DEACTIVATE_RE = re.compile(r"loads\['([^']+)'\]\.deactivate\('([^']+)'\)")
SET_VALUES_RE = re.compile(r"loads\['([^']+)'\]\.setValuesInStep\((.*?)\)", re.DOTALL)


def extract_jnl_conditions(path: str | Path) -> dict[str, Any]:
    source = Path(path)
    text = source.read_text(encoding="utf-8", errors="replace")
    loads: dict[str, dict[str, Any]] = {}
    steps: list[str] = []
    evidence: list[dict[str, Any]] = []
    lines = text.splitlines()

    for match in STEP_CREATE_RE.finditer(text):
        body = match.group("body")
        name = _first(NAME_RE, body)
        if name and name not in steps:
            steps.append(name)
            evidence.append(_line_evidence(lines, match.start(), f"step created: {name}"))

    for match in LOAD_RE.finditer(text):
        body = match.group("body")
        name = _first(NAME_RE, body)
        if not name:
            continue
        created_step = _first(CREATE_STEP_RE, body)
        magnitude_raw = _first(MAG_RE, body)
        loads[name] = {
            "name": name,
            "kind": match.group("kind"),
            "created_step": created_step,
            "deactivated_steps": [],
            "set_values_in_step": [],
            "magnitude": float(magnitude_raw) if magnitude_raw else None,
            "evidence_lines": [_line_evidence(lines, match.start(), f"load created: {name}")],
        }

    for match in DEACTIVATE_RE.finditer(text):
        name, step = match.groups()
        item = loads.setdefault(name, {"name": name, "kind": "unknown", "created_step": None, "deactivated_steps": [], "set_values_in_step": [], "magnitude": None, "evidence_lines": []})
        item.setdefault("deactivated_steps", []).append(step)
        item.setdefault("evidence_lines", []).append(_line_evidence(lines, match.start(), f"load deactivated: {name} in {step}"))

    for match in SET_VALUES_RE.finditer(text):
        name = match.group(1)
        item = loads.setdefault(name, {"name": name, "kind": "unknown", "created_step": None, "deactivated_steps": [], "set_values_in_step": [], "magnitude": None, "evidence_lines": []})
        item.setdefault("set_values_in_step", []).append(match.group(2).strip())

    return {
        "schema_version": "0.1",
        "source_type": "jnl",
        "path": str(source),
        "steps": steps,
        "loads": list(loads.values()),
        "boundaries": [],
        "interactions": [],
        "amplitudes": _extract_amplitudes_from_jnl(text),
        "evidence_lines": evidence,
        "parse_errors": [],
    }


def extract_inp_conditions(path: str | Path) -> dict[str, Any]:
    source = Path(path)
    lines = source.read_text(encoding="utf-8", errors="replace").splitlines()
    steps = _step_blocks(lines)
    parsed_steps = [_parse_step(lines, step) for step in steps]
    return {
        "schema_version": "0.1",
        "source_type": "inp",
        "path": str(source),
        "steps": parsed_steps,
        "amplitudes": _extract_inp_amplitudes(lines),
        "output_request_blocks": _keyword_lines(lines, ["*output"]),
        "reference_names": sorted(_reference_names(parsed_steps)),
        "parse_errors": [],
    }


def _parse_step(lines: list[str], step: dict[str, Any]) -> dict[str, Any]:
    block = lines[step["start_line"] - 1 : step["end_line"]]
    dflux_keywords: list[dict[str, Any]] = []
    positive_bf: list[dict[str, Any]] = []
    zero_bf: list[dict[str, Any]] = []
    boundary_blocks: list[dict[str, Any]] = []
    other_load_blocks: list[dict[str, Any]] = []
    output_blocks: list[dict[str, Any]] = []
    for offset, raw in enumerate(block, step["start_line"]):
        stripped = raw.strip()
        low = stripped.lower()
        if low.startswith("*dflux"):
            dflux_keywords.append({"line": offset, "text": stripped, "op": _keyword_op(stripped)})
        elif ", bf" in low:
            item = {"line": offset, "text": stripped, "value": _last_float(stripped), "reference": stripped.split(",", 1)[0].strip()}
            if item["value"] == 0:
                zero_bf.append(item)
            elif item["value"] is None or item["value"] > 0:
                positive_bf.append(item)
        elif low.startswith("*boundary"):
            boundary_blocks.append({"line": offset, "text": stripped, "op": _keyword_op(stripped)})
        elif low.startswith(("*cload", "*dload", "*dsload", "*film", "*sfilm")):
            other_load_blocks.append({"line": offset, "text": stripped, "op": _keyword_op(stripped)})
        elif low.startswith("*output"):
            output_blocks.append({"line": offset, "text": stripped})
    return {
        **step,
        "dflux": {
            "has_dflux": bool(dflux_keywords),
            "op": dflux_keywords[-1]["op"] if dflux_keywords else "none",
            "keywords": dflux_keywords,
            "positive_bf_lines": positive_bf,
            "zero_bf_lines": zero_bf,
            "has_dflux_op_new": any(item["op"] == "NEW" for item in dflux_keywords),
        },
        "boundary": {"blocks": boundary_blocks},
        "other_loads": {"blocks": other_load_blocks},
        "output_requests": {"blocks": output_blocks},
    }


def _step_blocks(lines: list[str]) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    active: dict[str, Any] | None = None
    for idx, raw in enumerate(lines, 1):
        stripped = raw.strip()
        if stripped.lower().startswith("*step"):
            active = {"name": _step_name(stripped), "start_line": idx, "keyword": stripped}
        elif stripped.lower().startswith("*end step") and active:
            active["end_line"] = idx
            found.append(active)
            active = None
    return found


def _keyword_op(line: str) -> str:
    normalized = line.replace(" ", "")
    for part in normalized.split(","):
        if part.lower().startswith("op="):
            return part.split("=", 1)[1].upper()
    return "none"


def _step_name(line: str) -> str | None:
    for part in line.split(","):
        part = part.strip()
        if part.lower().startswith("name="):
            return part.split("=", 1)[1]
    return None


def _last_float(line: str) -> float | None:
    try:
        return float(line.split(",")[-1].strip().replace("D", "E").replace("d", "e"))
    except ValueError:
        return None


def _reference_names(steps: list[dict[str, Any]]) -> set[str]:
    refs: set[str] = set()
    for step in steps:
        for line in step.get("dflux", {}).get("positive_bf_lines", []) + step.get("dflux", {}).get("zero_bf_lines", []):
            if line.get("reference"):
                refs.add(str(line["reference"]))
    return refs


def _keyword_lines(lines: list[str], prefixes: list[str]) -> list[dict[str, Any]]:
    return [{"line": idx, "text": raw.strip()} for idx, raw in enumerate(lines, 1) if raw.strip().lower().startswith(tuple(prefixes))]


def _extract_inp_amplitudes(lines: list[str]) -> list[dict[str, Any]]:
    return _keyword_lines(lines, ["*amplitude"])


def _extract_amplitudes_from_jnl(text: str) -> list[dict[str, Any]]:
    return [{"text": line.strip()} for line in text.splitlines() if "Amplitude" in line]


def _first(pattern: re.Pattern[str], text: str) -> str | None:
    match = pattern.search(text)
    return match.group(1) if match else None


def _line_evidence(lines: list[str], char_offset: int, note: str) -> dict[str, Any]:
    running = 0
    for idx, line in enumerate(lines, 1):
        running += len(line) + 1
        if running >= char_offset:
            return {"line": idx, "text": line.strip(), "note": note}
    return {"line": None, "text": "", "note": note}
