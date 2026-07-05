# AbqPilot Project Status

Latest verdict: `PASS_ABQPILOT_V2_STAGE5_2C_CONTROLLED_SOLVER_INACTIVE_HUMAN_GATE_DRAFT_READY`
Generated at: `2026-07-05T17:59:31`

## Capabilities

- guarded CAE/INP preparation
- heat patch audit
- StaticValidator / DiffGuard / PhysicsGuard
- task workspace and pipeline runner
- resume / skip / force-step
- abqjobpilot preflight
- dry-run enqueue
- human approval token
- controlled real queue-only enqueue
- queue status polling
- completed-job intake gate
- gated ODB metrics continuation
- metrics comparison
- deterministic evaluation
- deterministic repair-plan generation
- module registry
- event stream
- runtime view model
- tkinter GUI beta
- artifact browser / run report export
- alpha freeze package
- optional schema-bound LLM provider contract
- deterministic mock reasoner
- real LLM task-summary reasoning panel
- strict LLM output safety validation
- LLM-guided candidate patch proposal review
- strict patch proposal safety validation
- guarded PatchBuilder application preview
- guarded patch-to-queue workflow
- candidate-specific patch queue approval token
- patch queue production queue-only enqueue smoke
- patched job status poll and completed output intake gate
- patched job gated metrics continuation gate
- patched job report
- real sanity-base-derived patch candidate recovery
- fixture workflow evidence reclassified as non-production evidence
- equivalent real ODB intake, gated metrics extraction, and mixed metrics report
- controlled single-job Abaqus solver automation framework
- solver-specific approval token
- controlled solver monitor, output intake, and report gates
- Abaqus job/ODB failure diagnosis taxonomy reference
- deterministic Abaqus job/ODB failure diagnosis module
- deterministic solver-failure repair proposal
- abqjobpilot-backed job/ODB diagnosis integration
- abqjobpilot runtime/report record reader
- guarded DFLUX deactivation patch preview
- DFLUX lifecycle guarded controlled solver validation
- Model Condition Preservation Guard
- generalized source-intent to INP condition preservation checks
- ACOM handoff package infrastructure
- ACOM structured result intake placeholder validation
- dual execution-mode documentation: ACOM and NARM
- pipeline-style multi-agent protocol
- RUN/HANDOFF/GATE frontmatter validation
- flat pipeline task scaffold generation
- pipeline protocol CLI and GUI-safe actions
- ACOM template pack on pipeline protocol
- pipeline-integrated ACOM RUN/HANDOFF generation
- ACOM template registry and validation
- ACOM result pipeline revalidation gate
- pipeline-integrated ACOM result RUN/HANDOFF/GATE generation
- ACOM result routing to downstream AbqPilot revalidation agents
- ACOM downstream revalidation handoff scaffold
- downstream agent-specific revalidation profiles
- revalidation package RUN/HANDOFF/GATE scaffold generation
- deterministic non-solver revalidation executor
- non-solver revalidation RUN/HANDOFF/GATE result records
- PipelineSupervisor non-solver review gate
- non-final non-solver evidence ledger
- EvidenceReportAgent non-solver evidence summary report
- non-final non-solver summary RUN/HANDOFF/GATE records
- PipelineSupervisor non-solver summary acknowledgement
- non-final non-solver summary acknowledgement ledger
- GUI workflow state model for ACOM/non-solver pipeline state
- GUI safe action catalog with disabled high-risk controls
- GUI information architecture for RUN/HANDOFF/GATE visibility
- GUI non-final/non-solver boundary copy and final-evidence lock display
- GUI visual layout/readability cards, timeline, badges, and action panels
- GUI read-only trace viewer and timeline interaction
- GUI evidence file resolver and read-only document previews
- GUI read-only report viewer and artifact preview polish
- GUI Markdown/JSON preview safety claim detection
- GUI guided next-step recommendation for non-solver ACOM workflow
- GUI beta end-to-end safe workflow smoke and readiness report
- GUI high-risk gate UX specification and preview-only checklist catalog
- GUI controlled solver human gate preview and inactive approval token schema
- GUI controlled solver inactive human gate draft and future-shape specification

