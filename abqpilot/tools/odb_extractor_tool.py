from __future__ import annotations

import json
from pathlib import Path


class OdbExtractorTool:
    """Fixture-only metrics extractor for MVP-01."""

    def extract(self, fixture_metrics_path: str | Path) -> dict:
        path = Path(fixture_metrics_path)
        if not path.exists():
            return {
                "tool": "OdbExtractorTool",
                "mode": "fixture_only",
                "ok": False,
                "errors": ["fixture metrics file does not exist"],
            }
        with path.open("r", encoding="utf-8") as handle:
            metrics = json.load(handle)
        metrics["tool"] = "OdbExtractorTool"
        metrics["mode"] = "fixture_only"
        metrics["ok"] = True
        return metrics

