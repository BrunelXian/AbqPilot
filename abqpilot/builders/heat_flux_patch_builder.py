from __future__ import annotations

import re
from pathlib import Path

from abqpilot.builders.base import Builder


START_RE = re.compile(r"^\*\*\s+ABQPILOT_EDITABLE_HEAT_FLUX_START\s+id=(?P<id>\S+)\s*$")
END_RE = re.compile(r"^\*\*\s+ABQPILOT_EDITABLE_HEAT_FLUX_END\s+id=(?P<id>\S+)\s*$")
NUMBER_RE = re.compile(
    r"^(?P<prefix>.*,\s*)(?P<value>[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[Ee][+-]?\d+)?)(?P<suffix>\s*)$"
)


def _newline_suffix(line: str) -> str:
    if line.endswith("\r\n"):
        return "\r\n"
    if line.endswith("\n"):
        return "\n"
    return ""


def locate_single_heat_flux_marker(lines: list[str]) -> dict:
    starts: list[tuple[int, str]] = []
    ends: list[tuple[int, str]] = []
    for idx, line in enumerate(lines):
        stripped = line.rstrip("\r\n")
        start_match = START_RE.match(stripped)
        end_match = END_RE.match(stripped)
        if start_match:
            starts.append((idx, start_match.group("id")))
        if end_match:
            ends.append((idx, end_match.group("id")))

    if len(starts) != 1 or len(ends) != 1:
        return {"ok": False, "reason": "expected exactly one editable heat flux marker block"}

    start_idx, start_id = starts[0]
    end_idx, end_id = ends[0]
    if start_id != end_id or end_idx <= start_idx:
        return {"ok": False, "reason": "marker block ids or ordering are invalid"}

    data_candidates: list[int] = []
    for idx in range(start_idx + 1, end_idx):
        text = lines[idx].strip()
        if not text or text.startswith("**") or text.startswith("*"):
            continue
        data_candidates.append(idx)

    if len(data_candidates) != 1:
        return {"ok": False, "reason": "expected exactly one editable heat flux data line"}

    data_idx = data_candidates[0]
    data_text = lines[data_idx].rstrip("\r\n")
    number_match = NUMBER_RE.match(data_text)
    if not number_match:
        return {"ok": False, "reason": "editable heat flux magnitude was not numeric"}

    return {
        "ok": True,
        "marker_id": start_id,
        "start_idx": start_idx,
        "end_idx": end_idx,
        "data_idx": data_idx,
        "original_magnitude": float(number_match.group("value")),
        "number_match": number_match,
    }


class HeatFluxPatchBuilder(Builder):
    def build(self, build_request: dict) -> dict:
        base_path = Path(build_request["base_inp_path"])
        output_path = Path(build_request["generated_inp_path"])
        scale = float(build_request.get("parameters", {}).get("heat_flux_scale", 1.0))

        status = {
            "builder": "HeatFluxPatchBuilder",
            "allowed": False,
            "generated_inp_path": str(output_path),
            "errors": [],
            "changes": [],
        }

        if scale <= 0:
            status["errors"].append("heat_flux_scale must be positive")
            return status

        if not base_path.exists():
            status["errors"].append(f"base INP does not exist: {base_path}")
            return status

        lines = base_path.read_text(encoding="utf-8").splitlines(keepends=True)
        marker = locate_single_heat_flux_marker(lines)
        if not marker["ok"]:
            status["errors"].append(marker["reason"])
            return status

        match = marker["number_match"]
        original = marker["original_magnitude"]
        updated = original * scale
        line = lines[marker["data_idx"]]
        newline = _newline_suffix(line)
        replacement = f"{match.group('prefix')}{updated:.10g}{match.group('suffix')}{newline}"
        lines[marker["data_idx"]] = replacement

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text("".join(lines), encoding="utf-8", newline="")

        status.update(
            {
                "allowed": True,
                "marker_id": marker["marker_id"],
                "original_magnitude": original,
                "updated_magnitude": updated,
                "heat_flux_scale": scale,
                "changes": [
                    {
                        "line_index": marker["data_idx"],
                        "field": "heat_flux_magnitude",
                        "from": original,
                        "to": updated,
                    }
                ],
            }
        )
        return status

