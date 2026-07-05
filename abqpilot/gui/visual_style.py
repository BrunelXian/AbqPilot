from __future__ import annotations


VISUAL_TOKENS = {
    "surface": "panel",
    "surface_muted": "subtle_panel",
    "text_primary": "text",
    "text_muted": "muted",
    "accent_safe": "safe",
    "accent_warning": "warning",
    "accent_blocked": "blocked",
    "accent_locked": "locked",
    "accent_disabled": "disabled",
}

BADGE_STYLES = {
    "PASS": "safe",
    "WARNING": "warning",
    "BLOCKED": "blocked",
    "PENDING": "pending",
    "READY": "ready",
    "ACKNOWLEDGED": "safe",
    "LOCKED": "locked",
    "DISABLED": "disabled",
    "NON_FINAL": "non_final",
    "NON_SOLVER": "non_solver",
    "SAFE": "safe",
    "HIGH_RISK": "high_risk",
}

LAYOUT_COLUMNS = {
    "left": "Task / navigation",
    "center": "Workflow state and timeline",
    "right": "Next safe action and disabled high-risk actions",
    "lower": "Trace / report / ledger summary",
}


def visual_token(name: str) -> str:
    return VISUAL_TOKENS.get(name, name)
