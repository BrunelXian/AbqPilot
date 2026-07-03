from __future__ import annotations

import difflib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from abqpilot.patching.dflux_lifecycle_schema import INSERTED_KEYWORD


PATCH_COMMENT = "** ABQPILOT_PATCH: explicit DFLUX reset at cooling step start"


@dataclass(frozen=True)
class StepBlock:
    name: str
    start: int
    end: int


def preview_dflux_deactivation_patch(
    source_inp: str | Path,
    preview_inp: str | Path,
    scan_step: str = "step_scan_00",
    cooling_step: str = "Step_cool_00",
) -> dict[str, Any]:
    source = Path(source_inp)
    preview = Path(preview_inp)
    lines = source.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)
    source_sha = _sha256(source)
    scan = _find_step(lines, scan_step)
    cool = _find_step(lines, cooling_step)
    errors: list[str] = []
    if scan is None:
        errors.append(f"scan step not found: {scan_step}")
    if cool is None:
        errors.append(f"cooling step not found: {cooling_step}")
    if scan and not _step_has_dflux_bf(lines, scan):
        errors.append("scan-step DFLUX/BF load not found")
    if errors:
        return {
            "status": "DFLUX_DEACTIVATION_PATCH_PREVIEW_BLOCKED",
            "allowed": False,
            "errors": errors,
            "source_inp": str(source),
            "preview_inp": str(preview),
            "source_sha256_before": source_sha,
            "source_sha256_after": _sha256(source),
            "source_inp_unchanged": True,
        }
    assert cool is not None
    if _cooling_has_op_new(lines, cool):
        new_lines = list(lines)
        insertion_index = None
        inserted_lines: list[dict[str, Any]] = []
        status = "DFLUX_DEACTIVATION_PATCH_PREVIEW_ALREADY_PRESENT"
    else:
        insertion_index = _find_cooling_insertion_index(lines, cool)
        inserted = [_with_newline(PATCH_COMMENT, lines), _with_newline(INSERTED_KEYWORD, lines)]
        new_lines = lines[:insertion_index] + inserted + lines[insertion_index:]
        inserted_lines = [
            {"line": insertion_index + 1, "text": PATCH_COMMENT},
            {"line": insertion_index + 2, "text": INSERTED_KEYWORD},
        ]
        status = "DFLUX_DEACTIVATION_PATCH_PREVIEW_APPLIED"
    preview.parent.mkdir(parents=True, exist_ok=True)
    preview.write_text("".join(new_lines), encoding="utf-8")
    return {
        "status": status,
        "allowed": True,
        "source_inp": str(source),
        "preview_inp": str(preview),
        "scan_step": scan_step,
        "cooling_step": cooling_step,
        "inserted_keyword": INSERTED_KEYWORD,
        "insertion_line": insertion_index + 1 if insertion_index is not None else None,
        "inserted_lines": inserted_lines,
        "inserted_lines_count": len(inserted_lines),
        "source_sha256_before": source_sha,
        "source_sha256_after": _sha256(source),
        "preview_sha256": _sha256(preview),
        "source_inp_unchanged": source_sha == _sha256(source),
    }


def validate_dflux_lifecycle(
    source_inp: str | Path,
    preview_inp: str | Path,
    scan_step: str = "step_scan_00",
    cooling_step: str = "Step_cool_00",
) -> dict[str, Any]:
    source = Path(source_inp)
    preview = Path(preview_inp)
    source_lines = source.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)
    preview_lines = preview.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)
    scan = _find_step(preview_lines, scan_step)
    cool = _find_step(preview_lines, cooling_step)
    scan_preserved = bool(scan and _step_has_dflux_bf(preview_lines, scan))
    cooling_op_new = bool(cool and _cooling_has_op_new(preview_lines, cool))
    positive_bf = _positive_bf_lines(preview_lines, cool) if cool else []
    diff_report = build_lifecycle_diff_report(source_lines, preview_lines, source, preview, cooling_step)
    passed = scan_preserved and cooling_op_new and not positive_bf and diff_report["allowed"]
    return {
        "tool": "DFLUXLifecycleValidator",
        "passed": passed,
        "scan_step_bf_preserved": scan_preserved,
        "cooling_step_has_dflux_op_new": cooling_op_new,
        "cooling_step_positive_bf_lines": len(positive_bf),
        "positive_bf_lines": positive_bf,
        "unrelated_changes_count": diff_report["unrelated_changes_count"],
        "errors": [] if passed else _validation_errors(scan_preserved, cooling_op_new, positive_bf, diff_report),
        "diff_report": diff_report,
    }


