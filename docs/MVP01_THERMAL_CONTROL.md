# MVP-01 Thermal Control

MVP-01 proves this dry-run chain:

```text
base_heatflux_marker.inp
-> objective_spec.json
-> build_request.json
-> generated.inp
-> StaticValidator
-> DiffGuard
-> PhysicsGuard
-> dry-run JobPilotAdapter
-> fixture ODB metrics
-> EvalRepairTool
-> repair_plan.json
-> parameter_history.json
-> trace
-> PASS / REPAIR / FAIL_STOP
```

Only the heat-flux magnitude inside a single explicit marker block may change:

```text
** ABQPILOT_EDITABLE_HEAT_FLUX_START id=HF_SURF_TRACK_001_TOP
*Dsflux
SURF_TRACK_001_TOP, S, 1000000.0
** ABQPILOT_EDITABLE_HEAT_FLUX_END id=HF_SURF_TRACK_001_TOP
```

No Abaqus solver, ODB opening, DFLUX, Fortran, CAE generation, Web UI, database, RAG, LangGraph, or multi-agent chat is implemented.

