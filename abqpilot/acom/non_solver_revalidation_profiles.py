from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from abqpilot.acom.result_schema import unsafe_safety_flags


PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class CheckResult:
    name: str
    status: str
    detail: str


def run_profile_checks(agent: str, *, task_dir: Path, scaffold: dict[str, Any], intake: dict[str, Any], structured_result: dict[str, Any] | None) -> list[CheckResult]:
    checks = [
        _check("ACOM intake accepted", intake.get("result_status") == "ACOM_RESULT_ACCEPTED_PENDING_REVALIDATION", str(intake.get("result_status"))),
        _check("Codex summary is not final evidence", not _truthy(structured_result, "codex_summary_is_final_evidence"), "claim boundary preserved"),
    ]
    checks.extend(_common_safety_checks(structured_result or {}))
    if agent == "DocsStatusAgent":
        checks.extend(_docs_status_checks(structured_result or {}))
    elif agent == "SoftwareQAAgent":
        checks.extend(_software_qa_checks(structured_result or {}))
    elif agent == "AuditAgent":
        checks.extend(_audit_checks(task_dir, structured_result or {}))
    elif agent == "EvidenceReportAgent":
        checks.extend(_evidence_report_checks(structured_result or {}))
    elif agent == "PipelineSupervisor":
        checks.extend(_pipeline_supervisor_checks(structured_result or {}))
    else:
        checks.append(CheckResult("supported Stage 5.0F agent", "fail", f"{agent} is not a supported non-solver revalidation agent"))
    return checks


def summarize_checks(checks: list[CheckResult]) -> dict[str, list[str]]:
    return {
        "pass_items": [f"{item.name}: {item.detail}" for item in checks if item.status == "pass"],
        "warning_items": [f"{item.name}: {item.detail}" for item in checks if item.status == "warning"],
        "fail_items": [f"{item.name}: {item.detail}" for item in checks if item.status == "fail"],
    }


def _docs_status_checks(result: dict[str, Any]) -> list[CheckResult]:
    status_md = PROJECT_ROOT / "PROJECT_STATUS_CURRENT.md"
    status_json = PROJECT_ROOT / "PROJECT_STATUS_CURRENT.json"
    abqpilot = PROJECT_ROOT / "ABQPILOT.md"
    agents = PROJECT_ROOT / "AGENTS.md"
    checks = [
        _exists("PROJECT_STATUS_CURRENT.md exists", status_md),
        _exists("PROJECT_STATUS_CURRENT.json exists", status_json),
        _exists("ABQPILOT.md exists", abqpilot),
        _exists("AGENTS.md exists", agents),
    ]
    payload: dict[str, Any] = {}
    try:
        payload = json.loads(status_json.read_text(encoding="utf-8"))
        checks.append(CheckResult("PROJECT_STATUS_CURRENT.json valid JSON", "pass", "parsed"))
    except Exception as exc:
        checks.append(CheckResult("PROJECT_STATUS_CURRENT.json valid JSON", "fail", str(exc)))
    latest = str(payload.get("latest_verdict") or payload.get("current_verdict") or payload.get("status") or "")
    status_text = status_md.read_text(encoding="utf-8") if status_md.exists() else ""
    abq_text = abqpilot.read_text(encoding="utf-8") if abqpilot.exists() else ""
    agents_text = agents.read_text(encoding="utf-8") if agents.exists() else ""
    if latest:
        checks.append(_check("PROJECT_STATUS_CURRENT.md mentions current verdict", latest in status_text, latest))
        checks.append(_check("ABQPILOT.md mentions current verdict or stage", latest in abq_text or "Stage 5.0" in abq_text, latest))
    else:
        checks.append(CheckResult("current verdict discoverable", "warning", "latest verdict field not found"))
    checks.append(_check("AGENTS.md mentions ACOM/pipeline safety rules", "ACOM" in agents_text and "pipeline" in agents_text.lower(), "ACOM pipeline rule present"))
    code_changes = [path for path in result.get("files_modified", []) + result.get("files_created", []) if str(path).endswith((".py", ".inp", ".cae", ".odb"))]
    checks.append(_check("no behavior-changing code/model modifications accepted by docs profile", not code_changes, f"declared code/model changes: {code_changes}"))
    return checks


