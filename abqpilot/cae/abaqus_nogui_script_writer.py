from __future__ import annotations

from pathlib import Path


def write_input_export_script(
    script_path: str | Path,
    cae_path: str | Path,
    output_dir: str | Path,
    job_name: str,
) -> Path:
    script = build_input_export_script(cae_path=cae_path, output_dir=output_dir, job_name=job_name)
    path = Path(script_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(script, encoding="utf-8")
    return path


def build_input_export_script(cae_path: str | Path, output_dir: str | Path, job_name: str) -> str:
    return f'''from abaqus import mdb, openMdb
from abaqusConstants import OFF
import os

cae_path = r"{Path(cae_path)}"
job_name = "{job_name}"
output_dir = r"{Path(output_dir)}"

os.chdir(output_dir)
openMdb(pathName=cae_path)

model_names = list(mdb.models.keys())
if not model_names:
    raise RuntimeError("No models found in CAE database.")

model_name = model_names[0]

job = mdb.Job(
    name=job_name,
    model=model_name,
    description="AbqPilot controlled INP export only",
)

job.writeInput(consistencyChecking=OFF)
'''
