"""
Modern Root Application Controller built with CustomTkinter.
"""
import os
import subprocess
from tkinter import ttk, messagebox
import customtkinter as ctk

from ..database import LibraryDatabase
from .analytics_view import AnalyticsView
from .books_view import BooksView
from .history_view import HistoryView
from .patrons_view import PatronsView
from .styles import (
    COLOR_PRIMARY,
    COLOR_PRIMARY_HOVER,
    COLOR_SUCCESS,
    COLOR_SUCCESS_HOVER,
    COLOR_UNSAVED,
    COLOR_UNSAVED_HOVER,
    FONT_BODY,
    FONT_BODY_BOLD,
    FONT_HEADING,
    FONT_SECTION,
    FONT_SMALL,
    FONT_SUBTITLE,
    configure_treeview_theme,
)
from .transactions_view import TransactionsView


class LibraryApp:
    """Root Application controller managing CustomTkinter window, sidebar, and views."""

    def __init__(self, root: ctk.CTk, excel_path: str = None):
        self.root = root
        self.root.title("Library Management System Pro — Modern Edition")
        self.root.geometry("1360x860")
        self.root.minsize(1100, 700)

        # Default theme
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        # TTK Style for Treeviews
        self.ttk_style = ttk.Style(self.root)
        configure_treeview_theme(self.ttk_style, mode="Dark")

        # Initialize database
        self.db = LibraryDatabase(excel_path)

        # Build Layout
        self._build_layout()

        # Show default view
        self._select_view("books")

        # Handle close
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def _build_layout(self) -> None:
        self.root.grid_columnconfigure(0, weight=0, minsize=240)
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(0, weight=1)

        # -----------------------------
        # Left Sidebar Navigation
        # -----------------------------
        self.sidebar = ctk.CTkFrame(self.root, width=240, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(6, weight=1)

        # App Branding
        brand_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        brand_frame.grid(row=0, column=0, padx=20, pady=(24, 20), sticky="ew")

        ctk.CTkLabel(
            brand_frame,
            text="📚 LibraryOS",
            font=FONT_HEADING,
            anchor="w"
        ).pack(fill="x")

        ctk.CTkLabel(
            brand_frame,
            text="Management System Pro",
            font=FONT_SMALL,
            text_color=("gray40", "gray60"),
            anchor="w"
        ).pack(fill="x")

        # Navigation Buttons
        self.nav_btns = {}
        nav_items = [
            ("books", "📚  Books Catalog"),
            ("loans", "🔄  Circulation Desk"),
            ("history", "📜  Transaction History"),
            ("patrons", "👥  Members & Merit"),
            ("analytics", "📊  Visual Analytics"),
        ]

        for i, (key, label) in enumerate(nav_items, start=1):
            btn = ctk.CTkButton(
                self.sidebar,
                text=label,
                font=FONT_BODY_BOLD,
                anchor="w",
                height=42,
                corner_radius=8,
                fg_color="transparent",
                text_color=("#18181B", "#F4F4F5"),
                hover_color=("#E4E4E7", "#27272A"),
                command=lambda k=key: self._select_view(k)
            )
            btn.grid(row=i, column=0, padx=14, pady=4, sticky="ew")
            self.nav_btns[key] = btn

        # Spacer in row 6

        # Appearance & Theme Controls at bottom of sidebar
        settings_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        settings_frame.grid(row=7, column=0, padx=16, pady=16, sticky="ew")

        ctk.CTkLabel(settings_frame, text="Appearance Mode:", font=FONT_SMALL, text_color=("gray40", "gray70"), anchor="w").pack(fill="x", pady=(0, 4))
        self.appearance_menu = ctk.CTkOptionMenu(
            settings_frame,
            values=["Dark", "Light", "System"],
            height=30,
            corner_radius=6,
            command=self._change_appearance_mode
        )
        self.appearance_menu.set("Dark")
        self.appearance_menu.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(settings_frame, text="UI Scaling:", font=FONT_SMALL, text_color=("gray40", "gray70"), anchor="w").pack(fill="x", pady=(0, 4))
        self.scaling_menu = ctk.CTkOptionMenu(
            settings_frame,
            values=["80%", "90%", "100%", "110%", "120%"],
            height=30,
            corner_radius=6,
            command=self._change_scaling
        )
        self.scaling_menu.set("100%")
        self.scaling_menu.pack(fill="x")

        # -----------------------------
        # Main Area (Header + Content + Footer)
        # -----------------------------
        self.main_container = ctk.CTkFrame(self.root, fg_color="transparent")
        self.main_container.grid(row=0, column=1, sticky="nsew", padx=16, pady=12)
        self.main_container.columnconfigure(0, weight=1)
        self.main_container.rowconfigure(1, weight=1)

        # Top Action Header
        header = ctk.CTkFrame(self.main_container, corner_radius=12, height=54)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        header.pack_propagate(False)

        self.view_title_lbl = ctk.CTkLabel(header, text="📚 Books Catalog", font=FONT_SUBTITLE)
        self.view_title_lbl.pack(side="left", padx=16)

        # Header Buttons
        self.save_btn = ctk.CTkButton(
            header,
            text="💾 Save to Excel",
            font=FONT_BODY_BOLD,
            fg_color=COLOR_SUCCESS,
            hover_color=COLOR_SUCCESS_HOVER,
            width=130,
            height=34,
            corner_radius=8,
            command=self.save_to_excel
        )
        self.save_btn.pack(side="right", padx=(6, 14))

        open_folder_btn = ctk.CTkButton(
            header,
            text="📁 Data Folder",
            font=FONT_BODY,
            fg_color=("#F1F5F9", "#27272A"),
            text_color=("#0F172A", "#F8FAFC"),
            hover_color=("#E2E8F0", "#3F3F46"),
            width=110,
            height=34,
            corner_radius=8,
            command=self._open_data_folder
        )
        open_folder_btn.pack(side="right", padx=6)

        about_btn = ctk.CTkButton(
            header,
            text="ℹ️ About",
            font=FONT_BODY,
            fg_color=("#F1F5F9", "#27272A"),
            text_color=("#0F172A", "#F8FAFC"),
            hover_color=("#E2E8F0", "#3F3F46"),
            width=80,
            height=34,
            corner_radius=8,
            command=self._show_about
        )
        about_btn.pack(side="right", padx=6)

        # Content Area (Hosting views)
        self.content_area = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.content_area.grid(row=1, column=0, sticky="nsew")
        self.content_area.columnconfigure(0, weight=1)
        self.content_area.rowconfigure(0, weight=1)

        # Instantiate View Frames
        self.views = {
            "books": BooksView(
                self.content_area,
                self.db,
                on_change_callback=self.on_data_change,
                on_issue_callback=self._issue_book_from_catalog
            ),
            "loans": TransactionsView(
                self.content_area,
                self.db,
                on_change_callback=self.on_data_change,
                on_view_history=lambda: self._select_view("history")
            ),
            "history": HistoryView(
                self.content_area,
                self.db,
                on_change_callback=self.on_data_change
            ),
            "patrons": PatronsView(self.content_area, self.db, on_change_callback=self.on_data_change),
            "analytics": AnalyticsView(self.content_area, self.db, on_change_callback=self.on_data_change),
        }

        # Status Bar
        self.status_bar = ctk.CTkFrame(self.main_container, corner_radius=8, height=30)
        self.status_bar.grid(row=2, column=0, sticky="ew", pady=(8, 0))
        self.status_bar.pack_propagate(False)

        self.status_lbl = ctk.CTkLabel(
            self.status_bar,
            text="Ready | All changes synchronized with Excel.",
            font=FONT_SMALL,
            text_color=("gray40", "gray70")
        )
        self.status_lbl.pack(side="left", padx=12)

        self.db_path_lbl = ctk.CTkLabel(
            self.status_bar,
            text=f"Database: {os.path.basename(self.db.excel_file)}",
            font=FONT_SMALL,
            text_color=("gray40", "gray70")
        )
        self.db_path_lbl.pack(side="right", padx=12)

    def _issue_book_from_catalog(self, book_data: dict) -> None:
        """Switch to Circulation & Loans view and pre-fill selected book."""
        self._select_view("loans")
        self.views["loans"].set_selected_book(book_data)

    def _select_view(self, view_key: str) -> None:
        """Switch active view and update sidebar button styling."""
        for key, btn in self.nav_btns.items():
            if key == view_key:
                btn.configure(
                    fg_color=(COLOR_PRIMARY, COLOR_PRIMARY),
                    text_color="#FFFFFF"
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=("#18181B", "#F4F4F5")
                )

        # Title map
        titles = {
            "books": "📚 Books Catalog Management",
            "loans": "🔄 Circulation Desk & Active Loans",
            "history": "📜 Transaction History & Audit Trail",
            "patrons": "👥 Member Profiles & Merit Standing",
            "analytics": "📊 Visual Analytics & Intelligence",
        }
        self.view_title_lbl.configure(text=titles.get(view_key, "LibraryOS"))

        # Switch visible frame
        for key, view in self.views.items():
            if key == view_key:
                view.grid(row=0, column=0, sticky="nsew")
                view.refresh()
            else:
                view.grid_forget()

    def _change_appearance_mode(self, new_mode: str) -> None:
        ctk.set_appearance_mode(new_mode)
        # Update Treeview colors to match
        configure_treeview_theme(self.ttk_style, mode=ctk.get_appearance_mode())
        # Refresh current view
        for view in self.views.values():
            view.refresh()

    def _change_scaling(self, new_scaling: str) -> None:
        scale_val = int(new_scaling.replace("%", "")) / 100
        ctk.set_widget_scaling(scale_val)

    def on_data_change(self) -> None:
        """Triggered whenever any view modifies the data."""
        self.status_lbl.configure(
            text="⚠️ Unsaved session changes pending. Click 'Save to Excel' or exit to save.",
            text_color=("#D97706", "#FBBF24")
        )
        self.save_btn.configure(
            text="💾 Save to Excel ●",
            fg_color=COLOR_UNSAVED,
            hover_color=COLOR_UNSAVED_HOVER
        )

    def save_to_excel(self) -> None:
        """Persist memory DataFrames to the Excel storage."""
        try:
            self.db.save_data()
            self.status_lbl.configure(
                text=f"✅ Data saved successfully to Excel at {self.db.last_saved_time}.",
                text_color=("#059669", "#34D399")
            )
            self.save_btn.configure(
                text="💾 Save to Excel",
                fg_color=COLOR_SUCCESS,
                hover_color=COLOR_SUCCESS_HOVER
            )
            messagebox.showinfo("Saved", f"Excel database saved successfully!\n\nFile: {self.db.excel_file}")
        except Exception as e:
            messagebox.showerror("Save Failed", f"Could not write to Excel: {e}")

    def _open_data_folder(self) -> None:
        folder = os.path.dirname(self.db.excel_file)
        try:
            if os.name == "nt":
                os.startfile(folder)
            else:
                subprocess.Popen(["xdg-open", folder])
        except Exception as e:
            messagebox.showerror("Folder Error", str(e))

    def _show_about(self) -> None:
        msg = (
            "Library Management System Pro v2.5\n\n"
            "A modern desktop application built with Python, CustomTkinter,\n"
            "Pandas, OpenPyXL, and Matplotlib.\n\n"
            "Key Features:\n"
            "• Modern Fluent Design with Dark & Light Mode\n"
            "• ⭐ User Merit System (Initial 100 Merit, On-Time Rewards, Overdue Penalties)\n"
            "• 👥 Member Registration & Tier Limits (Gold/Silver/Bronze/Suspended)\n"
            "• 🔄 Loan Renewals (+7 Days) & Digital Circulation Receipts\n"
            "• 📊 Embedded Matplotlib charts (Donut & Bar charts)\n"
            "• 📖 Complete Catalog CRUD operations (Add, Edit, Delete)\n"
            "• 💰 Automatic Overdue Fine Calculation (₹5.00/day)\n"
            "• 💾 Safe Multi-Sheet Excel Storage (Books, Transactions, Patrons)"
        )
        messagebox.showinfo("About LibraryOS", msg)

    def on_close(self) -> None:
        """Safely handle application exit, prompting to save if dirty."""
        if self.db.is_dirty:
            resp = messagebox.askyesnocancel(
                "Unsaved Changes",
                "You have unsaved changes in this session.\n\n"
                "Would you like to save them to Excel before exiting?"
            )
            if resp is True:
                try:
                    self.db.save_data()
                except Exception as e:
                    messagebox.showerror("Save Error", f"Failed to save data: {e}")
                    return
                self.root.destroy()
            elif resp is False:
                self.root.destroy()
            else:
                return
        else:
            self.root.destroy()