## Safety Boundary Matrix

| Boundary | Status |
| --- | --- |
| Abaqus solver submit | not automatic |
| QueueRunner launch | not automatic |
| abqjobpilot GUI | not used |
| OpenAI API | not integrated |
| LLM repair | not integrated |
| ODB open | gated extractor only |
| Real enqueue | approval-token gated and queue-only |
| INP mutation from repair plan | disabled |
| LLM provider | optional and confirmation-gated |
| Real LLM task summary | sanitized, compact, confirmation-gated, read-only |
| LLM patch proposal | advisory only, no INP mutation, guard-validated |
| PatchBuilder preview | candidate INP copy only, validator-gated, no solver/enqueue |
| Patch-to-queue workflow | validated preview only, candidate approval-token gated, no solver/QueueRunner/ODB open |
| Patch queue production smoke | queue-only proof confirmed; only runtime/queue.json changed |
| Patched job intake | read-only status/output evidence gate; no solver/QueueRunner/ODB direct open |
| Patched job metrics | requires accepted existing ODB and uses the existing gated metrics extractor only |
| Real patch candidates | must derive from sanity-base CAE/exported INP; toy fixtures are workflow-only |
| Equivalent ODB intake | requires Stage 3.9B traceability/equivalence evidence and uses existing ODBs only |
| Controlled solver automation | single validated sanity-base-derived candidate only; solver-specific approval-token gated; fixed Abaqus command shape; no batch loop |
| Job/ODB diagnosis | read-only log and metadata parser; ODB existence alone is not accepted |
| Solver-failure repair proposal | diagnosis-driven and proposal-only; no INP mutation, no solver run, no ODB open |
| abqjobpilot execution records | abqjobpilot remains execution-record/path authority; AbqPilot consumes records read-only for diagnosis and repair context |
| DFLUX deactivation preview | copied candidate INP only; inserts explicit cooling-step DFLUX reset, validator-gated, no solver/enqueue/ODB open |
| DFLUX guarded solver validation | requires Stage 4.3 DFLUX lifecycle guard PASS plus solver-specific approval token before a fixed single-job Abaqus run |
| Model Condition Preservation Guard | checks original CAE/JNL model-condition intent against exported, patched, and solver-run INPs; no solver/ODB/runtime mutation |
| ACOM handoff | bounded Codex operator packages only; AbqPilot does not call Codex CLI and Codex summaries are not final evidence |
| ACOM result intake | Codex structured results are accepted only pending downstream AbqPilot revalidation; unsafe safety flags, task mismatch, and handoff mismatch are rejected |
| ACOM downstream revalidation | accepted ACOM results can create downstream revalidation scaffolds; Stage 5.0F executes only supported non-solver deterministic checks and still does not approve evidence |
| ACOM non-solver revalidation | DocsStatusAgent, SoftwareQAAgent, AuditAgent, EvidenceReportAgent, and PipelineSupervisor only; Guard/CandidateBuilder/Diagnosis/Execution/Metrics agents are blocked |
| PipelineSupervisor non-solver review | can accept Stage 5.0F results into NON_SOLVER_EVIDENCE_LEDGER only; no final evidence freeze, solver approval, ODB approval, or metrics approval |
| EvidenceReportAgent non-solver summary | summarizes NON_SOLVER_EVIDENCE_LEDGER only; does not update TASK_FINAL_EVIDENCE_LEDGER.md or approve solver/ODB/metrics/final evidence |
| PipelineSupervisor non-solver summary acknowledgement | acknowledges EvidenceReportAgent non-solver summaries into NON_SOLVER_SUMMARY_ACK_LEDGER only; does not update TASK_FINAL_EVIDENCE_LEDGER.md |
| GUI safe workflow UX | Stage 5.1A displays ACOM/non-solver workflow state and disables solver, ODB, queue, Codex execution, auto scheduling, final evidence, and final verdict controls |
| GUI visual polish | Stage 5.1B improves layout and readability only; disabled high-risk actions remain callback-free and no execution capability is added |
| GUI trace viewer | Stage 5.1C resolves RUN/HANDOFF/GATE records and related artifacts read-only; timeline selection does not execute actions |
| GUI artifact preview | Stage 5.1D previews Markdown and JSON artifacts read-only; no external editor launch, artifact mutation, execution, final evidence approval, or final verdict freeze |
| GUI next-step recommendation | Stage 5.1E provides advisory recommendations only; no generic executor, no auto scheduling, no Codex CLI call, no solver/ODB/queue/final-evidence action |
| GUI beta readiness smoke | Stage 5.1F validates GUI beta readiness for non-solver ACOM governance only; not final evidence readiness and no execution authority |
| GUI high-risk gate UX | Stage 5.2A specifies high-risk gate UX only; preview-only, not approved, not executable, and no real gate creation |
| Controlled solver gate preview | Stage 5.2B designs controlled solver human gate preview and inactive token schema only; no solver approval, no solver request, and no execution |
| Controlled solver inactive gate draft | Stage 5.2C creates an inactive controlled solver human gate draft only; no active task gate, no solver request, and no execution |
| ACOM templates | pipeline RUN/HANDOFF plus bounded codex_handoff packages only; Codex executes externally and manually |
| Pipeline agents | bounded station protocol only; no automatic scheduling, no Codex bridge, no solver, no QueueRunner, no ODB open |
| NARM | optional native runtime mode and must preserve the same evidence and safety contracts |
| Arbitrary solver commands | not accepted |
| LLM solver authority | not integrated |
| API key display | masked only |

