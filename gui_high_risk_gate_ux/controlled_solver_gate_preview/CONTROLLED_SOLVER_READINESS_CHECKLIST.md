# Controlled Solver Readiness Checklist

This checklist is preview-only. Passing items do not approve or execute a solver run.

| Item | Status | Description |
| --- | --- | --- |
| `task_dir_exists` | `PASS` | task_dir exists |
| `task_scaffold_exists` | `PASS` | task scaffold exists |
| `candidate_inp_exists` | `MISSING` | candidate INP exists under allowed task/artifact directory |
| `candidate_inp_not_source_sanity_base` | `MISSING` | candidate INP is not source sanity-base INP |
| `source_mutation_not_required` | `MISSING` | source CAE/INP mutation is not required |
| `static_validator_pass` | `MISSING` | StaticValidator PASS record exists |
| `diff_guard_pass` | `MISSING` | DiffGuard PASS record exists |
| `physics_guard_pass` | `MISSING` | PhysicsGuard PASS record exists |
| `mcpguard_pass_or_not_applicable` | `PASS` | MCPGuard PASS record exists or explicit MCPGuard not-applicable reason exists |
| `candidate_patch_preview_exists` | `MISSING` | candidate patch preview exists |
| `target_modification_summary_exists` | `MISSING` | target modification summary exists |
| `forbidden_action_confirmation_exists` | `PASS` | forbidden action confirmation exists |
| `solver_command_path_configured` | `PASS` | solver command path is configured in project status/config |
| `future_solver_output_dir_defined` | `PASS` | future controlled solver output directory is defined |
| `future_human_approval_required` | `PASS` | explicit human approval token would be required in a future stage |
| `no_queue_mutation_requested` | `PASS` | no queue mutation is requested |
| `no_odb_metrics_acceptance_requested` | `PASS` | no ODB metrics acceptance is requested |
| `no_final_evidence_update_requested` | `MISSING` | no final evidence update is requested |
| `no_final_verdict_freeze_requested` | `MISSING` | no final verdict freeze is requested |
| `no_automatic_execution_requested` | `MISSING` | no automatic execution requested |
