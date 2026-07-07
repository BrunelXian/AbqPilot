# Stage 5.3A-R Patch-Root Hardening Policy

All future Codex/apply_patch operations must confirm cwd, resolved project root, and git root before patching.

The only valid project root is `D:\Projects\AbqPilot-v2`.

`D:\Users\wuxia\Documents\AbqPilot` is forbidden except for explicitly approved cleanup.

Relative patch paths must not be used unless cwd and git root are confirmed. Before any patch, list the absolute path of every file to be created or modified. After patching, run a forbidden-root scan.

If apply_patch or any writer writes outside the project root, stop immediately and do not continue the implementation stage. Cleanup of the forbidden root requires explicit human approval.

Stage 5.3A-R does not run Abaqus, does not create solver_request.json, does not open ODB, does not extract metrics, does not approve final evidence, and does not freeze verdict.
