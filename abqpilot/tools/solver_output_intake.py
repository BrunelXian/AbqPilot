from __future__ import annotations

from collections import defaultdict
from pathlib import Path


SUPPORTED_EXTENSIONS = {".inp", ".odb", ".sta", ".msg", ".dat", ".log", ".com", ".prt", ".sim", ".lck"}
PRIMARY_FIELDS = {
    ".inp": "inp_path",
    ".odb": "odb_path",
    ".sta": "sta_path",
    ".msg": "msg_path",
    ".dat": "dat_path",
    ".log": "log_path",
    ".lck": "lck_path",
}


def inventory_solver_outputs(search_roots: list[str | Path]) -> dict:
    groups = _group_files(search_roots)
    candidates = [_case_from_group(stem, files) for stem, files in groups.items()]
    role_candidates = {
        "base": [case for case in candidates if case["expected_role"] == "base"],
        "power_x2": [case for case in candidates if case["expected_role"] == "power_x2"],
    }
    selected = []
    for role in ("base", "power_x2"):
        best = _best_case(role_candidates[role])
        if best:
            selected.append(best)

    verdict = "SOLVER_OUTPUT_PAIR_FOUND" if len(selected) == 2 else "FAIL_SOLVER_OUTPUT_PAIR_NOT_FOUND"
    if verdict == "SOLVER_OUTPUT_PAIR_FOUND" and not all(case["odb_exists"] for case in selected):
        verdict = "FAIL_ODB_PAIR_NOT_FOUND"

    return {
        "tool": "SolverOutputIntake",
        "search_roots": [str(Path(root)) for root in search_roots],
        "verdict": verdict,
        "cases": selected,
        "all_candidates": candidates,
    }


def _group_files(search_roots: list[str | Path]) -> dict[str, list[Path]]:
    groups: dict[str, list[Path]] = defaultdict(list)
    for root in search_roots:
        root_path = Path(root)
        if not root_path.exists():
            continue
        for path in root_path.rglob("*"):
            if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
                groups[path.stem].append(path)
    return groups


def _case_from_group(stem: str, files: list[Path]) -> dict:
    role = _infer_role(stem)
    case_id = "base_power_1x" if role == "base" else "power_x2" if role == "power_x2" else stem
    case = {
        "case_id": case_id,
        "source_stem": stem,
        "expected_role": role,
        "inp_path": None,
        "odb_path": None,
        "sta_path": None,
        "msg_path": None,
        "dat_path": None,
        "log_path": None,
        "lck_path": None,
        "other_files": [],
        "files_found": bool(files),
        "odb_exists": False,
        "lock_exists": False,
    }
    for path in sorted(files):
        field = PRIMARY_FIELDS.get(path.suffix.lower())
        if field and case[field] is None:
            case[field] = str(path)
        else:
            case["other_files"].append(str(path))
    case["odb_exists"] = bool(case["odb_path"] and Path(case["odb_path"]).exists())
    case["lock_exists"] = bool(case["lck_path"] and Path(case["lck_path"]).exists())
    if case["lock_exists"]:
        case["warning"] = "WARNING_LOCK_FILE_PRESENT"
    return case


def _infer_role(stem: str) -> str | None:
    normalized = stem.lower()
    if any(token in normalized for token in ("power_2x", "power_x2", "_2x", "x2", "generated_power_x2")):
        return "power_x2"
    if any(token in normalized for token in ("power_1x", "_1x", "base_power", "base_heatflux", "base")):
        return "base"
    return None


def _best_case(cases: list[dict]) -> dict | None:
    if not cases:
        return None
    return max(cases, key=_score_case)


def _score_case(case: dict) -> tuple[int, int, str]:
    score = 0
    for field in ("odb_path", "sta_path", "msg_path", "dat_path", "log_path", "inp_path"):
        if case.get(field):
            score += 1
    if case.get("odb_exists"):
        score += 10
    return (score, len(case.get("other_files", [])), case["source_stem"])

