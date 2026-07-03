from __future__ import annotations

import re
from pathlib import Path
from typing import Any


MAX_READ_BYTES = 2_000_000
TAIL_LINES = 80

COMPLETION_PATTERNS = [
    r"THE ANALYSIS HAS COMPLETED SUCCESSFULLY",
    r"THE ANALYSIS HAS COMPLETED\b",
    r"Abaqus JOB .* COMPLETED",
    r"COMPLETED SUCCESSFULLY",
]
TERMINAL_FAILURE_PATTERNS = [
    r"THE ANALYSIS HAS NOT BEEN COMPLETED",
    r"TOO MANY ATTEMPTS MADE FOR THIS INCREMENT",
    r"ANALYSIS HAS BEEN TERMINATED",
    r"TERMINATED DUE TO PREVIOUS ERRORS",
    r"INPUT FILE PROCESSOR exited with an error",
    r"Abaqus Error",
    r"\*\*\*ERROR",
    r"\bERROR:",
]
INPUT_PROCESSOR_PATTERNS = [
    r"Analysis Input File Processor exited with an error",
    r"Begin Analysis Input File Processor",
    r"Run pre\.exe",
    r"Unknown assembly set",
    r"Unknown part instance",
    r"Unknown node set",
    r"Unknown element set",
    r"Missing data",
    r"The keyword is misplaced",
    r"This keyword is not available",
]
INPUT_PROCESSOR_ERROR_PATTERNS = [
    r"Analysis Input File Processor exited with an error",
    r"INPUT FILE PROCESSOR exited with an error",
    r"Unknown assembly set",
    r"Unknown part instance",
    r"Unknown node set",
    r"Unknown element set",
    r"Missing data",
    r"The keyword is misplaced",
    r"This keyword is not available",
]
CONVERGENCE_PATTERNS = [
    r"Too many attempts made for this increment",
    r"Too many attempts",
    r"too many increments",
    r"time increment required is less than",
    r"convergence",
    r"severe discontinuity",
]
NUMERICAL_PATTERNS = [
    r"zero pivot",
    r"negative eigenvalue",
    r"singular",
    r"instability",
    r"rigid body motion",
    r"ill-conditioned",
    r"excessive distortion",
    r"negative volume",
]
MESH_PATTERNS = [
    r"element distortion",
    r"excessive distortion",
    r"negative volume",
    r"badly shaped element",
    r"hourglass",
]
CONTACT_PATTERNS = [
    r"contact convergence",
    r"overclosure",
    r"tie constraint",
    r"coupling constraint",
    r"duplicate constraint",
    r"constraint conflict",
]
MATERIAL_PATTERNS = [
    r"invalid material",
    r"plastic data",
    r"temperature-dependent material",
    r"user material",
    r"\bUMAT\b",
    r"\bVUMAT\b",
    r"negative plastic",
]
THERMAL_PATTERNS = [
    r"temperature degree of freedom",
    r"temperature-displacement",
    r"coupled temp-displacement",
    r"heat flux",
    r"thermal boundary",
    r"NT11",
]
LICENSE_ENV_PATTERNS = [
    r"not enough licenses",
    r"license.*(error|failed|failure|denied|unavailable)",
    r"(error|failed|failure|denied|unavailable).*license",
    r"FlexNet.*(error|failed|failure|denied|unavailable)",
    r"Abaqus License Manager.*(error|failed|failure|denied|unavailable)",
    r"not enough licenses",
    r"permission denied",
    r"access denied",
    r"disk.*(full|error|failed|failure)",
    r"memory allocation",
    r"path too long",
    r"compiler.*(error|failed|failure)",
]


