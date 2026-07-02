from __future__ import annotations

from pathlib import Path


class InventoryTool:
    def inspect(self, base_inp_path: str | Path) -> dict:
        path = Path(base_inp_path)
        return {
            "tool": "InventoryTool",
            "base_inp_path": str(path),
            "exists": path.exists(),
            "ready": path.exists() and path.is_file(),
        }

