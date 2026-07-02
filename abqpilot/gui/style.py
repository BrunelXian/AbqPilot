from __future__ import annotations

try:  # Optional dependency: use when present, keep tkinter fallback safe.
    import customtkinter as ctk
except ImportError:  # pragma: no cover - depends on local desktop environment.
    ctk = None


APP_TITLE = "AbqPilot-v2"
DISABLED_ACTION_MESSAGE = "This action is disabled in GUI Beta and requires a future gated stage."
HAS_CUSTOMTKINTER = ctk is not None
CTK = ctk

PALETTE = {
    "bg": "#0f1419",
    "panel": "#171d24",
    "panel_alt": "#1d2630",
    "border": "#2a3441",
    "text": "#e6edf3",
    "muted": "#93a4b7",
    "accent": "#4f8cff",
    "accent_hover": "#3f76d8",
    "danger": "#b85c5c",
    "success": "#4fa36c",
}


def configure_window_theme(root) -> None:
    if HAS_CUSTOMTKINTER:
        CTK.set_appearance_mode("dark")
        CTK.set_default_color_theme("blue")
    try:
        root.configure(bg=PALETTE["bg"])
    except Exception:
        pass


def configure_ttk_style(root) -> None:
    import tkinter.ttk as ttk

    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except Exception:
        pass
    style.configure("TFrame", background=PALETTE["bg"])
    style.configure("Panel.TFrame", background=PALETTE["panel"])
    style.configure("TLabel", background=PALETTE["bg"], foreground=PALETTE["text"])
    style.configure("Muted.TLabel", background=PALETTE["bg"], foreground=PALETTE["muted"])
    style.configure("TButton", padding=(10, 7), background=PALETTE["panel_alt"], foreground=PALETTE["text"])
    style.map("TButton", background=[("active", PALETTE["accent"])])
    style.configure("TSeparator", background=PALETTE["border"])
