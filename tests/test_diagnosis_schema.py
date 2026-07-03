from abqpilot.diagnostics.diagnosis_schema import (
    JOB_COMPLETED_ODB_ACCEPTABLE,
    JOB_SOLVER_CONVERGENCE_FAILED,
    COMPLETED,
    SOLVER_CONVERGENCE_FAILURE,
    category_for_status,
)


def test_diagnosis_schema_categories():
    assert category_for_status(JOB_COMPLETED_ODB_ACCEPTABLE) == COMPLETED
    assert category_for_status(JOB_SOLVER_CONVERGENCE_FAILED) == SOLVER_CONVERGENCE_FAILURE
    assert category_for_status("NOPE") == "unknown"

