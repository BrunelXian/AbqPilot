from __future__ import annotations

from pathlib import Path

from abqpilot.builders.heat_flux_patch_builder import NUMBER_RE, locate_single_heat_flux_marker


FORBIDDEN_KEYWORDS = [
    "*Material",
    "*Elastic",
    "*Plastic",
    "*Density",
    "*Conductivity",
    "*Specific Heat",
    "*Expansion",
    "*Node",
    "*Element",
    "*Nset",
    "*Elset",
    "*Solid Section",
    "*Shell Section",
    "*Boundary",
    "*Contact",
    "*Surface Interaction",
]


class DiffGuard:
    def compare(self, base_inp_path: str | Path, generated_inp_path: str | Path) -> dict:
        base_path = Path(base_inp_path)
        generated_path = Path(generated_inp_path)
        report = {
            "tool": "DiffGuard",
            "base_inp_path": str(base_path),
            "generated_inp_path": str(generated_path),
            "allowed": False,
            "forbidden_changed": False,
            "uncertainty": False,
            "changed_lines": [],
            "errors": [],
        }

        if not base_path.exists() or not generated_path.exists():
            report["errors"].append("base or generated INP is missing")
            report["uncertainty"] = True
            return report

        base_lines = base_path.read_text(encoding="utf-8").splitlines(keepends=True)
        gen_lines = generated_path.read_text(encoding="utf-8").splitlines(keepends=True)

        if len(base_lines) != len(gen_lines):
            report["errors"].append("line counts differ; alignment is ambiguous")
            report["uncertainty"] = True
            return report

        base_marker = locate_single_heat_flux_marker(base_lines)
        gen_marker = locate_single_heat_flux_marker(gen_lines)
        if not base_marker["ok"] or not gen_marker["ok"]:
            report["errors"].append("missing or ambiguous editable heat flux marker")
            report["uncertainty"] = True
            return report
        if (
            base_marker["marker_id"] != gen_marker["marker_id"]
            or base_marker["start_idx"] != gen_marker["start_idx"]
            or base_marker["end_idx"] != gen_marker["end_idx"]
            or base_marker["data_idx"] != gen_marker["data_idx"]
        ):
            report["errors"].append("editable heat flux marker alignment changed")
            report["uncertainty"] = True
            return report

        forbidden_base = _forbidden_ranges(base_lines)
        forbidden_gen = _forbidden_ranges(gen_lines)
        normalized_base = _normalize_allowed_magnitude(base_lines, base_marker["data_idx"])
        normalized_gen = _normalize_allowed_magnitude(gen_lines, gen_marker["data_idx"])

        for idx, (base_line, gen_line) in enumerate(zip(base_lines, gen_lines, strict=True)):
            if base_line != gen_line:
                in_forbidden = idx in forbidden_base or idx in forbidden_gen
                if in_forbidden:
                    report["forbidden_changed"] = True
                report["changed_lines"].append(
                    {
                        "line_index": idx,
                        "base": base_line.rstrip("\r\n"),
                        "generated": gen_line.rstrip("\r\n"),
                        "forbidden_section": in_forbidden,
                    }
                )

        if normalized_base != normalized_gen:
            report["errors"].append("changes exceed the allowed heat flux magnitude token")

        report["allowed"] = (
            normalized_base == normalized_gen
            and not report["forbidden_changed"]
            and not report["uncertainty"]
            and not report["errors"]
        )
        return report


def _keyword_name(line: str) -> str | None:
    stripped = line.strip().lower()
    if not stripped.startswith("*") or stripped.startswith("**"):
        return None
    return stripped.split(",", 1)[0]


def _is_forbidden_keyword(line: str) -> bool:
    keyword = _keyword_name(line)
    if keyword is None:
        return False
    return any(keyword == forbidden.lower() for forbidden in FORBIDDEN_KEYWORDS)


def _forbidden_ranges(lines: list[str]) -> set[int]:
    forbidden: set[int] = set()
    active = False
    for idx, line in enumerate(lines):
        keyword = _keyword_name(line)
        if keyword is not None:
            active = _is_forbidden_keyword(line)
        if active:
            forbidden.add(idx)
    return forbidden


def _normalize_allowed_magnitude(lines: list[str], data_idx: int) -> list[str]:
    normalized = list(lines)
    line = normalized[data_idx]
    newline = "\r\n" if line.endswith("\r\n") else "\n" if line.endswith("\n") else ""
    text = line.rstrip("\r\n")
    match = NUMBER_RE.match(text)
    if match:
        normalized[data_idx] = f"{match.group('prefix')}<ABQPILOT_HEAT_FLUX_MAGNITUDE>{match.group('suffix')}{newline}"
    return normalized

