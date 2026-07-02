from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from abqpilot.gui.artifact_viewer import preview_artifact
from abqpilot.gui.style import CTK, HAS_CUSTOMTKINTER, PALETTE


def clear_text(widget) -> None:
    widget.configure(state="normal")
    widget.delete("1.0", "end")


def set_text(widget, text: str) -> None:
    clear_text(widget)
    widget.insert("end", text)
    widget.configure(state="disabled")


def artifact_preview(path: str | None) -> str:
    return preview_artifact(path).get("preview", "No preview available.")


def make_frame(parent, padding: int | tuple[int, int] = 0, panel: bool = False):
    if HAS_CUSTOMTKINTER:
        return CTK.CTkFrame(
            parent,
            fg_color=PALETTE["panel"] if panel else PALETTE["bg"],
            corner_radius=10 if panel else 0,
        )
    return ttk.Frame(parent, padding=padding, style="Panel.TFrame" if panel else "TFrame")


def make_label(parent, text: str, font=None, muted: bool = False):
    if HAS_CUSTOMTKINTER:
        return CTK.CTkLabel(parent, text=text, font=font, text_color=PALETTE["muted"] if muted else PALETTE["text"])
    return ttk.Label(parent, text=text, font=font, style="Muted.TLabel" if muted else "TLabel")


def make_button(parent, text: str, command, *, danger: bool = False):
    if HAS_CUSTOMTKINTER:
        color = PALETTE["danger"] if danger else PALETTE["accent"]
        hover = "#934646" if danger else PALETTE["accent_hover"]
        return CTK.CTkButton(parent, text=text, command=command, fg_color=color, hover_color=hover, corner_radius=8)
    return ttk.Button(parent, text=text, command=command)


def make_text(parent, height: int, width: int | None = None):
    if HAS_CUSTOMTKINTER:
        return CTK.CTkTextbox(
            parent,
            height=height * 18,
            width=(width or 60) * 8,
            fg_color=PALETTE["panel"],
            text_color=PALETTE["text"],
            border_color=PALETTE["border"],
            border_width=1,
            corner_radius=8,
            wrap="word",
        )
    return tk.Text(
        parent,
        height=height,
        width=width,
        wrap="word",
        bg=PALETTE["panel"],
        fg=PALETTE["text"],
        insertbackground=PALETTE["text"],
        relief="flat",
        highlightthickness=1,
        highlightbackground=PALETTE["border"],
    )


def make_listbox(parent, width: int, height: int):
    return tk.Listbox(
        parent,
        width=width,
        height=height,
        bg=PALETTE["panel"],
        fg=PALETTE["text"],
        selectbackground=PALETTE["accent"],
        selectforeground="#ffffff",
        relief="flat",
        highlightthickness=1,
        highlightbackground=PALETTE["border"],
        activestyle="none",
    )
