# Model Condition Preservation Guard

Stage 4.5 introduces the Model Condition Preservation Guard, or MCPGuard.

MCPGuard generalizes the Stage 4.3 DFLUX lifecycle issue. The lesson is not simply that DFLUX must always be reset during cooling. The broader rule is that original model conditions must not be lost, changed, or semantically drifted during CAE export, INP patching, candidate generation, and controlled solver execution.

MCPGuard compares:

```text
source CAE/JNL condition intent
-> source exported INP representation
-> patched candidate INP representation
-> solver-run INP representation
```

It complements StaticValidator, DiffGuard, and PhysicsGuard. It does not run Abaqus, does not open ODB files, and does not mutate simulation files.

## Categories

Stage 4.5 defines these condition categories:

- `load_lifecycle`
- `boundary_lifecycle`
- `interaction_lifecycle`
- `amplitude_lifecycle`
- `step_procedure`
- `output_request`
- `reference_integrity`
- `target_patch_isolation`

The concrete Stage 4.5 implemented sub-check is:

```text
MCPGuard.load_lifecycle.body_heat_flux_dflux_bf
```

For the sanity-base case, the JNL says `load_body_hflux_00` is created in `step_scan_00` and deactivated in `Step_cool_00`. For BodyHeatFlux exported as DFLUX/BF, MCPGuard requires explicit candidate INP reset/removal evidence in the cooling step, such as:

```text
*Dflux, OP=NEW
```

If this representation is missing, MCPGuard reports:

```text
CONDITION_LOSS_LOAD_LIFECYCLE_DEACTIVATION_MISSING
```

## CLI

```powershell
D:\XianLab\envs\conda\LangChainEnv\Scripts\python.exe -m abqpilot.cli run-model-condition-guard --source-jnl <jnl> --source-inp <source_inp> --candidate-inp <candidate_inp> --solver-inp <solver_inp> --target-change body_heat_flux_magnitude:load_body_hflux_00:step_scan_00:1e+10:2e+10
```

The guard writes:

- `model_condition_source_intent.json`
- `model_condition_source_exported_inp.json`
- `model_condition_candidate_inp.json`
- `model_condition_solver_inp.json`
- `model_condition_preservation_result.json`
- `model_condition_preservation_report.md`

Future solver eligibility should require:

```text
StaticValidator
DiffGuard
PhysicsGuard
MCPGuard
```
