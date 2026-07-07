# Controlled Solver Active Gate Writer Fixture Policy

- TEST_FIXTURE_ONLY mode is supported.
- REAL_TASK_WRITE_DISABLED mode remains active for real tasks.
- Real `runs/tasks/*/gates` writes are blocked.
- Solver request creation is blocked.
- Execution handoff creation is blocked.
- Final evidence authority is blocked.
- No Abaqus solver command is executed.
- `TASK_FINAL_EVIDENCE_LEDGER.md` remains untouched.
