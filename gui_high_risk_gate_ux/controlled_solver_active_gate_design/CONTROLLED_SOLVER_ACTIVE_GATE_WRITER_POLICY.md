# Controlled Solver Active Gate Writer Policy

ACTIVE_GATE_WRITER_DISABLED_IN_STAGE_5_2D

- writer_enabled=false
- No real active gate is written under real task `gates/`.
- No active execution handoff is written under real task `handoffs/`.
- No solver request file is created.
- Future explicit stage must enable and revalidate writer behavior.
