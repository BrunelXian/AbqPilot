from __future__ import annotations

from pathlib import Path


SUCCESS_TOKENS = [
    "THE ANALYSIS HAS COMPLETED SUCCESSFULLY",
    "COMPLETED SUCCESSFULLY",
    "COMPLETED",
]
FAILURE_TOKENS = [
    "ABAQUS/ANALYSIS EXITED WITH ERRORS",
    "THE ANALYSIS HAS NOT BEEN COMPLETED",
    "ABAQUS ERROR",
]


def classify_solver_status(case_inventory: dict) -> dict:
    case_id = case_inventory.get("case_id")
    if case_inventory.get("lock_exists"):
        return _report(case_id, "RUNNING_OR_LOCKED", ["lock file present"])

    text_paths = [
        case_inventory.get("sta_path"),
        case_inventory.get("msg_path"),
        case_inventory.get("dat_path"),
        case_inventory.get("log_path"),
    ]
    combined = "\n".join(_read_text(path) for path in text_paths if path)
    upper = combined.upper()
    success_hits = [token for token in SUCCESS_TOKENS if token in upper]
    failure_hits = [token for token in FAILURE_TOKENS if token in upper]
    if _has_failure_error_line(combined):
        failure_hits.append("ERROR")

    if success_hits and failure_hits:
        return _report(case_id, "UNKNOWN", success_hits + failure_hits)
    if failure_hits:
        return _report(case_id, "FAILED", failure_hits)
    if success_hits:
        return _report(case_id, "COMPLETED", success_hits)
    return _report(case_id, "UNKNOWN", [])


def _report(case_id: str | None, status: str, signals: list[str]) -> dict:
    return {
        "case_id": case_id,
        "status": status,
        "signals": signals,
    }


def _read_text(path: str) -> str:
    file_path = Path(path)
    if not file_path.exists():
        return ""
    return file_path.read_text(encoding="utf-8", errors="replace")


def _has_failure_error_line(text: str) -> bool:
    for line in text.splitlines():
        upper = line.strip().upper()
        if not upper:
            continue
        if "ERROR TOLERANCE" in upper or "0 ERROR" in upper:
            continue
        if upper.startswith("ERROR") or " ERROR:" in upper or upper.startswith("***ERROR"):
            return True
    return False