## Main CLI Commands

- `python -m abqpilot.cli status`
- `python -m abqpilot.cli run-sanity-demo --config configs\sanity_demo_task.json --mode prepare-only --task-id <task_id>`
- `python -m abqpilot.cli approve-jobpilot-enqueue --task-dir <task_dir> --approved-by human --approval-phrase I_APPROVE_ABQJOBPILOT_REAL_ENQUEUE_FOR_THIS_TASK`
- `python -m abqpilot.cli continue-from-job-output --task-dir <task_dir>`
- `python -m abqpilot.cli generate-repair-plan --task-dir <task_dir>`
- `python -m abqpilot.cli export-run-report --task-dir <task_dir>`
- `python -m abqpilot.cli llm-reason --provider mock --task-dir <task_dir>`
- `python -m abqpilot.cli llm-reason --task-dir <task_dir> --dry-run-input-summary`
- `python -m abqpilot.cli llm-reason --provider chatanywhere --task-dir <task_dir> --confirm-send-task-summary`
- `python -m abqpilot.cli propose-patch --task-dir <task_dir> --provider mock`
- `python -m abqpilot.cli propose-patch --task-dir <task_dir> --provider chatanywhere --confirm-send-patch-context`
- `python -m abqpilot.cli preview-patch --task-dir <task_dir> --provider-source llm`
- `python -m abqpilot.cli preview-dflux-deactivation-patch --source-inp <inp_path> --output-dir <out_dir>`
- `python -m abqpilot.cli prepare-dflux-guarded-solver-run --preview-inp <preview_inp> --validation-json <dflux_lifecycle_validation.json>`
- `python -m abqpilot.cli approve-dflux-guarded-solver-run --solver-run-dir <solver_run_dir> --approval-phrase I_APPROVE_ABQPILOT_DFLUX_DEACTIVATED_CONTROLLED_SOLVER_RUN`
- `python -m abqpilot.cli run-dflux-guarded-solver-approved --solver-run-dir <solver_run_dir>`
- `python -m abqpilot.cli monitor-dflux-guarded-solver-run --solver-run-dir <solver_run_dir>`
- `python -m abqpilot.cli intake-dflux-guarded-solver-output --solver-run-dir <solver_run_dir>`
- `python -m abqpilot.cli report-dflux-guarded-solver-run --solver-run-dir <solver_run_dir>`
- `python -m abqpilot.cli run-model-condition-guard --source-jnl <jnl> --source-inp <source_inp> --candidate-inp <candidate_inp> --solver-inp <solver_inp> --target-change body_heat_flux_magnitude:load_body_hflux_00:step_scan_00:1e+10:2e+10`
- `python -m abqpilot.cli generate-codex-handoff --task-id <task_id> --task-type model_condition_guard_review`
- `python -m abqpilot.cli list-acom-templates`
- `python -m abqpilot.cli describe-acom-template --template-id mcpguard_review`
- `python -m abqpilot.cli generate-codex-handoff --task-id <task_id> --template-id mcpguard_review`
- `python -m abqpilot.cli validate-acom-template-pack`
- `python -m abqpilot.cli validate-codex-handoff --handoff-dir <handoff_dir>`
- `python -m abqpilot.cli intake-codex-result --handoff-dir <handoff_dir> --result-json <structured_result.json>`
- `python -m abqpilot.cli report-acom-result-intake --task-dir <task_dir>`
- `python -m abqpilot.cli scaffold-acom-revalidation --task-dir <task_dir>`
- `python -m abqpilot.cli report-acom-revalidation --task-dir <task_dir>`
- `python -m abqpilot.cli execute-non-solver-revalidation --task-dir <task_dir>`
- `python -m abqpilot.cli report-non-solver-revalidation --task-dir <task_dir>`
- `python -m abqpilot.cli supervisor-review-non-solver-revalidation --task-dir <task_dir>`
- `python -m abqpilot.cli report-supervisor-non-solver-review --task-dir <task_dir>`
- `python -m abqpilot.cli generate-non-solver-evidence-summary --task-dir <task_dir>`
- `python -m abqpilot.cli report-non-solver-evidence-summary --task-dir <task_dir>`
- `python -m abqpilot.cli supervisor-ack-non-solver-summary --task-dir <task_dir>`
- `python -m abqpilot.cli report-supervisor-non-solver-summary-ack --task-dir <task_dir>`
- `python -m abqpilot.cli report-codex-handoff --handoff-dir <handoff_dir>`
- `python -m abqpilot.cli queue-patch-preview --task-dir <task_dir> --patch-preview-dir <preview_dir> --mode preflight-only`
- `python -m abqpilot.cli queue-patch-preview --task-dir <task_dir> --patch-preview-dir <preview_dir> --mode dry-run-enqueue`
- `python -m abqpilot.cli approve-patch-queue --workflow-dir <workflow_dir> --approved-by human --approval-phrase I_APPROVE_ABQPILOT_PATCH_CANDIDATE_QUEUE_ONLY_ENQUEUE`
- `python -m abqpilot.cli queue-patch-preview --workflow-dir <workflow_dir> --mode real-queue-only --approval-token <token_path>`
- `python -m abqpilot.cli poll-patch-queue --workflow-dir <workflow_dir>`
- `python -m abqpilot.cli intake-patched-job-output --workflow-dir <workflow_dir>`
- `python -m abqpilot.cli extract-patched-job-metrics --workflow-dir <workflow_dir>`
- `python -m abqpilot.cli report-patched-job --workflow-dir <workflow_dir>`
- `python -m abqpilot.cli recover-sanity-base-patch-candidate`
- `python -m abqpilot.cli run-stage3-9c-equivalent-odb`
- `python -m abqpilot.cli prepare-solver-run --candidate-inp <candidate_inp> --source-inp <source_inp> --evidence-dir <stage3_9b_dir> --cpus 14`
- `python -m abqpilot.cli approve-solver-run --solver-run-dir <solver_run_dir> --approved-by human --approval-phrase I_APPROVE_ABQPILOT_CONTROLLED_ABAQUS_SOLVER_RUN`
- `python -m abqpilot.cli run-solver-approved --solver-run-dir <solver_run_dir> --approval-token <token_path>`
- `python -m abqpilot.cli monitor-solver-run --solver-run-dir <solver_run_dir>`
- `python -m abqpilot.cli diagnose-job-output --job-dir <job_dir> --job-name <job_name>`
- `python -m abqpilot.cli diagnose-job-output --abqjobpilot-report <report_json>`
- `python -m abqpilot.cli diagnose-job-output --abqjobpilot-job-id <job_id> --abqjobpilot-runtime-dir D:\Projects\abqjobpilot_dev\runtime`
- `python -m abqpilot.cli list-abqjobpilot-records --abqjobpilot-runtime-dir D:\Projects\abqjobpilot_dev\runtime --max-results 20`
- `python -m abqpilot.cli intake-solver-run-output --solver-run-dir <solver_run_dir>`
- `python -m abqpilot.cli report-solver-run --solver-run-dir <solver_run_dir>`
- `python -c "from abqpilot.patching.patch_queue_smoke import write_stage3_8a_smoke_summary; write_stage3_8a_smoke_summary(<workflow_dir>)"`
- `python -m abqpilot.cli probe-llm --provider chatanywhere --model deepseek-chat --confirm-send-test-request`
- `python -m abqpilot.cli list-pipeline-agents`
- `python -m abqpilot.cli scaffold-pipeline-task --task-id <task_id>`
- `python -m abqpilot.cli validate-pipeline-protocol --task-dir <task_dir>`
- `python -m abqpilot.cli report-pipeline-protocol --task-dir <task_dir>`
- `python -m abqpilot.cli gui`

