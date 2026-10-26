"""
Modern selection dialogs for choosing books and members in circulation workflows.
"""
import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional, Dict, Any
import customtkinter as ctk

from ..database import LibraryDatabase
from ..models import STATUS_AVAILABLE, get_merit_tier
from .styles import (
    COLOR_PRIMARY,
    COLOR_PRIMARY_HOVER,
    COLOR_SUCCESS,
    COLOR_SUCCESS_HOVER,
    FONT_BODY,
    FONT_BODY_BOLD,
    FONT_SECTION,
    FONT_SMALL,
    FONT_SUBTITLE,
    apply_treeview_row_tags,
)


class BookPickerDialog(ctk.CTkToplevel):
    """Modal dialog to search, browse, and pick an available book to issue."""

    def __init__(self, parent, db: LibraryDatabase, on_select: Callable[[Dict[str, Any]], None]):
        super().__init__(parent)
        self.db = db
        self.on_select = on_select
        self.selected_book_id: Optional[int] = None

        self.title("📚 Select Book from Catalog")
        self.geometry("820x540")
        self.minsize(700, 450)
        self.transient(parent)
        self.grab_set()

        self._create_widgets()
        self.refresh()

    def _create_widgets(self) -> None:
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=16, pady=16)

        # Header
        header = ctk.CTkFrame(container, fg_color="transparent")
        header.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(header, text="📚 Select a Book to Issue", font=FONT_SUBTITLE).pack(side="left")
        ctk.CTkLabel(
            header,
            text="Only books with available copies can be issued",
            font=FONT_SMALL,
            text_color=("gray40", "gray70")
        ).pack(side="right")

        # Search & Filter Row
        search_card = ctk.CTkFrame(container, corner_radius=10)
        search_card.pack(fill="x", pady=(0, 10))

        search_row = ctk.CTkFrame(search_card, fg_color="transparent")
        search_row.pack(fill="x", padx=12, pady=10)

        self.search_entry = ctk.CTkEntry(
            search_row,
            placeholder_text="🔍 Search by Title, Author, Genre, ISBN, or Book ID...",
            font=FONT_BODY,
            height=36,
            corner_radius=8
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.search_entry.bind("<KeyRelease>", lambda _: self.refresh())

        self.avail_only_var = ctk.BooleanVar(value=True)
        avail_cb = ctk.CTkCheckBox(
            search_row,
            text="Available Only",
            variable=self.avail_only_var,
            font=FONT_SMALL,
            command=self.refresh
        )
        avail_cb.pack(side="left")

        # Table Container
        table_card = ctk.CTkFrame(container, corner_radius=10)
        table_card.pack(fill="both", expand=True, pady=(0, 12))

        tree_scroll_y = ttk.Scrollbar(table_card, orient="vertical")
        tree_scroll_x = ttk.Scrollbar(table_card, orient="horizontal")

        columns = (
            ("BookID", "ID", 50, "center"),
            ("Title", "Title", 220, "w"),
            ("Author", "Author", 150, "w"),
            ("Genre", "Genre", 110, "w"),
            ("AvailableCopies", "Avail", 65, "center"),
            ("TotalCopies", "Total", 65, "center"),
            ("Status", "Status", 95, "center"),
        )

        self.tree = ttk.Treeview(
            table_card,
            columns=[c[0] for c in columns],
            show="headings",
            yscrollcommand=tree_scroll_y.set,
            xscrollcommand=tree_scroll_x.set,
            selectmode="browse"
        )

        tree_scroll_y.config(command=self.tree.yview)
        tree_scroll_x.config(command=self.tree.xview)

        tree_scroll_y.pack(side="right", fill="y", padx=(0, 4), pady=4)
        tree_scroll_x.pack(side="bottom", fill="x", padx=4, pady=(0, 4))
        self.tree.pack(side="left", fill="both", expand=True, padx=4, pady=4)

        for col_id, heading_text, width, align in columns:
            self.tree.heading(col_id, text=heading_text)
            self.tree.column(col_id, width=width, minwidth=35, anchor=align)

        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)
        self.tree.bind("<Double-1>", lambda _: self._on_confirm_select())

        # Action Buttons Footer
        footer = ctk.CTkFrame(container, fg_color="transparent")
        footer.pack(fill="x")

        self.selection_label = ctk.CTkLabel(
            footer,
            text="Click a book row to select it",
            font=FONT_BODY,
            text_color=("gray40", "gray70")
        )
        self.selection_label.pack(side="left")

        cancel_btn = ctk.CTkButton(
            footer,
            text="Cancel",
            font=FONT_BODY,
            fg_color=("#E4E4E7", "#3F3F46"),
            text_color=("#18181B", "#F4F4F5"),
            hover_color=("#D4D4D8", "#52525B"),
            width=90,
            height=36,
            corner_radius=8,
            command=self.destroy
        )
        cancel_btn.pack(side="right", padx=(8, 0))

        self.confirm_btn = ctk.CTkButton(
            footer,
            text="✅ Select This Book",
            font=FONT_BODY_BOLD,
            fg_color=COLOR_SUCCESS,
            hover_color=COLOR_SUCCESS_HOVER,
            width=160,
            height=36,
            corner_radius=8,
            state="disabled",
            command=self._on_confirm_select
        )
        self.confirm_btn.pack(side="right")

    def refresh(self) -> None:
        apply_treeview_row_tags(self.tree, "books", ctk.get_appearance_mode())

        for item in self.tree.get_children():
            self.tree.delete(item)

        filter_st = STATUS_AVAILABLE if self.avail_only_var.get() else None

        df = self.db.get_books(
            search_query=self.search_entry.get(),
            sort_by="Title",
            ascending=True,
            filter_status=filter_st
        )

        for _, row in df.iterrows():
            b_id = row['BookID']
            avail = row['AvailableCopies']
            tag = "unavailable" if avail == 0 else "evenrow"

            self.tree.insert(
                "",
                tk.END,
                iid=str(b_id),
                values=(
                    b_id,
                    row['Title'],
                    row['Author'],
                    row['Genre'],
                    avail,
                    row['TotalCopies'],
                    row['Status']
                ),
                tags=(tag,)
            )

    def _on_tree_select(self, event=None) -> None:
        selection = self.tree.selection()
        if not selection:
            self.selected_book_id = None
            self.confirm_btn.configure(state="disabled")
            self.selection_label.configure(text="Click a book row to select it")
            return

        b_id = int(selection[0])
        book = self.db.get_book_by_id(b_id)
        if not book:
            return

        avail = book['AvailableCopies']
        if avail <= 0:
            self.selected_book_id = None
            self.confirm_btn.configure(state="disabled")
            self.selection_label.configure(
                text=f"⚠️ '{book['Title']}' has 0 available copies (Checked Out)",
                text_color=COLOR_PRIMARY
            )
        else:
            self.selected_book_id = b_id
            self.confirm_btn.configure(state="normal")
            self.selection_label.configure(
                text=f"Selected: '{book['Title']}' ({avail} copies available)",
                text_color=COLOR_SUCCESS
            )

    def _on_confirm_select(self) -> None:
        if self.selected_book_id is None:
            return

        book = self.db.get_book_by_id(self.selected_book_id)
        if book and book['AvailableCopies'] > 0:
            self.on_select(book)
            self.destroy()


