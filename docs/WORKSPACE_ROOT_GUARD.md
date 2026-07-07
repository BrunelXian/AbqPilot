# Workspace Root Guard

Stage 5.3A-R documents the remediation after a failed Stage 5.3A attempt wrote relative patch paths under the forbidden root.

The only valid project root is `D:\Projects\AbqPilot-v2`.

The root `D:\Users\wuxia\Documents\AbqPilot` is forbidden for project writes. It may be touched only for explicitly approved cleanup of known stray files, and cleanup must be limited to the exact approved files or files that clearly contain the failed-stage markers.

Before any future Codex or apply_patch operation:

- confirm the current working directory
- confirm the resolved project root
- confirm the git root when available
- list the absolute path of every file to be created or modified
- verify each target is under `D:\Projects\AbqPilot-v2`

Relative patch paths must not be used unless the cwd and git root are already confirmed. If apply_patch or any other writer creates or modifies a file outside the project root, stop immediately and do not continue the implementation stage.

After patching, run a forbidden-root scan for the relevant stage markers. Cleanup of the forbidden root requires explicit human approval.

Stage 5.3A-R did not run Abaqus, did not create `solver_request.json`, did not open ODB, did not extract metrics, and did not touch final evidence.

## Stage 5.3A-v2 Application

Stage 5.3A-v2 must run the workspace guard before patching, confirm the forbidden-root pre-scan has zero hits, print absolute write targets before writing, and run the forbidden-root scan again after patching. Any write under `D:\Users\wuxia\Documents\AbqPilot` is a safety failure for this stage.
