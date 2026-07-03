from __future__ import annotations

import json
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "0.1"

PATH_FIELDS = {
    "inp_path": ["inp_path", "input_path", "input_file"],
    "work_dir": ["work_dir", "working_dir", "job_dir", "run_dir"],
    "sta_path": ["sta_path", "status_path"],
    "msg_path": ["msg_path", "message_path"],
    "dat_path": ["dat_path", "data_path"],
    "log_path": ["log_path"],
    "odb_path": ["odb_path", "output_odb_path"],
    "lck_path": ["lck_path", "lock_path"],
}


def load_abqjobpilot_report(report_json: str | Path) -> dict[str, Any]:
    path = Path(report_json)
    payload = _read_json(path)
    record = _extract_record(payload)
    return normalize_abqjobpilot_record(record, path, record_kind=_record_kind(path))


def load_abqjobpilot_record_by_job_id(job_id: str, runtime_dir: str | Path) -> dict[str, Any]:
    runtime = Path(runtime_dir)
    candidates: list[dict[str, Any]] = []
    for path in _runtime_record_paths(runtime):
        payload = _read_json(path)
        for record in _iter_records(payload):
            normalized = normalize_abqjobpilot_record(record, path, record_kind=_record_kind(path))
            if normalized.get("job_id") == job_id or normalized.get("raw_record", {}).get("id") == job_id:
                candidates.append(normalized)
    if not candidates:
        return {
            "record_source": "abqjobpilot",
            "schema_version": SCHEMA_VERSION,
            "record_path": None,
            "record_kind": "unknown",
            "job_id": job_id,
            "missing": True,
            "selection_reason": "NO_MATCHING_ABQJOBPILOT_RECORD",
            "raw_record": {},
        }
    selected = sorted(candidates, key=_record_sort_key, reverse=True)[0]
    selected["selection_reason"] = "newest_matching_report_by_mtime"
    return selected


def list_abqjobpilot_records(
    runtime_dir: str | Path,
    status: str | None = None,
    job_name: str | None = None,
    max_results: int | None = None,
) -> list[dict[str, Any]]:
    runtime = Path(runtime_dir)
    records: list[dict[str, Any]] = []
    for path in _runtime_record_paths(runtime):
        payload = _read_json(path)
        for record in _iter_records(payload):
            normalized = normalize_abqjobpilot_record(record, path, record_kind=_record_kind(path))
            if status and str(normalized.get("status") or "").upper() != status.upper():
                continue
            if job_name and job_name.lower() not in str(normalized.get("job_name") or "").lower():
                continue
            records.append(normalized)
    sorted_records = sorted(records, key=_record_sort_key, reverse=True)
    return sorted_records[:max_results] if max_results is not None else sorted_records


def normalize_abqjobpilot_record(
    record: dict[str, Any],
    record_path: str | Path | None = None,
    record_kind: str | None = None,
) -> dict[str, Any]:
    raw = record or {}
    work_dir = _first(raw, PATH_FIELDS["work_dir"])
    job_name = _first(raw, ["job_name", "name", "job"]) or _job_name_from_paths(raw)
    lck_path = _first(raw, PATH_FIELDS["lck_path"])
    lck_source = "abqjobpilot_record" if lck_path else None
    normalized = {
        "schema_version": SCHEMA_VERSION,
        "record_source": "abqjobpilot",
        "record_path": str(record_path) if record_path else None,
        "record_kind": record_kind or (_record_kind(Path(record_path)) if record_path else "unknown"),
        "job_id": _first(raw, ["job_id", "id", "queue_id"]),
        "status": _first(raw, ["status", "state"]),
        "job_name": job_name,
        "inp_path": _first(raw, PATH_FIELDS["inp_path"]),
        "work_dir": work_dir,
        "sta_path": _first(raw, PATH_FIELDS["sta_path"]),
        "msg_path": _first(raw, PATH_FIELDS["msg_path"]),
        "dat_path": _first(raw, PATH_FIELDS["dat_path"]),
        "log_path": _first(raw, PATH_FIELDS["log_path"]),
        "odb_path": _first(raw, PATH_FIELDS["odb_path"]),
        "lck_path": lck_path,
        "lck_path_source": lck_source,
        "fatal_reason": _first(raw, ["fatal_reason", "error", "error_message", "failure_reason"]),
        "return_code": _first(raw, ["return_code", "exit_code"]),
        "raw_status": _first(raw, ["status", "state"]),
        "raw_record": raw,
        "missing_fields": [],
        "selection_reason": None,
    }
    if not normalized["lck_path"] and normalized["odb_path"]:
        normalized["lck_path"] = str(Path(normalized["odb_path"]).with_suffix(".lck"))
        normalized["lck_path_source"] = "derived_from_odb_path"
    if work_dir and job_name:
        for field, suffix in {
            "sta_path": ".sta",
            "msg_path": ".msg",
            "dat_path": ".dat",
            "log_path": ".log",
            "odb_path": ".odb",
            "lck_path": ".lck",
        }.items():
            if not normalized[field]:
                normalized[field] = str(Path(work_dir) / f"{job_name}{suffix}")
                if field == "lck_path":
                    normalized["lck_path_source"] = "derived_from_job_name_and_work_dir"
    normalized["missing_fields"] = [
        key
        for key in ["job_id", "status", "job_name", "work_dir", "sta_path", "msg_path", "dat_path", "log_path", "odb_path"]
        if not normalized.get(key)
    ]
    return normalized


def _record_kind(path: Path | None) -> str:
    if path is None:
        return "unknown"
    name = path.name.lower()
    if name == "queue.json":
        return "queue"
    if name == "live_status.json":
        return "live_status"
    if path.parent.name.lower() == "reports" or path.suffix.lower() == ".json":
        return "report"
    return "unknown"


def _runtime_record_paths(runtime: Path) -> list[Path]:
    paths = [runtime / "queue.json", runtime / "live_status.json"]
    reports = runtime / "reports"
    if reports.exists():
        paths.extend(sorted(reports.glob("*.json")))
    return [path for path in paths if path.exists()]


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _extract_record(payload: Any) -> dict[str, Any]:
    if isinstance(payload, dict):
        for key in ["job", "record", "job_record", "result", "details"]:
            nested = payload.get(key)
            if isinstance(nested, dict):
                return nested
        return payload
    return {}


def _iter_records(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        for key in ["jobs", "queue", "records", "history", "items"]:
            value = payload.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
        return [_extract_record(payload)]
    return []


def _first(record: dict[str, Any], keys: list[str]) -> Any:
    for key in keys:
        value = record.get(key)
        if value not in (None, ""):
            return value
    return None


def _job_name_from_paths(record: dict[str, Any]) -> str | None:
    for keys in PATH_FIELDS.values():
        value = _first(record, keys)
        if value:
            suffix = Path(str(value)).suffix.lower()
            if suffix in {".inp", ".sta", ".msg", ".dat", ".log", ".odb"}:
                return Path(str(value)).stem
    return None


def _record_sort_key(record: dict[str, Any]) -> tuple[float, str]:
    raw = record.get("raw_record", {})
    for key in ["updated_at", "finished_at", "created_at", "timestamp", "time"]:
        value = raw.get(key)
        if isinstance(value, (int, float)):
            return (float(value), str(record.get("record_path") or ""))
    path = record.get("record_path")
    mtime = Path(path).stat().st_mtime if path and Path(path).exists() else 0.0
    return (mtime, str(path or ""))
