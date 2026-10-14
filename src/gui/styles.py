"""
Styling constants and modern theme helpers for CustomTkinter & TTK widgets.
"""
from tkinter import ttk
import customtkinter as ctk

# Accent Palette (Modern Indigo / Blue)
COLOR_PRIMARY = "#2563EB"       # Blue 600
COLOR_PRIMARY_HOVER = "#1D4ED8" # Blue 700

COLOR_SUCCESS = "#059669"       # Emerald 600
COLOR_SUCCESS_HOVER = "#047857"

COLOR_WARNING = "#D97706"       # Amber 600
COLOR_DANGER = "#DC2626"        # Red 600
COLOR_DANGER_HOVER = "#B91C1C"

COLOR_CARD_DARK = "#1E293B"     # Slate 800
COLOR_CARD_LIGHT = "#FFFFFF"

# Fonts
FONT_HEADING = ("Segoe UI", 20, "bold")
FONT_SUBTITLE = ("Segoe UI", 14, "bold")
FONT_SECTION = ("Segoe UI", 12, "bold")
FONT_BODY = ("Segoe UI", 11)
FONT_BODY_BOLD = ("Segoe UI", 11, "bold")
FONT_SMALL = ("Segoe UI", 9)
FONT_MONO = ("Consolas", 10)


def configure_treeview_theme(style: ttk.Style, mode: str = "Dark") -> None:
    """Synchronize TTK Treeview styling with CustomTkinter appearance mode."""
    is_dark = mode.lower() == "dark"

    bg_main = "#18181B" if is_dark else "#FFFFFF"
    fg_main = "#F4F4F5" if is_dark else "#09090B"
    bg_alt = "#27272A" if is_dark else "#F8FAFC"
    bg_heading = "#27272A" if is_dark else "#E4E4E7"
    fg_heading = "#FFFFFF" if is_dark else "#18181B"
    sel_bg = "#3B82F6" if is_dark else "#BFDBFE"
    sel_fg = "#FFFFFF" if is_dark else "#1E3A8A"

    style.configure(
        "Treeview",
        background=bg_main,
        foreground=fg_main,
        fieldbackground=bg_main,
        rowheight=28,
        font=FONT_BODY,
        borderwidth=0,
        relief="flat"
    )
    style.configure(
        "Treeview.Heading",
        background=bg_heading,
        foreground=fg_heading,
        font=FONT_SECTION,
        padding=[8, 8],
        relief="flat"
    )
    style.map(
        "Treeview.Heading",
        background=[("active", "#3F3F46" if is_dark else "#D4D4D8")],
        foreground=[("active", fg_heading)]
    )
    style.map(
        "Treeview",
        background=[("selected", sel_bg)],
        foreground=[("selected", sel_fg)]
    )
