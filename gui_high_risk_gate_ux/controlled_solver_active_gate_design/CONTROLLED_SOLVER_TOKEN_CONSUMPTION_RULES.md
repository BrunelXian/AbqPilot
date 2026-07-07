# Controlled Solver Token Consumption Rules

- Token must be valid before consumption.
- Token must be one-time use.
- Token must bind to task_id.
- Token must bind to candidate artifact hash.
- Token must verify exact approval phrase.
- All acknowledgement flags must be true.
- Consumed token must not be reused.
- Token consumption does not execute solver.
- Token consumption does not approve ODB, metrics, final evidence, or final verdict.