def _software_qa_checks(result: dict[str, Any]) -> list[CheckResult]:
    tests_run = result.get("tests_run") or []
    artifacts = result.get("artifacts") or {}
    claims = result.get("validation_claims") or {}
    checks = [
        _present_or_warn("test result summary declared", tests_run or artifacts.get("tests_result") or artifacts.get("pytest_result"), "tests not run or not declared"),
        _present_or_warn("safety audit summary declared", artifacts.get("safety_audit") or claims.get("safety_audit_passed"), "safety audit not run or not declared"),
        _present_or_warn("secret audit summary declared", artifacts.get("secret_audit") or claims.get("secret_audit_passed"), "secret audit not run or not declared"),
        _check("test result summary is not final physical evidence", True, "claim boundary preserved"),
    ]
    return checks


def _audit_checks(task_dir: Path, result: dict[str, Any]) -> list[CheckResult]:
    artifacts = result.get("artifacts") or {}
    files_modified = result.get("files_modified") or []
    files_deleted = result.get("files_deleted") or []
    audit_artifact = artifacts.get("audit_report") or artifacts.get("report")
    checks = [
        _present_or_warn("audit output artifact declared", audit_artifact, "audit artifact missing or explicitly absent"),
        _check("read-only file modifications absent", not files_modified and not files_deleted, f"modified={files_modified}, deleted={files_deleted}"),
    ]
    if audit_artifact:
        path = _resolve_task_path(task_dir, str(audit_artifact))
        checks.append(_exists("declared audit artifact exists", path))
        if path.exists() and path.suffix.lower() == ".md":
            text = path.read_text(encoding="utf-8")
            required = ["files inspected", "final verdict"]
            checks.append(_check("audit report has required sections", all(item in text.lower() for item in required), ", ".join(required)))
    return checks


def _evidence_report_checks(result: dict[str, Any]) -> list[CheckResult]:
    artifacts = result.get("artifacts") or {}
    limitations = result.get("known_limitations") or []
    checks = [
        _present_or_warn("artifact list exists or absence declared", artifacts or "artifacts intentionally absent" in " ".join(limitations).lower(), "artifact list missing"),
        _check("known limitations section exists", bool(limitations), f"{len(limitations)} limitations"),
        _check("no final evidence frozen by Codex", not (result.get("safety_flags") or {}).get("final_evidence_frozen"), "final_evidence_frozen=false"),
        _check("no human approval fabricated", not (result.get("safety_flags") or {}).get("human_approval_fabricated"), "human_approval_fabricated=false"),
    ]
    return checks


def _pipeline_supervisor_checks(result: dict[str, Any]) -> list[CheckResult]:
    artifacts = result.get("artifacts") or {}
    final_status = str(result.get("final_status") or "")
    text = json.dumps(artifacts, ensure_ascii=False).lower() + " " + final_status.lower()
    checks = [
        _check("planning output confirms no execution performed", not _any_action_flag(result), "no execution safety flags set"),
        _present_or_warn("eligibility gates listed", "gate" in text or "eligibility" in text, "gates not clearly declared"),
        _present_or_warn("human approval requirement listed for high-risk transitions", "approval" in text or "human" in text, "human approval requirement not clearly declared"),
        _check("decision is not APPROVED automatically", "APPROVED" not in final_status.upper(), final_status or "no final status"),
    ]
    return checks


def _common_safety_checks(result: dict[str, Any]) -> list[CheckResult]:
    unsafe = unsafe_safety_flags(result) if result else []
    checks = [_check("unsafe safety flags are false", not unsafe, ", ".join(unsafe) if unsafe else "all false")]
    flags = result.get("safety_flags") or {}
    for flag in ["shell_true_used", "generic_subprocess_added", "codex_cli_auto_called", "solver_started", "queue_runner_launched", "odb_opened"]:
        checks.append(_check(f"no declared {flag}", flags.get(flag) is not True, f"{flag}={flags.get(flag)}"))
    return checks


def _any_action_flag(result: dict[str, Any]) -> bool:
    flags = result.get("safety_flags") or {}
    return any(flags.get(key) is True for key in ["solver_started", "queue_runner_launched", "odb_opened", "codex_cli_auto_called"])


def _truthy(result: dict[str, Any] | None, key: str) -> bool:
    if not result:
        return False
    return result.get(key) is True


def _check(name: str, condition: bool, detail: str) -> CheckResult:
    return CheckResult(name, "pass" if condition else "fail", detail)


def _exists(name: str, path: Path) -> CheckResult:
    return _check(name, path.exists(), str(path))


def _present_or_warn(name: str, value: Any, warning: str) -> CheckResult:
    return CheckResult(name, "pass" if bool(value) else "warning", str(value) if value else warning)


def _resolve_task_path(task_dir: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else task_dir / path
