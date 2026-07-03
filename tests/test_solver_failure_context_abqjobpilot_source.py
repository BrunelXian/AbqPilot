import json

from abqpilot.repair.solver_failure_context import build_solver_failure_context


def test_solver_failure_context_records_abqjobpilot_source_metadata(tmp_path):
    diagnosis = {
        "diagnosis_input_mode": "abqjobpilot_record",
        "diagnosis_status": "JOB_SOLVER_CONVERGENCE_FAILED",
        "failure_category": "solver_convergence_failure",
        "odb_acceptable_for_metrics": False,
        "evidence": {"too_many_attempts": True},
        "abqjobpilot_record": {
            "job_id": "qctx",
            "raw_status": "FAILED_FATAL",
            "fatal_reason": "Abaqus Error",
            "return_code": 1,
            "record_path": "runtime/reports/qctx.json",
            "record_kind": "report",
        },
    }
    (tmp_path / "job_odb_diagnosis_result.json").write_text(json.dumps(diagnosis), encoding="utf-8")

    context = build_solver_failure_context(tmp_path)

    assert context["diagnosis_input_mode"] == "abqjobpilot_record"
    assert context["abqjobpilot_execution_record"]["available"] is True
    assert context["abqjobpilot_execution_record"]["job_id"] == "qctx"
    assert context["abqjobpilot_execution_record"]["raw_status"] == "FAILED_FATAL"
    assert context["abqjobpilot_execution_record"]["record_kind"] == "report"
