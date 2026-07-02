# Architecture V2

AbqPilot-v2 is a deterministic orchestrator with structured schemas, controlled builders, static validation, diff guard, physics guard, dry-run job adapter, fixture ODB metrics extraction, deterministic evaluation/repair planning, trace writing, and rollback placeholders.

The orchestrator is not an LLM agent. LLM nodes are stubs behind explicit interfaces and are not invoked in MVP-01.

Guard order:

1. Inventory
2. Objective load
3. Build request
4. Heat flux patch build
5. Static validation
6. Diff guard
7. Physics guard
8. Dry-run job command preparation
9. Fixture metrics extraction
10. Evaluation and repair planning
11. Trace and final verdict