def build_lifecycle_diff_report(
    source_lines: list[str],
    preview_lines: list[str],
    source_path: Path,
    preview_path: Path,
    cooling_step: str,
) -> dict[str, Any]:
    diff = list(difflib.ndiff(source_lines, preview_lines))
    inserted = [line[2:].rstrip("\r\n") for line in diff if line.startswith("+ ")]
    deleted = [line[2:].rstrip("\r\n") for line in diff if line.startswith("- ")]
    changed = [line for line in diff if line.startswith("- ") or line.startswith("+ ")]
    expected_inserted = [PATCH_COMMENT, INSERTED_KEYWORD]
    already_present = not inserted and not deleted and source_lines == preview_lines
    allowed_insert = inserted == expected_inserted and not deleted
    allowed = already_present or allowed_insert
    unrelated = 0 if allowed else len(changed)
    return {
        "tool": "DFLUXLifecycleDiffGuard",
        "base_inp_path": str(source_path),
        "generated_inp_path": str(preview_path),
        "allowed": allowed,
        "cooling_step": cooling_step,
        "inserted_lines_count": len(inserted),
        "changed_lines_count": 0,
        "deleted_lines_count": len(deleted),
        "unrelated_changes_count": unrelated,
        "inserted_lines": inserted,
        "deleted_lines": deleted,
        "errors": [] if allowed else ["diff contains changes outside the explicit DFLUX reset insertion"],
    }


def _find_step(lines: list[str], name: str) -> StepBlock | None:
    start = None
    step_name = None
    for idx, line in enumerate(lines):
        stripped = line.strip()
        if stripped.lower().startswith("*step"):
            if start is not None:
                return None
            parsed = _step_name(stripped)
            if parsed == name:
                start = idx
                step_name = parsed
        elif start is not None and stripped.lower().startswith("*end step"):
            return StepBlock(step_name or name, start, idx)
    return None


def _find_cooling_insertion_index(lines: list[str], step: StepBlock) -> int:
    idx = step.start + 1
    while idx < step.end:
        stripped = lines[idx].strip()
        if stripped and stripped.startswith("*") and not stripped.startswith("**"):
            idx += 1
            while idx < step.end:
                data = lines[idx].strip()
                if data.startswith("*") or data.startswith("**"):
                    break
                idx += 1
            return idx
        idx += 1
    return step.start + 1


def _step_name(line: str) -> str | None:
    for part in line.split(","):
        part = part.strip()
        if part.lower().startswith("name="):
            return part.split("=", 1)[1]
    return None


def _step_has_dflux_bf(lines: list[str], step: StepBlock) -> bool:
    has_dflux = False
    has_bf = False
    for line in lines[step.start : step.end + 1]:
        low = line.lower()
        if low.strip().startswith("*dflux"):
            has_dflux = True
        if ", bf" in low:
            has_bf = True
    return has_dflux and has_bf


def _cooling_has_op_new(lines: list[str], step: StepBlock) -> bool:
    for line in lines[step.start : step.end + 1]:
        low = line.lower().replace(" ", "")
        if low.startswith("*dflux") and "op=new" in low:
            return True
    return False


def _positive_bf_lines(lines: list[str], step: StepBlock) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    for offset, line in enumerate(lines[step.start : step.end + 1], step.start + 1):
        low = line.lower()
        if ", bf" not in low:
            continue
        parts = [part.strip().replace("D", "E").replace("d", "e") for part in line.split(",")]
        try:
            value = float(parts[-1])
        except (ValueError, IndexError):
            value = 1.0
        if value > 0:
            found.append({"line": offset, "text": line.rstrip("\r\n")})
    return found


def _validation_errors(scan_preserved: bool, cooling_op_new: bool, positive_bf: list[dict[str, Any]], diff: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not scan_preserved:
        errors.append("scan-step BF heat flux was not preserved")
    if not cooling_op_new:
        errors.append("cooling step does not contain *Dflux, OP=NEW")
    if positive_bf:
        errors.append("cooling step contains positive BF heat flux lines")
    if not diff.get("allowed"):
        errors.extend(diff.get("errors", []))
    return errors


def _with_newline(text: str, lines: list[str]) -> str:
    newline = "\r\n" if any(line.endswith("\r\n") for line in lines[:50]) else "\n"
    return text + newline


def _sha256(path: Path) -> str:
    import hashlib

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
