# Controlled Solver Approval Token Rules

The token schema is preview-only in Stage 5.2B. A token that validates here is valid for future-stage design review only and is not active approval.

- token_type must be CONTROLLED_SOLVER_RUN_APPROVAL
- token_version must be supported
- task_id and task_dir must match
- candidate_artifact_hash must match the candidate artifact if it exists
- approval phrase must exactly match the required phrase
- all acknowledgement flags must be true
- token must not be expired if expires_at_optional is present
- one_time_use must be true
- preview_only_in_stage_5_2b must be true
- active_approval must be false in Stage 5.2B

If `active_approval=true`, validation must return `TOKEN_PREVIEW_BLOCKED_ACTIVE_APPROVAL_ATTEMPT`.
Future approval and future solver execution must remain separate stages.
