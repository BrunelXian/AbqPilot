from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

from abqpilot.odb.abaqus_odb_script_writer import write_odb_metrics_script


REQUIRED_SCRIPT_TOKENS = ["open" + "Odb"]
FORBIDDEN_SCRIPT_TOKENS = [
    "sub" + "mit(",
    "wait" + "ForCompletion",
    "mdb." + "Job",
    "write" + "Input",
    "save" + "As",
    "os." + "system",
    "sub" + "process",
    "Po" + "pen",
    "en" + "queue",
    "abq" + "jobpilot",
]


class OdbMetricsExtractor:
    def __init__(
        self,
        abaqus_command: str,
        allow_odb_read: bool = False,
        odb_read_mode: str = "disabled",
        allow_solver_submit: bool = False,
        allow_abqjobpilot: bool = False,
        allow_llm: bool = False,
        timeout_s: int = 300,
    ) -> None:
        self.abaqus_command = abaqus_command
        self.allow_odb_read = allow_odb_read
        self.odb_read_mode = odb_read_mode
        self.allow_solver_submit = allow_solver_submit
        self.allow_abqjobpilot = allow_abqjobpilot
        self.allow_llm = allow_llm
        self.timeout_s = timeout_s

    def prepare_request(self, contract_path: str | Path, output_dir: str | Path) -> dict:
        contract_file = Path(contract_path)
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        if not contract_file.exists():
            request = self._request(contract_file, out_dir)
            request["verdict"] = "FAIL_ODB_PAIR_NOT_FOUND"
            request["errors"] = ["contract file does not exist"]
            self._write_json(out_dir / "odb_metrics_extraction_request.json", request)
            return request

        contract = json.loads(contract_file.read_text(encoding="utf-8"))
        request = self._request(contract_file, out_dir)
        request["contract"] = contract
        missing = [
            case.get("odb_path")
            for case in contract.get("cases", [])
            if not case.get("odb_path") or not Path(case["odb_path"]).exists()
        ]
        if len(contract.get("cases", [])) != 2 or missing:
            request["verdict"] = "FAIL_ODB_PAIR_NOT_FOUND"
            request["errors"] = [f"missing ODB paths: {missing}"]
        else:
            write_odb_metrics_script(
                script_path=request["script_path"],
                contract_path=contract_file,
                output_json_path=request["metrics_json_path"],
            )
            request["verdict"] = "ODB_METRICS_REQUEST_PREPARED"
        self._write_json(out_dir / "odb_metrics_extraction_request.json", request)
        return request

    def extract(self, request: dict) -> dict:
        report = {
            "request_path": str(Path(request["output_dir"]) / "odb_metrics_extraction_request.json"),
            "contract_path": request.get("contract_path"),
            "script_path": request.get("script_path"),
            "metrics_json_path": request.get("metrics_json_path"),
            "abaqus_command": self.abaqus_command,
            "allow_odb_read": self.allow_odb_read,
            "odb_read_mode": self.odb_read_mode,
            "allow_solver_submit": self.allow_solver_submit,
            "allow_abqjobpilot": self.allow_abqjobpilot,
            "allow_llm": self.allow_llm,
            "executed": False,
            "command": None,
            "return_code": None,
            "stdout_tail": "",
            "stderr_tail": "",
            "safety_scan": {},
            "verdict": "FAIL_ODB_PAIR_NOT_FOUND" if request.get("verdict") == "FAIL_ODB_PAIR_NOT_FOUND" else "ODB_READ_DISABLED",
            "errors": list(request.get("errors", [])),
        }
        output_dir = Path(request["output_dir"])

        if request.get("verdict") == "FAIL_ODB_PAIR_NOT_FOUND":
            self._write_json(output_dir / "odb_metrics_extraction_report.json", report)
            return report

        gate_error = self._gate_error(request)
        if gate_error:
            report["verdict"] = gate_error["verdict"]
            report["errors"].append(gate_error["error"])
            self._write_json(output_dir / "odb_metrics_extraction_report.json", report)
            return report

        safety_scan = scan_odb_script_safety(request["script_path"])
        report["safety_scan"] = safety_scan
        if not safety_scan["safe"]:
            report["verdict"] = "FAIL_ODB_EXTRACT_SCRIPT_UNSAFE"
            report["errors"].extend(safety_scan["forbidden_hits"] + safety_scan["required_missing"])
            self._write_json(output_dir / "odb_metrics_extraction_report.json", report)
            return report

        command = [self.abaqus_command, "python", request["script_path"]]
        report["command"] = command
        try:
            completed = subprocess.run(
                command,
                cwd=request["output_dir"],
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
            report["verdict"] = "FAIL_ODB_EXTRACT_COMMAND_FAILED"
            report["errors"].append(f"timeout after {self.timeout_s}s")
            report["stdout_tail"] = _tail(exc.stdout or "")
            report["stderr_tail"] = _tail(exc.stderr or "")
            self._write_json(output_dir / "odb_metrics_extraction_report.json", report)
            return report

        if report["return_code"] != 0:
            report["verdict"] = "FAIL_ODB_EXTRACT_COMMAND_FAILED"
            self._write_json(output_dir / "odb_metrics_extraction_report.json", report)
            return report

        metrics_path = Path(request["metrics_json_path"])
        if not metrics_path.exists():
            report["verdict"] = "FAIL_ODB_METRICS_JSON_MISSING"
            self._write_json(output_dir / "odb_metrics_extraction_report.json", report)
            return report

        metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
        report["metrics_summary"] = summarize_metrics(metrics)
        if len(metrics.get("cases", [])) != 2:
            report["verdict"] = "FAIL_ODB_METRICS_INCOMPLETE"
        elif any(not case.get("metrics") and not case.get("missing_fields") for case in metrics.get("cases", [])):
            report["verdict"] = "FAIL_ODB_METRICS_INCOMPLETE"
        else:
            report["verdict"] = "PASS_ABQPILOT_V2_STAGE1_8_GATED_ODB_METRICS_EXTRACTION_READY"
        self._write_json(output_dir / "odb_metrics_extraction_report.json", report)
        return report

    def _gate_error(self, request: dict) -> dict | None:
        if not self.allow_odb_read:
            return {"verdict": "ODB_READ_DISABLED", "error": "allow_odb_read must be true"}
        if self.odb_read_mode != "metrics_only":
            return {"verdict": "ODB_READ_DISABLED", "error": "odb_read_mode must be metrics_only"}
        if self.allow_solver_submit:
            return {"verdict": "ODB_READ_DISABLED", "error": "allow_solver_submit must be false"}
        if self.allow_abqjobpilot:
            return {"verdict": "ODB_READ_DISABLED", "error": "allow_abqjobpilot must be false"}
        if self.allow_llm:
            return {"verdict": "ODB_READ_DISABLED", "error": "allow_llm must be false"}
        if not Path(self.abaqus_command).exists():
            return {"verdict": "FAIL_ODB_EXTRACT_COMMAND_FAILED", "error": "abaqus_command does not exist"}
        if not Path(request["script_path"]).exists():
            return {"verdict": "FAIL_ODB_EXTRACT_COMMAND_FAILED", "error": "extract script does not exist"}
        return None

    def _request(self, contract_path: Path, output_dir: Path) -> dict:
        return {
            "contract_path": str(contract_path),
            "output_dir": str(output_dir),
            "script_path": str(output_dir / "extract_stage1_8_odb_metrics.py"),
            "metrics_json_path": str(output_dir / "odb_metrics_pair.json"),
            "abaqus_command": self.abaqus_command,
            "allow_odb_read": self.allow_odb_read,
            "odb_read_mode": self.odb_read_mode,
            "allow_solver_submit": self.allow_solver_submit,
            "allow_abqjobpilot": self.allow_abqjobpilot,
            "allow_llm": self.allow_llm,
            "verdict": "ODB_METRICS_REQUEST_PREPARED",
            "errors": [],
        }

    @staticmethod
    def _write_json(path: Path, payload: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def scan_odb_script_safety(script_path: str | Path) -> dict:
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
    executable_text = _strip_quoted_strings(text)
    required_present = [token for token in REQUIRED_SCRIPT_TOKENS if token in text]
    required_missing = [token for token in REQUIRED_SCRIPT_TOKENS if token not in text]
    forbidden_hits = [token for token in FORBIDDEN_SCRIPT_TOKENS if token in executable_text]
    return {
        "script_path": str(path),
        "safe": not required_missing and not forbidden_hits,
        "required_present": required_present,
        "required_missing": required_missing,
        "forbidden_hits": forbidden_hits,
    }


def summarize_metrics(metrics: dict) -> dict:
    return {
        "case_count": len(metrics.get("cases", [])),
        "case_statuses": [
            {
                "case_id": case.get("case_id"),
                "status": case.get("status"),
                "missing_fields": case.get("missing_fields", []),
            }
            for case in metrics.get("cases", [])
        ],
        "comparison": metrics.get("comparison", {}),
    }


def safe_ratio(base: float | None, power: float | None) -> float | None:
    if base in (None, 0) or power is None:
        return None
    return power / base


def _strip_quoted_strings(text: str) -> str:
    return re.sub(r"(?i)r?(['\"])(?:\\.|(?!\1).)*\1", '""', text)


def _tail(text: str, limit: int = 4000) -> str:
    return text[-limit:] if len(text) > limit else text
