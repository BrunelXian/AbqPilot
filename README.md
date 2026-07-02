# AbqPilot

AbqPilot: A closed-loop CAE-ODB agent for Abaqus simulation automation

AbqPilot：面向 Abaqus 仿真自动化的闭环 CAE-ODB Agent

AbqPilot is an Abaqus simulation task compiler plus ODB-feedback-driven self-iteration agent. MVP-01 is deterministic and dry-run only: it edits a single heat-flux marker, validates the generated INP, applies static diff and physics guards, prepares a dry job command, reads fixture metrics, and produces an auditable evaluation/repair verdict.

MVP-01 does not run Abaqus, open ODB files, call LLMs, use LangGraph, submit jobs, or generate real CAE.

## Quick Check

```powershell
D:\XianLab\envs\conda\LangChainEnv\Scripts\python.exe -m pytest -q
D:\XianLab\envs\conda\LangChainEnv\Scripts\python.exe examples\mvp1_am_thermal\run_v2_dry_pipeline.py
D:\XianLab\envs\conda\LangChainEnv\Scripts\python.exe examples\mvp1_am_thermal\run_v2_eval_repair_loop.py
```

