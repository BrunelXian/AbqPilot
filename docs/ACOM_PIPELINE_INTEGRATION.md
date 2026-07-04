# ACOM Pipeline Integration

ACOM integrates with the flat RUN/HANDOFF/GATE protocol.

Codex remains an external operator. Codex summaries are not final evidence.

Stage 5.0D writes ACOM result intake records. Stage 5.0E adds downstream revalidation scaffolds and records:

- `trace/RUN_XXX_<DOWNSTREAM_AGENT>_REVALIDATION.md`
- `gates/GATE_XXX_<DOWNSTREAM_AGENT>_REVALIDATION.md`
- `handoffs/HANDOFF_XXX_<DOWNSTREAM_AGENT>_REVALIDATION_TO_<NEXT_AGENT>.md`

No automatic scheduling is added. No downstream agent is run automatically.

Stage 5.0F adds an explicitly invoked deterministic non-solver revalidation executor. It does not schedule agents. It only checks supported low-risk downstream scaffolds and routes the result to PipelineSupervisor review.