class MemberPickerDialog(ctk.CTkToplevel):
    """Modal dialog to search, browse, and pick a registered member."""

    def __init__(self, parent, db: LibraryDatabase, on_select: Callable[[Dict[str, Any]], None]):
        super().__init__(parent)
        self.db = db
        self.on_select = on_select
        self.selected_patron_id: Optional[int] = None

        self.title("👤 Select Registered Member")
        self.geometry("820x520")
        self.minsize(700, 450)
        self.transient(parent)
        self.grab_set()

        self._create_widgets()
        self.refresh()

    def _create_widgets(self) -> None:
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=16, pady=16)

        header = ctk.CTkFrame(container, fg_color="transparent")
        header.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(header, text="👤 Select Patron for Book Loan", font=FONT_SUBTITLE).pack(side="left")

        search_card = ctk.CTkFrame(container, corner_radius=10)
        search_card.pack(fill="x", pady=(0, 10))

        search_row = ctk.CTkFrame(search_card, fg_color="transparent")
        search_row.pack(fill="x", padx=12, pady=10)

        self.search_entry = ctk.CTkEntry(
            search_row,
            placeholder_text="🔍 Search member by Name, Email, Phone, or ID...",
            font=FONT_BODY,
            height=36,
            corner_radius=8
        )
        self.search_entry.pack(side="left", fill="x", expand=True)
        self.search_entry.bind("<KeyRelease>", lambda _: self.refresh())

        table_card = ctk.CTkFrame(container, corner_radius=10)
        table_card.pack(fill="both", expand=True, pady=(0, 12))

        tree_scroll_y = ttk.Scrollbar(table_card, orient="vertical")
        tree_scroll_x = ttk.Scrollbar(table_card, orient="horizontal")

        columns = (
            ("MemberID", "Member ID", 85, "center"),
            ("Name", "Name", 160, "w"),
            ("Email", "Email", 175, "w"),
            ("Type", "Type", 95, "center"),
            ("Merit", "Merit", 65, "center"),
            ("Tier", "Merit Standing", 125, "w"),
            ("ActiveLoans", "Loans", 55, "center"),
            ("Status", "Status", 75, "center"),
        )

        self.tree = ttk.Treeview(
            table_card,
            columns=[c[0] for c in columns],
            show="headings",
            yscrollcommand=tree_scroll_y.set,
            xscrollcommand=tree_scroll_x.set,
            selectmode="browse"
        )

        tree_scroll_y.config(command=self.tree.yview)
        tree_scroll_x.config(command=self.tree.xview)

        tree_scroll_y.pack(side="right", fill="y", padx=(0, 4), pady=4)
        tree_scroll_x.pack(side="bottom", fill="x", padx=4, pady=(0, 4))
        self.tree.pack(side="left", fill="both", expand=True, padx=4, pady=4)

        for col_id, heading_text, width, align in columns:
            self.tree.heading(col_id, text=heading_text)
            self.tree.column(col_id, width=width, minwidth=35, anchor=align)

        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)
        self.tree.bind("<Double-1>", lambda _: self._on_confirm_select())

        footer = ctk.CTkFrame(container, fg_color="transparent")
        footer.pack(fill="x")

        self.selection_label = ctk.CTkLabel(
            footer,
            text="Select a member from the directory",
            font=FONT_BODY,
            text_color=("gray40", "gray70")
        )
        self.selection_label.pack(side="left")

        cancel_btn = ctk.CTkButton(
            footer,
            text="Cancel",
            font=FONT_BODY,
            fg_color=("#E4E4E7", "#3F3F46"),
            text_color=("#18181B", "#F4F4F5"),
            hover_color=("#D4D4D8", "#52525B"),
            width=90,
            height=36,
            corner_radius=8,
            command=self.destroy
        )
        cancel_btn.pack(side="right", padx=(8, 0))

        self.confirm_btn = ctk.CTkButton(
            footer,
            text="✅ Select Member",
            font=FONT_BODY_BOLD,
            fg_color=COLOR_SUCCESS,
            hover_color=COLOR_SUCCESS_HOVER,
            width=150,
            height=36,
            corner_radius=8,
            state="disabled",
            command=self._on_confirm_select
        )
        self.confirm_btn.pack(side="right")

    def refresh(self) -> None:
        apply_treeview_row_tags(self.tree, "books", ctk.get_appearance_mode())

        for item in self.tree.get_children():
            self.tree.delete(item)

        df = self.db.get_patrons(search_query=self.search_entry.get(), sort_by="MeritScore", ascending=False)

        for _, row in df.iterrows():
            p_id = row['PatronID']
            m_id = str(row.get('MemberID', f"MEM-{1000 + int(p_id)}"))
            merit = int(row['MeritScore'])
            tier = get_merit_tier(merit)

            self.tree.insert(
                "",
                tk.END,
                iid=str(p_id),
                values=(
                    m_id,
                    row['Name'],
                    row['Email'],
                    row['MembershipType'],
                    merit,
                    tier['badge'],
                    row['CurrentLoans'],
                    row['Status']
                ),
                tags=("evenrow",)
            )

    def _on_tree_select(self, event=None) -> None:
        selection = self.tree.selection()
        if not selection:
            self.selected_patron_id = None
            self.confirm_btn.configure(state="disabled")
            self.selection_label.configure(text="Select a member from the directory")
            return

        p_id = int(selection[0])
        patron = self.db.get_patron_by_id(p_id)
        if not patron:
            return

        m_id = str(patron.get('MemberID', f"MEM-{1000 + p_id}"))
        merit = patron['MeritScore']
        tier = get_merit_tier(merit)

        if not tier['can_borrow']:
            self.selected_patron_id = None
            self.confirm_btn.configure(state="disabled")
            self.selection_label.configure(
                text=f"🚫 [{m_id}] {patron['Name']} is Suspended ({merit} pts) - Cannot borrow",
                text_color=COLOR_PRIMARY
            )
        else:
            self.selected_patron_id = p_id
            self.confirm_btn.configure(state="normal")
            self.selection_label.configure(
                text=f"Selected: [{m_id}] {patron['Name']} • Merit: {merit} ({tier['badge']})",
                text_color=COLOR_SUCCESS
            )

    def _on_confirm_select(self) -> None:
        if self.selected_patron_id is None:
            return

        patron = self.db.get_patron_by_id(self.selected_patron_id)
        if patron:
            self.on_select(patron)
            self.destroy()


