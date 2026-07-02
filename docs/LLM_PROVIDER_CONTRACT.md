# Optional LLM Provider Contract

Stage 3.5A adds an optional runtime LLM provider contract for AbqPilot-v2. It is not a Codex bridge and does not make Codex the runtime LLM.

## Priority

The default and safest reasoner is the local mock provider:

```powershell
D:\XianLab\envs\conda\LangChainEnv\Scripts\python.exe -m abqpilot.cli llm-reason --provider mock --task-dir D:\Projects\AbqPilot-v2\runs\tasks\stage2_6a_production_queue_only_smoke
```

The mock reasoner is deterministic, offline, and schema-validated.

## `.env`

AbqPilot may read `D:\Projects\AbqPilot-v2\.env` for these keys:

```env
ABQPILOT_LLM_ENABLED=false
ABQPILOT_LLM_PROVIDER=chatanywhere
ABQPILOT_LLM_MODEL=deepseek-chat
ABQPILOT_LLM_API_KEY=sk-REPLACE_WITH_YOUR_KEY
ABQPILOT_LLM_CHAT_URL=https://api.chatanywhere.tech/v1/chat/completions
ABQPILOT_LLM_EMBED_URL=https://api.chatanywhere.tech/v1/embeddings
ABQPILOT_LLM_TIMEOUT_SECONDS=30
ABQPILOT_LLM_MAX_INPUT_CHARS=12000
ABQPILOT_LLM_REQUIRE_JSON=true
```

The API key is never printed. Displayed configuration masks it as `sk-****MASKED****` or `<not-configured>`.

## Real Provider Probe

A real provider probe requires explicit confirmation:

```powershell
D:\XianLab\envs\conda\LangChainEnv\Scripts\python.exe -m abqpilot.cli probe-llm --provider chatanywhere --model deepseek-chat --confirm-send-test-request
```

The probe sends only:

```json
{"test": "Return JSON {\"ok\": true}."}
```

It does not send task summaries, INP, ODB, CAE files, logs, or secrets.

## Task Reasoning

Sending a task summary to a non-mock provider requires:

```powershell
D:\XianLab\envs\conda\LangChainEnv\Scripts\python.exe -m abqpilot.cli llm-reason --task-dir <task_dir> --provider chatanywhere --confirm-send-task-summary
```

Only compact sanitized JSON from the LLM input builder is sent. It excludes full INP, ODB, CAE files, raw logs, binary artifacts, and API keys.

## Patch Proposal Review

Stage 3.6 adds advisory LLM-guided candidate patch proposals:

```powershell
D:\XianLab\envs\conda\LangChainEnv\Scripts\python.exe -m abqpilot.cli propose-patch --task-dir <task_dir> --provider mock
```

Real provider patch proposal review requires explicit confirmation:

```powershell
D:\XianLab\envs\conda\LangChainEnv\Scripts\python.exe -m abqpilot.cli propose-patch --task-dir <task_dir> --provider chatanywhere --confirm-send-patch-context
```

Only sanitized patch context is sent. It may include deterministic evaluation summaries, deterministic repair-plan summaries, prior LLM reasoning verdicts, and safety boundaries. It never sends full INP, ODB, CAE files, raw logs, binary artifacts, `.env`, or secrets.

Allowed proposal types are:

- `heat_flux_magnitude_adjustment`
- `step_time_adjustment`
- `output_request_adjustment`
- `no_action`
- `human_review_only`

Forbidden proposal types include material, geometry, mesh, boundary-condition, contact, solver-submit, queue-runner, direct-ODB-open, and raw-INP-edit changes. Candidate proposals are advisory only; Stage 3.6 does not apply patches. Any future application must go through deterministic patch builders plus StaticValidator, DiffGuard, PhysicsGuard, and human review.

## Guarded PatchBuilder Preview

Stage 3.7 can convert a validated candidate proposal into a deterministic preview:

```powershell
D:\XianLab\envs\conda\LangChainEnv\Scripts\python.exe -m abqpilot.cli preview-patch --task-dir <task_dir> --provider-source llm
```

The LLM still does not edit INP files. The proposal is only an input specification. A deterministic PatchBuilder creates a candidate INP copy in `patch_previews/preview_*` only for supported proposal types. Stage 3.7 supports `heat_flux_magnitude_adjustment`; other allowed types remain blocked unless a deterministic builder is added later. StaticValidator, DiffGuard, and PhysicsGuard must pass before the preview is marked ready.

## Guarded Patch-to-Queue Workflow

Stage 3.8 can take a validated Stage 3.7 candidate INP preview into the existing guarded abqjobpilot queue workflow:

```text
validated candidate INP
-> abqjobpilot preflight
-> dry-run enqueue
-> candidate-specific approval token
-> controlled real queue-only enqueue
-> status polling
```

The LLM has no execution authority in this chain. It cannot approve, enqueue, submit solver jobs, launch external queue workers, open ODB files, or bypass StaticValidator, DiffGuard, PhysicsGuard, or approval-token checks. Candidate approval tokens bind the preview directory, candidate INP hash, job request hash, preflight result hash, dry-run result hash, patch type, and changed-line counts.

## Safety

- No OpenAI SDK dependency is added.
- No LangGraph dependency is added.
- No Codex runtime bridge is added.
- No automatic repair loop is added.
- LLM output is advisory and schema-validated.
- LLM patch proposals are advisory and never mutate INP files.
- LLM patch proposals cannot queue jobs; Stage 3.8 queue actions require deterministic preview evidence and candidate-specific approval.
- Repair plans remain deterministic unless a future gated stage explicitly changes that policy.
