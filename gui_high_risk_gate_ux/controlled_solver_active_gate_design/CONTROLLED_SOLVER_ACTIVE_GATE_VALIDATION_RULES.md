# Controlled Solver Active Gate Validation Rules

- doc_type must be gate_decision.
- gate_type must be CONTROLLED_SOLVER_RUN.
- decision and approval_status must be APPROVED_BY_HUMAN.
- human approval token must be valid, consumed, one-time use, and non-reusable.
- solver_approved may be true only inside the schema/design object.
- solver_execution_allowed must be false.
- solver_request_created, solver_run, queue_runner_launched, and odb_opened must be false.
- ODB metrics approval, final evidence approval, final verdict freeze, and task final ledger updates must be false.
- downstream execution auto-start must be false.
