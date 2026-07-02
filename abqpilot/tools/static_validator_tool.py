from __future__ import annotations

from pathlib import Path


class StaticValidator:
    REQUIRED_TOKENS = ["*Heading", "*Step", "*End Step", "*Output", "NT11"]

    def validate(
        self,
        inp_path: str | Path,
        target_region: str | None = "SURF_TRACK_001_TOP",
        required_tokens: list[str] | None = None,
    ) -> dict:
        path = Path(inp_path)
        tokens = required_tokens or self.REQUIRED_TOKENS
        report = {
            "tool": "StaticValidator",
            "inp_path": str(path),
            "target_region": target_region,
            "target_region_status": "CONFIRMED" if target_region else "TARGET_REGION_NOT_CONFIRMED",
            "required_tokens": tokens,
            "passed": False,
            "missing": [],
            "errors": [],
        }
        if not path.exists():
            report["errors"].append("INP file does not exist")
            return report

        text = path.read_text(encoding="utf-8", errors="replace")
        lower_text = text.lower()
        for token in tokens:
            if token.lower() not in lower_text:
                report["missing"].append(token)
        if target_region and target_region.lower() not in lower_text:
            report["missing"].append(target_region)

        report["passed"] = not report["missing"] and not report["errors"]
        return report