class TransactionReceiptDialog(ctk.CTkToplevel):
    """Modal dialog displaying a digital circulation receipt or audit slip."""

    def __init__(self, parent, receipt_text: str, title: str = "🧾 Digital Circulation Receipt"):
        super().__init__(parent)
        self.receipt_text = receipt_text
        self.title(title)
        self.geometry("480x520")
        self.minsize(420, 380)
        self.transient(parent)
        self.grab_set()

        self._create_widgets()

    def _create_widgets(self) -> None:
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=16, pady=(16, 8))

        ctk.CTkLabel(header, text="🧾 Circulation Audit Slip", font=FONT_SUBTITLE).pack(side="left")

        # Monospace Text Box
        self.txt = ctk.CTkTextbox(
            self,
            font=("Consolas", 11),
            corner_radius=8,
            fg_color=("#F8FAFC", "#18181B")
        )
        self.txt.pack(fill="both", expand=True, padx=16, pady=(0, 12))
        self.txt.insert("1.0", self.receipt_text)
        self.txt.configure(state="disabled")

        # Buttons Row
        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(fill="x", padx=16, pady=(0, 16))

        copy_btn = ctk.CTkButton(
            btn_row,
            text="📋 Copy Text",
            font=FONT_BODY,
            width=110,
            height=32,
            fg_color=("#E2E8F0", "#27272A"),
            text_color=("#0F172A", "#F8FAFC"),
            hover_color=("#CBD5E1", "#3F3F46"),
            command=self._copy_to_clipboard
        )
        copy_btn.pack(side="left")

        self.copied_lbl = ctk.CTkLabel(btn_row, text="", font=FONT_SMALL, text_color=COLOR_SUCCESS)
        self.copied_lbl.pack(side="left", padx=8)

        close_btn = ctk.CTkButton(
            btn_row,
            text="Close",
            font=FONT_BODY_BOLD,
            width=90,
            height=32,
            fg_color=COLOR_PRIMARY,
            hover_color=COLOR_PRIMARY_HOVER,
            command=self.destroy
        )
        close_btn.pack(side="right")

    def _copy_to_clipboard(self) -> None:
        self.clipboard_clear()
        self.clipboard_append(self.receipt_text)
        self.copied_lbl.configure(text="✅ Copied to clipboard!")
        self.after(2000, lambda: self.copied_lbl.configure(text=""))

