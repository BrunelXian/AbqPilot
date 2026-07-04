# NARM Mode

NARM means Native Agent Runtime Mode.

NARM is the optional advanced runtime direction where AbqPilot native Python code executes workflows directly without Codex CLI. NARM is not the default practical mode in Stage 5.0A.

NARM must satisfy the same safety and evidence contracts as ACOM. The runtime must not bypass StaticValidator, DiffGuard, PhysicsGuard, MCPGuard, Job/ODB diagnosis, schema validation, artifact hash checks, safety audits, or secret audits.

NARM does not weaken the hard rule that production simulation candidates must be sanity-base-derived and that non-target original model conditions must be preserved.
