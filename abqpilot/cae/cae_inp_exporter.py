from __future__ import annotations

import json
import subprocess
from pathlib import Path

from abqpilot.cae.abaqus_nogui_script_writer import write_input_export_script


class CaeInpExporter:
    def __init__(
        self,
        abaqus_command: str,
        allow_cae_export: bool = False,
        cae_export_mode: str = "disabled",
        allow_solver_submit: bool = False,
        allow_odb_read: bool = False,
        allow_abqjobpilot: bool = False,
        allow_llm: bool = False,
        timeout_s: int = 120,
    ):
        self.abaqus_command = abaqus_command
        self.allow_cae_export = allow_cae_export
        self.cae_export_mode = cae_export_mode
        self.allow_solver_submit = allow_solver_submit
        self.allow_odb_read = allow_odb_read
        self.allow_abqjobpilot = allow_abqjobpilot
        self.allow_llm = allow_llm
        self.timeout_s = timeout_s

    def prepare_export(self, cae_path: str, output_dir: str, job_name: str | None = None) -> dict:
        cae = Path(cae_path)
        if not cae.exists():
            raise FileNotFoundError(f"CAE file does not exist: {cae}")
        if cae.suffix.lower() != ".cae":
            raise ValueError(f"Expected a .cae file: {cae}")

        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        selected_job_name = job_name or f"{cae.stem}_export"
        expected_inp_path = out_dir / f"{selected_job_name}.inp"
        script_path = out_dir / f"{selected_job_name}_write_input.py"
        jnl_path = cae.with_suffix(".jnl")

        write_input_export_script(
            script_path=script_path,
            cae_path=cae,
            output_dir=out_dir,
            job_name=selected_job_name,
        )

        request = {
            "cae_path": str(cae),
            "jnl_path": str(jnl_path) if jnl_path.exists() else None,
            "output_dir": str(out_dir),
            "job_name": selected_job_name,
            "expected_inp_path": str(expected_inp_path),
            "script_path": str(script_path),
            "abaqus_command": self.abaqus_command,
            "allow_cae_export": self.allow_cae_export,
            "cae_export_mode": self.cae_export_mode,
            "allow_solver_submit": self.allow_solver_submit,
            "allow_odb_read": self.allow_odb_read,
            "allow_abqjobpilot": self.allow_abqjobpilot,
            "allow_llm": self.allow_llm,
            "executed": False,
            "verdict": "CAE_EXPORT_PREPARED",
        }
        (out_dir / "cae_export_request.json").write_text(
            json.dumps(request, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return request

    def export(self, export_request: dict) -> dict:
        report = {
            "cae_path": export_request.get("cae_path"),
            "jnl_path": export_request.get("jnl_path"),
            "output_dir": export_request.get("output_dir"),
            "job_name": export_request.get("job_name"),
            "expected_inp_path": export_request.get("expected_inp_path"),
            "script_path": export_request.get("script_path"),
            "abaqus_command": export_request.get("abaqus_command", self.abaqus_command),
            "allow_cae_export": self.allow_cae_export,
            "cae_export_mode": self.cae_export_mode,
            "allow_solver_submit": self.allow_solver_submit,
            "allow_odb_read": self.allow_odb_read,
            "allow_abqjobpilot": self.allow_abqjobpilot,
            "allow_llm": self.allow_llm,
            "executed": False,
            "command": None,
            "return_code": None,
            "stdout_tail": "",
            "stderr_tail": "",
            "safety_scan": {},
            "verdict": "CAE_EXPORT_DISABLED",
        }

        if not self.allow_cae_export:
            self._write_report(report)
            return report

        gate_error = self._gate_error(report)
        if gate_error:
            report["verdict"] = gate_error["verdict"]
            report["errors"] = [gate_error["error"]]
            self._write_report(report)
            return report

        safety_scan = scan_export_script_safety(Path(report["script_path"]))
        report["safety_scan"] = safety_scan
        if not safety_scan["safe"]:
            report["verdict"] = "FAIL_CAE_EXPORT_SCRIPT_UNSAFE"
            report["errors"] = safety_scan["forbidden_hits"]
            self._write_report(report)
            return report

        command = [
            self.abaqus_command,
            "cae",
            f"noGUI={report['script_path']}",
        ]
        report["command"] = command

        try:
            completed = subprocess.run(
                command,
                cwd=report["output_dir"],
                capture_output=True,
                text=True,
                timeout=self.timeout_s,
                shell=False,
            )
            report["executed"] = True
            report["return_code"] = completed.returncode
            report["stdout_tail"] = _tail(completed.stdout)
            report["stderr_tail"] = _tail(completed.stderr)
        except subprocess.TimeoutExpired as exc:
            report["executed"] = True
            report["return_code"] = None
            report["stdout_tail"] = _tail(exc.stdout or "")
            report["stderr_tail"] = _tail(exc.stderr or "")
            report["verdict"] = "CAE_EXPORT_FAILED_COMMAND"
            report["errors"] = [f"timeout after {self.timeout_s}s"]
            self._write_report(report)
            return report

        if report["return_code"] != 0:
            report["verdict"] = "CAE_EXPORT_FAILED_COMMAND"
            self._write_report(report)
            return report

        combined_tail = f"{report['stdout_tail']}\n{report['stderr_tail']}"
        if "Abaqus Error" in combined_tail or "Traceback" in combined_tail:
            report["verdict"] = "CAE_EXPORT_FAILED_COMMAND"
            self._write_report(report)
            return report

        expected_inp = Path(report["expected_inp_path"])
        if not expected_inp.exists():
            report["verdict"] = "CAE_EXPORT_FAILED_NO_INP"
            self._write_report(report)
            return report

        report["verdict"] = "CAE_EXPORT_COMPLETED"
        self._write_report(report)
        return report

    def _gate_error(self, report: dict) -> dict | None:
        if self.cae_export_mode != "write_input_only":
            return {"verdict": "CAE_EXPORT_DISABLED", "error": "cae_export_mode is not write_input_only"}
        if self.allow_solver_submit:
            return {"verdict": "CAE_EXPORT_DISABLED", "error": "allow_solver_submit must be false"}
        if self.allow_odb_read:
            return {"verdict": "CAE_EXPORT_DISABLED", "error": "allow_odb_read must be false"}
        if self.allow_abqjobpilot:
            return {"verdict": "CAE_EXPORT_DISABLED", "error": "allow_abqjobpilot must be false"}
        if self.allow_llm:
            return {"verdict": "CAE_EXPORT_DISABLED", "error": "allow_llm must be false"}
        if not Path(self.abaqus_command).exists():
            return {"verdict": "CAE_EXPORT_FAILED_COMMAND", "error": "abaqus_command does not exist"}
        script_path = report.get("script_path")
        if not script_path or not Path(script_path).exists():
            return {"verdict": "CAE_EXPORT_FAILED_COMMAND", "error": "generated script does not exist"}
        return None

    def _write_report(self, report: dict) -> None:
        output_dir = report.get("output_dir")
        if output_dir:
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            Path(output_dir, "cae_export_report.json").write_text(
                json.dumps(report, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )


REQUIRED_SCRIPT_TOKENS = ["writeInput", "openMdb"]
FORBIDDEN_SCRIPT_TOKENS = [
    "sub" + "mit(",
    "wait" + "ForCompletion",
    "open" + "Odb",
    "session." + "open" + "Odb",
    "mdb.jobs[",
    "os." + "system",
    "sub" + "process",
    "Po" + "pen",
    "en" + "queue",
    "abq" + "jobpilot",
]


def scan_export_script_safety(script_path: str | Path) -> dict:
    path = Path(script_path)
    if not path.exists():
        return {
            "script_path": str(path),
            "safe": False,
            "required_present": [],
            "required_missing": REQUIRED_SCRIPT_TOKENS,
            "forbidden_hits": ["SCRIPT_MISSING"],
        }
    text = path.read_text(encoding="utf-8", errors="replace")
    required_present = [token for token in REQUIRED_SCRIPT_TOKENS if token in text]
    required_missing = [token for token in REQUIRED_SCRIPT_TOKENS if token not in text]
    forbidden_hits = [token for token in FORBIDDEN_SCRIPT_TOKENS if token in text]
    return {
        "script_path": str(path),
        "safe": not required_missing and not forbidden_hits,
        "required_present": required_present,
        "required_missing": required_missing,
        "forbidden_hits": forbidden_hits,
    }


def _tail(text: str, limit: int = 4000) -> str:
    return text[-limit:] if len(text) > limit else text