def parse_job_logs(files: dict[str, Path]) -> dict[str, Any]:
    texts = {key: _read_text(path) for key, path in files.items() if key in {"dat", "msg", "sta", "log", "com", "prt"}}
    all_text = "\n".join(texts.values())
    attempt = _latest_attempt_text(all_text)
    decision_text = attempt["text"] or all_text
    error_lines = {
        "dat_error_lines": _matching_lines(_attempt_file_text(texts.get("dat", ""), attempt), TERMINAL_FAILURE_PATTERNS),
        "msg_error_lines": _matching_lines(_attempt_file_text(texts.get("msg", ""), attempt), TERMINAL_FAILURE_PATTERNS),
        "log_error_lines": _matching_lines(_attempt_file_text(texts.get("log", ""), attempt), TERMINAL_FAILURE_PATTERNS),
    }
    warnings = {
        "dat_warning_lines": _matching_lines(_attempt_file_text(texts.get("dat", ""), attempt), [r"\bWARNING\b", r"\*\*\*WARNING"]),
        "msg_warning_lines": _matching_lines(_attempt_file_text(texts.get("msg", ""), attempt), [r"\bWARNING\b", r"\*\*\*WARNING"]),
    }
    return {
        "text_by_file": texts,
        "flags": {
            "input_processor_seen": _has_any(decision_text, INPUT_PROCESSOR_PATTERNS),
            "input_processor_error": _has_any(decision_text, INPUT_PROCESSOR_ERROR_PATTERNS),
            "solver_started": _has_any(decision_text, [r"Begin Abaqus/Standard Analysis", r"Run standard\.exe"]),
            "analysis_completed": _has_any(decision_text, COMPLETION_PATTERNS),
            "analysis_not_completed": _has_any(decision_text, [r"THE ANALYSIS HAS NOT BEEN COMPLETED"]),
            "too_many_attempts": _has_any(decision_text, [r"TOO MANY ATTEMPTS MADE FOR THIS INCREMENT", r"Too many attempts"]),
            "terminated_due_to_errors": _has_any(decision_text, [r"TERMINATED DUE TO PREVIOUS ERRORS", r"ANALYSIS HAS BEEN TERMINATED"]),
            "completed_line_found": _has_any(decision_text, COMPLETION_PATTERNS),
            "error_lines_found": any(error_lines.values()) or _has_any(decision_text, [r"\*\*\*ERROR", r"\bERROR:"]),
            "warning_lines_found": any(warnings.values()),
            "license_error": _has_any(decision_text, LICENSE_ENV_PATTERNS),
            "environment_error": _has_any(
                decision_text,
                [
                    r"permission denied",
                    r"access denied",
                    r"disk.*(full|error|failed|failure)",
                    r"memory allocation",
                    r"path too long",
                    r"compiler.*(error|failed|failure)",
                ],
            ),
            "terminal_failure": _has_any(decision_text, TERMINAL_FAILURE_PATTERNS),
            "convergence_failure": _has_any(decision_text, CONVERGENCE_PATTERNS),
            "numerical_instability": _has_any(decision_text, NUMERICAL_PATTERNS),
            "mesh_distortion": _has_any(decision_text, MESH_PATTERNS),
            "contact_constraint_failure": _has_any(decision_text, CONTACT_PATTERNS),
            "material_model_failure": _has_any(decision_text, MATERIAL_PATTERNS),
            "thermal_coupling_failure": _has_any(decision_text, THERMAL_PATTERNS),
            "attempt_markers_found": attempt["markers_found"],
            "latest_attempt_parsing_required": False,
            "parser_mode": "latest_attempt_block" if attempt["markers_found"] else "whole_file",
        },
        "important_lines": {
            **error_lines,
            "sta_tail": _tail_lines(texts.get("sta", "")),
            "log_tail": _tail_lines(texts.get("log", "")),
            "dat_warning_lines": warnings["dat_warning_lines"][:20],
            "msg_warning_lines": warnings["msg_warning_lines"][:20],
        },
        "failure_location": _failure_location(texts.get("sta", "")),
        "attempt": {
            "markers_found": attempt["markers_found"],
            "label": attempt["label"],
            "parser_mode": "latest_attempt_block" if attempt["markers_found"] else "whole_file",
        },
    }


def _read_text(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return ""
    data = path.read_bytes()
    if len(data) > MAX_READ_BYTES:
        data = data[-MAX_READ_BYTES:]
    return data.decode("utf-8", errors="replace")


def _has_any(text: str, patterns: list[str]) -> bool:
    return any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in patterns)


def _matching_lines(text: str, patterns: list[str], limit: int = 40) -> list[str]:
    matched: list[str] = []
    for line in text.splitlines():
        if _has_any(line, patterns):
            matched.append(line.strip())
            if len(matched) >= limit:
                break
    return matched


def _tail_lines(text: str, limit: int = TAIL_LINES) -> list[str]:
    return [line.rstrip() for line in text.splitlines()[-limit:]]


def _failure_location(sta_text: str) -> dict[str, int | None]:
    last_step: int | None = None
    last_increment: int | None = None
    for raw in sta_text.splitlines():
        parts = raw.split()
        if len(parts) >= 2 and parts[0].isdigit() and parts[1].isdigit():
            last_step = int(parts[0])
            last_increment = int(parts[1])
    return {
        "failure_step": last_step,
        "failure_increment": last_increment,
        "last_step": last_step,
        "last_increment": last_increment,
    }


def _latest_attempt_text(text: str) -> dict[str, Any]:
    lines = text.splitlines()
    start_indices: list[tuple[int, str]] = []
    for index, line in enumerate(lines):
        match = re.search(r"\bSTART\s+([A-Z0-9_\- ]+)", line, flags=re.IGNORECASE)
        if match:
            start_indices.append((index, match.group(1).strip()))
    if not start_indices:
        return {"markers_found": False, "label": None, "text": ""}
    start, label = start_indices[-1]
    end = len(lines)
    for index in range(start + 1, len(lines)):
        if re.search(r"\bEND\s+", lines[index], flags=re.IGNORECASE):
            end = index + 1
            break
    return {"markers_found": True, "label": label, "text": "\n".join(lines[start:end])}


def _attempt_file_text(text: str, attempt: dict[str, Any]) -> str:
    if not attempt.get("markers_found"):
        return text
    latest = _latest_attempt_text(text)
    return latest["text"] if latest.get("markers_found") and latest.get("text") else text
