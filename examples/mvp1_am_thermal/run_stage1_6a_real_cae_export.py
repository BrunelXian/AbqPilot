from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from abqpilot.cae import CaeInpExporter


def main() -> int:
    config = _load_runtime_config(PROJECT_ROOT / "abqpilot" / "configs" / "abaqus_runtime.yaml")
    sanity_dir = PROJECT_ROOT / "CAE_model" / "sanity_base"
    output_dir = PROJECT_ROOT / "runs" / "stage1_6a_cae_to_inp_export"
    cae_path = sanity_dir / "sanity_base_v01.cae"

    exporter = CaeInpExporter(
        abaqus_command=config["abaqus_command"],
        allow_cae_export=config["allow_cae_export"],
        cae_export_mode=config["cae_export_mode"],
        allow_solver_submit=config["allow_solver_submit"],
        allow_odb_read=config["allow_odb_read"],
        allow_abqjobpilot=config["allow_abqjobpilot"],
        allow_llm=config["allow_llm"],
        timeout_s=300,
    )
    request = exporter.prepare_export(
        cae_path=str(cae_path),
        output_dir=str(output_dir),
        job_name="sanity_base_v01_export",
    )
    report = exporter.export(request)

    print(f"verdict={report['verdict']}")
    print(f"executed={str(report['executed']).lower()}")
    print(f"expected_inp={report['expected_inp_path']}")
    print(f"report={Path(report['output_dir']) / 'cae_export_report.json'}")
    return 0 if report["verdict"] == "CAE_EXPORT_COMPLETED" else 1


def _load_runtime_config(path: Path) -> dict:
    runtime: dict[str, object] = {}
    in_runtime = False
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        if raw_line.startswith("runtime:"):
            in_runtime = True
            continue
        if not in_runtime or not raw_line.startswith("  "):
            continue
        key, value = raw_line.strip().split(":", 1)
        runtime[key] = _parse_scalar(value.strip())
    return runtime


def _parse_scalar(value: str) -> object:
    lowered = value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    try:
        return int(value)
    except ValueError:
        return value


if __name__ == "__main__":
    raise SystemExit(main())

