from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from abqpilot.cae import CaeInpExporter


def main() -> int:
    sanity_dir = PROJECT_ROOT / "CAE_model" / "sanity_base"
    output_dir = PROJECT_ROOT / "runs" / "stage1_6a_cae_to_inp_export"
    cae_path = sanity_dir / "sanity_base_v01.cae"

    if not cae_path.exists():
        print("verdict=CAE_FILE_NOT_FOUND")
        print(f"cae_path={cae_path}")
        return 1

    exporter = CaeInpExporter(
        abaqus_command=r"D:\ABAQUS2024\Commands\abq2024.bat",
        allow_cae_export=False,
    )
    request = exporter.prepare_export(
        cae_path=str(cae_path),
        output_dir=str(output_dir),
        job_name="sanity_base_v01_export",
    )
    report = exporter.export(request)

    print(f"verdict={report['verdict']}")
    print(f"expected_inp={report['expected_inp_path']}")
    print(f"script_path={report['script_path']}")
    return 0 if report["verdict"] == "CAE_EXPORT_DISABLED" and not report["executed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