## Current Pipeline Order

- `01_export_cae`
- `02_audit_heat_x2`
- `03_abqjobpilot_preflight`
- `04_abqjobpilot_dry_run_enqueue`
- `05_jobpilot_enqueue_authorization`
- `06_abqjobpilot_real_enqueue`
- `07_abqjobpilot_status_poll`
- `08_solver_intake`
- `09_odb_metrics`
- `10_compare_metrics`

## Known Limitations

- The controlled solver automation framework exists, but the first real Stage 4.0 smoke failed safely because Abaqus terminated the analysis before completion.
- Queue worker launch remains outside AbqPilot GUI authority.
- ODB opening remains limited to the existing gated metrics extractor.
- Repair plans are deterministic reports and do not mutate INP files.
- LLM reasoning is advisory and cannot execute workflow actions.
- LLM patch proposals are advisory and cannot apply patches.
- Patch preview supports heat_flux_magnitude_adjustment only in Stage 3.7.
- Patch-to-queue does not run production real enqueue unless a candidate-specific token is supplied.
- Stage 3.9 can poll and intake completed patched-job outputs, but solver execution remains external/manual.
- Patched-job metrics remain blocked until an existing unlocked ODB is accepted by the intake gate.
- Stage 3.7/3.8 fixture patch candidates are workflow-only and not production solver-ready evidence.
- Stage 3.9B recovered a real sanity-base-derived candidate from the Stage 1.6A exported INP.
- Stage 3.9C accepted an existing manually completed equivalent 2x ODB and extracted metrics through the gated extractor.
- Stage 4.0 does not support batch loops, arbitrary solver commands, LLM-controlled execution, or QueueRunner launch.
- Stage 4.1 diagnosis implementation should use docs/diagnostics/ABQPILOT_ABAQUS_JOB_ODB_FAILURE_DIAGNOSIS_TAXONOMY.md as the design reference.
- Stage 4.1 blocks metrics extraction unless diagnosis_status is JOB_COMPLETED_ODB_ACCEPTABLE.
- Stage 4.2 creates repair proposals only and does not apply solver-control patches.
- Stage 4.1B consumes abqjobpilot records read-only; abqjobpilot remains the execution lifecycle and path authority.
- Attempt-block parsing is intentionally minimal and supports START/END marker styles used by abqjobpilot logs.
- Stage 4.3 creates a preview INP copy with explicit *Dflux, OP=NEW in the cooling step; it does not run solver or open ODB.
- Stage 4.4 permits a controlled solver attempt only after the Stage 4.3 DFLUX lifecycle guard passes and a DFLUX-specific approval token validates.
- Stage 4.5 generalizes the DFLUX lifecycle bug into MCPGuard; Stage 4.5 currently implements concrete body heat flux DFLUX/BF lifecycle preservation plus schema hooks for other condition categories.
- Stage 5.0A defines ACOM handoff infrastructure only; AbqPilot does not call Codex CLI and structured results remain pending deterministic AbqPilot revalidation.
- Stage 5.0B defines pipeline communication protocol only; it does not add automatic scheduling, Codex runtime bridge, solver execution, QueueRunner launch, enqueue, or ODB opening.
- Stage 5.0C defines ACOM templates on the pipeline protocol; it generates RUN/HANDOFF records and codex_handoff packages but does not call Codex CLI.
- Stage 5.0D intakes Codex structured results into pipeline RUN/HANDOFF/GATE records for downstream AbqPilot revalidation; accepted intake is not final evidence.
- Stage 5.0E creates downstream revalidation scaffolds only; it does not run downstream agents, schedule pipelines, or approve evidence.
- Stage 5.0F executes deterministic non-solver revalidation only for DocsStatusAgent, SoftwareQAAgent, AuditAgent, EvidenceReportAgent, and PipelineSupervisor; high-risk agents remain blocked.
- Stage 5.0G lets PipelineSupervisor accept completed non-solver revalidation into NON_SOLVER_EVIDENCE_LEDGER only; final evidence remains separate and unapproved.
- Stage 5.0H lets EvidenceReportAgent summarize NON_SOLVER_EVIDENCE_LEDGER into non-final reports only; TASK_FINAL_EVIDENCE_LEDGER.md remains untouched.
- Stage 5.0I lets PipelineSupervisor acknowledge EvidenceReportAgent non-solver summaries into NON_SOLVER_SUMMARY_ACK_LEDGER only; TASK_FINAL_EVIDENCE_LEDGER.md remains untouched.
- Stage 5.1A reorganizes GUI information architecture around safe workflow state. High-risk solver/ODB/queue/Codex/final-evidence actions are visible only as disabled controls with no execution backend.
- Stage 5.1B adds GUI visual layout/readability helpers: status cards, workflow timeline, badge labels, action panels, and disabled high-risk summaries. It adds no solver, ODB, Codex, queue, scheduling, or final-evidence capability.
- Stage 5.1C adds read-only GUI trace viewer and timeline interaction. It resolves RUN/HANDOFF/GATE records and related artifacts, flags unsafe final-approval claims, and adds no execution capability.
- Stage 5.1D adds read-only GUI report and artifact preview polish. It parses Markdown/JSON records, flags unsafe final-approval claims, and does not mutate artifacts or launch external editors.
- Stage 5.1E adds guided next-step recommendation. Recommendations point to existing safe GUI panels only and never auto-execute, call Codex CLI, run solver, open ODB, queue jobs, approve final evidence, or freeze verdict.
- Stage 5.1F adds an end-to-end GUI safe workflow smoke and non-final beta readiness report. It validates Stage 5.1A-E GUI components without adding solver, ODB, Codex, queue, scheduling, final evidence, or final verdict authority.
- Stage 5.2A adds a preview-only high-risk gate UX specification catalog. It does not execute high-risk actions, create real approving gates, update TASK_FINAL_EVIDENCE_LEDGER.md, approve final evidence, or freeze verdict.
- Stage 5.2B narrows the high-risk UX design to CONTROLLED_SOLVER_RUN. It creates preview-only readiness, approval-token schema, validator, and report artifacts, but does not approve solver, create solver requests, run Abaqus, open ODB, mutate queue/runtime files, update final evidence, or freeze verdict.
- Stage 5.2C creates an inactive CONTROLLED_SOLVER_RUN human gate draft, expected future active gate shape, and expected future solver execution handoff shape. These are specification artifacts only and do not create active task gates, solver requests, queue/runtime mutations, ODB/metrics approvals, final evidence, or verdict freeze.

## Recommended Next Stages

- Add later guarded executors for GuardAgent/CandidateBuilderAgent/DiagnosisAgent/MetricsAgent only with model/ODB-specific gates
- Integrate MCPGuard as a mandatory future solver eligibility gate beside StaticValidator, DiffGuard, and PhysicsGuard
- GUI persistence and usability hardening
- Add optional read-only GUI workflow reports after the Stage 5.1A presenter stabilizes
- Use pipeline protocol scaffolds for future task traces before any high-risk execution
- Implement real high-risk human approval gates only in a future explicit stage after the Stage 5.2A UX specification is reviewed
- Implement a real controlled solver approval gate only in a future explicit stage, then keep solver execution in a separate later stage
- Keep Stage 5.2C inactive draft artifacts separate from any future active GATE_XXX approval record
