from __future__ import annotations


class PhysicsGuard:
    def check(self, diff_report: dict | None) -> dict:
        report = {
            "tool": "PhysicsGuard",
            "passed": False,
            "errors": [],
            "diff_report_allowed": False,
        }
        if not diff_report:
            report["errors"].append("missing diff report")
            return report

        report["diff_report_allowed"] = bool(diff_report.get("allowed"))
        if diff_report.get("forbidden_changed"):
            report["errors"].append("diff guard reported forbidden changes")
        if diff_report.get("uncertainty"):
            report["errors"].append("diff guard reported uncertainty")
        if not diff_report.get("allowed"):
            report["errors"].append("diff guard did not allow the change")

        report["passed"] = not report["errors"]
        return report

