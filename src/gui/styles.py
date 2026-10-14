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
    # Ensure clam theme is used for reliable custom coloring across platforms
    if "clam" in style.theme_names():
        style.theme_use("clam")

    is_dark = mode.lower() == "dark"

    bg_main = "#18181B" if is_dark else "#FFFFFF"
    fg_main = "#F4F4F5" if is_dark else "#0F172A"
    bg_heading = "#27272A" if is_dark else "#E2E8F0"
    fg_heading = "#FFFFFF" if is_dark else "#0F172A"
    sel_bg = "#2563EB" if is_dark else "#BFDBFE"
    sel_fg = "#FFFFFF" if is_dark else "#1E3A8A"

    style.configure(
        "Treeview",
        background=bg_main,
        foreground=fg_main,
        fieldbackground=bg_main,
        rowheight=30,
        font=FONT_BODY,
        borderwidth=0,
        relief="flat"
    )
    style.configure(
        "Treeview.Heading",
        background=bg_heading,
        foreground=fg_heading,
        font=FONT_SECTION,
        padding=[10, 8],
        relief="flat",
        borderwidth=0
    )
    style.map(
        "Treeview.Heading",
        background=[("active", "#3F3F46" if is_dark else "#CBD5E1")],
        foreground=[("active", fg_heading)]
    )
    style.map(
        "Treeview",
        background=[("selected", sel_bg)],
        foreground=[("selected", sel_fg)]
    )


def apply_treeview_row_tags(tree: ttk.Treeview, view_type: str = "books", mode: str = "Dark") -> None:
    """Dynamically configure row tag colors based on current appearance mode."""
    is_dark = mode.lower() == "dark"

    if view_type == "books":
        tree.tag_configure(
            "evenrow",
            background="#18181B" if is_dark else "#FFFFFF",
            foreground="#F4F4F5" if is_dark else "#0F172A"
        )
        tree.tag_configure(
            "oddrow",
            background="#27272A" if is_dark else "#F8FAFC",
            foreground="#F4F4F5" if is_dark else "#0F172A"
        )
        tree.tag_configure(
            "unavailable",
            background="#7F1D1D" if is_dark else "#FEE2E2",
            foreground="#FCA5A5" if is_dark else "#991B1B"
        )
    elif view_type == "transactions":
        tree.tag_configure(
            "returned",
            background="#18181B" if is_dark else "#FFFFFF",
            foreground="#F4F4F5" if is_dark else "#0F172A"
        )
        tree.tag_configure(
            "active_ontime",
            background="#2E2A14" if is_dark else "#FEFCE8",
            foreground="#FDE68A" if is_dark else "#854D0E"
        )
        tree.tag_configure(
            "active_overdue",
            background="#7F1D1D" if is_dark else "#FEE2E2",
            foreground="#FCA5A5" if is_dark else "#991B1B"
        )
