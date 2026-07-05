from __future__ import annotations


RECOMMENDATION_ONLY_NOTICE = "Recommendation only; no automatic execution"
FINAL_EVIDENCE_LOCKED_COPY = "Final evidence remains locked"
NON_FINAL_WORKFLOW_COPY = "Non-final / non-solver workflow"
CODEX_EXTERNAL_COPY = "GUI does not call Codex CLI"
SOLVER_ODB_METRICS_DISABLED_COPY = "Solver / ODB / metrics remain disabled"
NO_GENERIC_EXECUTOR_COPY = "Use the named safe panel action manually; no generic recommendation executor exists."


FORBIDDEN_ACTION_GUIDANCE = (
    "Run Solver",
    "Open ODB",
    "Queue Job",
    "Run Codex from GUI",
    "Auto Schedule Agent",
    "Approve Final Evidence",
    "Freeze Final Verdict",
    "Approve Solver / ODB / Metrics",
)


def recommendation_safety_notes() -> list[str]:
    return [
        RECOMMENDATION_ONLY_NOTICE,
        FINAL_EVIDENCE_LOCKED_COPY,
        NON_FINAL_WORKFLOW_COPY,
        CODEX_EXTERNAL_COPY,
        SOLVER_ODB_METRICS_DISABLED_COPY,
        NO_GENERIC_EXECUTOR_COPY,
    ]
