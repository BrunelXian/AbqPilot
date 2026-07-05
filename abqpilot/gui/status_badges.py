from __future__ import annotations


REQUIRED_BADGE_LABELS = (
    "PASS",
    "WARNING",
    "BLOCKED",
    "PENDING",
    "READY",
    "ACKNOWLEDGED",
    "LOCKED",
    "DISABLED",
    "NON_FINAL",
    "NON_SOLVER",
    "SAFE",
    "HIGH_RISK",
)


def badge(label: str, detail: str | None = None) -> str:
    normalized = label.upper().replace(" ", "_")
    if normalized not in REQUIRED_BADGE_LABELS:
        normalized = "PENDING"
    return f"[{normalized}] {detail}" if detail else f"[{normalized}]"


def status_badge(status: str | None) -> str:
    value = status or "UNKNOWN"
    if "BLOCKED" in value or "FAIL" in value:
        return badge("BLOCKED", value)
    if "WARNING" in value:
        return badge("WARNING", value)
    if "ACK" in value or "ACCEPTED" in value or "READY" in value or "PASS" in value:
        if "ACK" in value:
            return badge("ACKNOWLEDGED", value)
        if "READY" in value:
            return badge("READY", value)
        return badge("NON_FINAL", value)
    return badge("PENDING", value)


def safety_badges() -> list[str]:
    return [
        "Final evidence remains locked",
        "Solver disabled",
        "ODB disabled",
        "Metrics approval disabled",
        "Queue disabled",
        "Codex CLI disabled",
        "Auto scheduling disabled",
    ]


def all_badge_labels() -> list[str]:
    return list(REQUIRED_BADGE_LABELS)
