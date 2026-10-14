"""
Modern Analytics and Visual Dashboard View built with CustomTkinter and Matplotlib.
"""
from typing import Callable
import customtkinter as ctk
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from ..database import LibraryDatabase
from .styles import (
    COLOR_DANGER,
    COLOR_PRIMARY,
    COLOR_SUCCESS,
    COLOR_WARNING,
    FONT_BODY,
    FONT_BODY_BOLD,
    FONT_HEADING,
    FONT_SECTION,
    FONT_SMALL,
    FONT_SUBTITLE,
)


class AnalyticsView(ctk.CTkScrollableFrame):
    """Modern dashboard view presenting circulation KPIs and embedded Matplotlib visual charts."""

    def __init__(self, parent, db: LibraryDatabase, on_change_callback: Callable[[], None]):
        super().__init__(parent, fg_color="transparent")
        self.db = db
        self.on_change_callback = on_change_callback

        self.fig_donut = None
        self.canvas_donut = None
        self.fig_bar = None
        self.canvas_bar = None

        self._create_widgets()
        self.refresh()

    def _create_widgets(self) -> None:
        # Header
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 14))

        ctk.CTkLabel(
            header_frame,
            text="📊 Visual Analytics & Circulation Intelligence",
            font=FONT_HEADING,
            anchor="w"
        ).pack(side="left")

        refresh_btn = ctk.CTkButton(
            header_frame,
            text="🔄 Refresh Metrics",
            font=FONT_BODY_BOLD,
            width=130,
            height=34,
            corner_radius=8,
            fg_color=("#E4E4E7", "#27272A"),
            text_color=("#18181B", "#F4F4F5"),
            hover_color=("#D4D4D8", "#3F3F46"),
            command=self.refresh
        )
        refresh_btn.pack(side="right")

        # -----------------------------
        # KPI Metric Cards Grid
        # -----------------------------
        cards_grid = ctk.CTkFrame(self, fg_color="transparent")
        cards_grid.pack(fill="x", pady=(0, 16))
        cards_grid.columnconfigure((0, 1, 2, 3), weight=1)

        self.kpi_cards = {}
        card_defs = [
            ("total_titles", "📚 Unique Titles", "0", COLOR_PRIMARY, 0, 0),
            ("total_copies", "📦 Total Copies", "0", "#0284C7", 0, 1),
            ("available_copies", "✅ Available Copies", "0", COLOR_SUCCESS, 0, 2),
            ("checked_out_copies", "🔄 Checked Out", "0", COLOR_WARNING, 0, 3),
            ("active_loans", "⚡ Active Loans", "0", "#6366F1", 1, 0),
            ("overdue_loans", "⚠️ Overdue Loans", "0", COLOR_DANGER, 1, 1),
            ("total_fines", "💰 Fines Assessed", "₹0.00", "#D97706", 1, 2),
            ("circulation_rate", "📈 Circulation Rate", "0%", "#4F46E5", 1, 3),
        ]

        for key, title, default_val, accent_color, r, c in card_defs:
            card = ctk.CTkFrame(cards_grid, corner_radius=12)
            card.grid(row=r, column=c, padx=5, pady=5, sticky="nsew")

            ctk.CTkLabel(card, text=title, font=FONT_SMALL, text_color=("gray40", "gray70")).pack(anchor="w", padx=14, pady=(12, 0))
            val_lbl = ctk.CTkLabel(card, text=default_val, font=("Segoe UI", 20, "bold"), text_color=accent_color)
            val_lbl.pack(anchor="w", padx=14, pady=(4, 12))
            self.kpi_cards[key] = val_lbl

        # -----------------------------
        # Charts Row (Embedded Matplotlib)
        # -----------------------------
        charts_row = ctk.CTkFrame(self, fg_color="transparent")
        charts_row.pack(fill="x", pady=(0, 16))
        charts_row.columnconfigure((0, 1), weight=1)

        # Donut Chart Card (Inventory Availability)
        self.donut_card = ctk.CTkFrame(charts_row, corner_radius=12)
        self.donut_card.grid(row=0, column=0, padx=(0, 8), sticky="nsew")
        ctk.CTkLabel(self.donut_card, text="🍩 Inventory Distribution", font=FONT_SUBTITLE).pack(anchor="w", padx=14, pady=(12, 4))
        self.donut_container = ctk.CTkFrame(self.donut_card, fg_color="transparent")
        self.donut_container.pack(fill="both", expand=True, padx=8, pady=(0, 12))

        # Bar Chart Card (Genre Distribution)
        self.bar_card = ctk.CTkFrame(charts_row, corner_radius=12)
        self.bar_card.grid(row=0, column=1, padx=(8, 0), sticky="nsew")
        ctk.CTkLabel(self.bar_card, text="📊 Top Genres in Catalog", font=FONT_SUBTITLE).pack(anchor="w", padx=14, pady=(12, 4))
        self.bar_container = ctk.CTkFrame(self.bar_card, fg_color="transparent")
        self.bar_container.pack(fill="both", expand=True, padx=8, pady=(0, 12))

        # -----------------------------
        # System Health & Details Card
        # -----------------------------
        info_card = ctk.CTkFrame(self, corner_radius=12)
        info_card.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(info_card, text="ℹ️ System Health & Data Integrity", font=FONT_SUBTITLE).pack(anchor="w", padx=16, pady=(14, 6))

        self.info_text_lbl = ctk.CTkLabel(
            info_card,
            text="Loading insights...",
            font=FONT_BODY,
            justify="left",
            anchor="w"
        )
        self.info_text_lbl.pack(fill="x", padx=16, pady=(0, 14))

    def refresh(self) -> None:
        """Update KPI cards, visual charts, and insights."""
        stats = self.db.get_statistics()

        # Update KPI figures
        self.kpi_cards["total_titles"].configure(text=str(stats['total_titles']))
        self.kpi_cards["total_copies"].configure(text=str(stats['total_copies']))
        self.kpi_cards["available_copies"].configure(text=str(stats['available_copies']))
        self.kpi_cards["checked_out_copies"].configure(text=str(stats['checked_out_copies']))
        self.kpi_cards["active_loans"].configure(text=str(stats['active_loans']))
        self.kpi_cards["overdue_loans"].configure(text=str(stats['overdue_loans']))
        self.kpi_cards["total_fines"].configure(text=f"₹{stats['total_fines']:.2f}")

        if stats['total_copies'] > 0:
            circ_pct = (stats['checked_out_copies'] / stats['total_copies']) * 100
            self.kpi_cards["circulation_rate"].configure(text=f"{circ_pct:.1f}%")
        else:
            self.kpi_cards["circulation_rate"].configure(text="0.0%")

        # Render Visual Matplotlib Charts
        self._render_charts(stats)

        # Health info
        active = stats['active_loans']
        overdue = stats['overdue_loans']
        overdue_rate = (overdue / active * 100) if active > 0 else 0.0

        insights = (
            f"• Persistent Storage: Microsoft Excel via OpenPyXL Engine\n"
            f"• Active File: {self.db.excel_file}\n"
            f"• Total Logged Transactions: {stats['total_transactions']} records\n"
            f"• Current Active Patron Loans: {active} books\n"
            f"• Overdue Delinquency Rate: {overdue_rate:.1f}%\n"
            f"• Session Status: {'⚠️ Unsaved Changes Pending' if self.db.is_dirty else '✅ Clean (Synced to Excel)'}\n"
            f"• Last Synced: {self.db.last_saved_time or 'Just now'}"
        )
        self.info_text_lbl.configure(text=insights)

    def _render_charts(self, stats) -> None:
        """Draw embedded Matplotlib charts styled for dark/light mode."""
        is_dark = ctk.get_appearance_mode() == "Dark"
        bg_color = "#1E293B" if is_dark else "#FFFFFF"
        text_color = "#E2E8F0" if is_dark else "#1E293B"

        # 1. Donut Chart (Availability)
        if self.canvas_donut:
            self.canvas_donut.get_tk_widget().destroy()
        if self.fig_donut:
            plt.close(self.fig_donut)

        self.fig_donut, ax_donut = plt.subplots(figsize=(4, 2.8), facecolor=bg_color)
        avail = max(0, stats['available_copies'])
        issued = max(0, stats['checked_out_copies'])

        if avail == 0 and issued == 0:
            avail, issued = 1, 0

        colors = ["#10B981", "#F59E0B"]  # Emerald & Amber
        labels = [f"Available ({avail})", f"Checked Out ({issued})"]
        wedges, texts, autotexts = ax_donut.pie(
            [avail, issued],
            labels=labels,
            autopct="%1.0f%%",
            startangle=90,
            colors=colors,
            wedgeprops=dict(width=0.45, edgecolor=bg_color, linewidth=2),
            textprops=dict(color=text_color, fontsize=9)
        )
        for at in autotexts:
            at.set_color("#FFFFFF")
            at.set_fontsize(9)
            at.set_weight("bold")

        ax_donut.set_facecolor(bg_color)
        plt.tight_layout()

        self.canvas_donut = FigureCanvasTkAgg(self.fig_donut, master=self.donut_container)
        self.canvas_donut.draw()
        self.canvas_donut.get_tk_widget().pack(fill="both", expand=True)

        # 2. Horizontal Bar Chart (Top Genres)
        if self.canvas_bar:
            self.canvas_bar.get_tk_widget().destroy()
        if self.fig_bar:
            plt.close(self.fig_bar)

        self.fig_bar, ax_bar = plt.subplots(figsize=(4.5, 2.8), facecolor=bg_color)
        genres = self.db.get_genre_distribution()[:6]  # Top 6
        if genres:
            genre_names = [g[0] for g in reversed(genres)]
            genre_counts = [g[1] for g in reversed(genres)]
        else:
            genre_names = ["None"]
            genre_counts = [0]

        bars = ax_bar.barh(genre_names, genre_counts, color="#3B82F6", height=0.6, edgecolor=bg_color)
        ax_bar.set_facecolor(bg_color)
        ax_bar.tick_params(colors=text_color, labelsize=9)
        for spine in ax_bar.spines.values():
            spine.set_visible(False)
        ax_bar.grid(axis="x", color="#475569" if is_dark else "#E2E8F0", linestyle="--", alpha=0.5)

        # Label counts at end of bars
        for bar in bars:
            w = bar.get_width()
            ax_bar.text(w + 0.1, bar.get_y() + bar.get_height() / 2, f"{int(w)}",
                        va="center", ha="left", color=text_color, fontsize=9, fontweight="bold")

        plt.tight_layout()

        self.canvas_bar = FigureCanvasTkAgg(self.fig_bar, master=self.bar_container)
        self.canvas_bar.draw()
        self.canvas_bar.get_tk_widget().pack(fill="both", expand=True)
