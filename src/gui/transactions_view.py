"""
Modern Circulation & Loans View built with CustomTkinter.
Features full Merit System integration, interactive book & member pickers, live due date calculation,
active loans desk, quick return/renew workflows, and digital circulation receipts.
"""
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Callable, Optional, Dict, Any
import customtkinter as ctk
import pandas as pd

from ..database import LibraryDatabase
from ..models import (
    DEFAULT_FINE_PER_DAY,
    DEFAULT_LOAN_DAYS,
    INITIAL_MERIT_SCORE,
    STATUS_AVAILABLE,
    TRANS_STATUS_ISSUED,
    TRANS_STATUS_RETURNED,
    get_merit_tier,
)
from .dialogs import BookPickerDialog, MemberPickerDialog, TransactionReceiptDialog
from .styles import (
    COLOR_DANGER,
    COLOR_PRIMARY,
    COLOR_PRIMARY_HOVER,
    COLOR_SUCCESS,
    COLOR_SUCCESS_HOVER,
    FONT_BODY,
    FONT_BODY_BOLD,
    FONT_HEADING,
    FONT_MONO,
    FONT_SECTION,
    FONT_SMALL,
    FONT_SUBTITLE,
    apply_treeview_row_tags,
)


class TransactionsView(ctk.CTkFrame):
    """Modern high-productivity circulation desk for issuing loans, returns, and renewals."""

    def __init__(
        self,
        parent,
        db: LibraryDatabase,
        on_change_callback: Callable[[], None],
        on_view_history: Optional[Callable[[], None]] = None
    ):
        super().__init__(parent, fg_color="transparent")
        self.db = db
        self.on_change_callback = on_change_callback
        self.on_view_history = on_view_history

        self.selected_trans_id: Optional[int] = None
        self.selected_book: Optional[Dict[str, Any]] = None
        self.selected_member_id: Optional[str] = None
        self.last_receipt: Optional[str] = None

        self._create_widgets()
        self.refresh()

    def _create_widgets(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # -----------------------------
        # 1. Top Quick Metric & Jump Bar
        # -----------------------------
        top_bar = ctk.CTkFrame(self, corner_radius=10, height=44)
        top_bar.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        top_bar.pack_propagate(False)

        # Quick Stat Badges
        stats_frame = ctk.CTkFrame(top_bar, fg_color="transparent")
        stats_frame.pack(side="left", fill="y", padx=12)

        self.active_stat_badge = ctk.CTkLabel(
            stats_frame,
            text="⚡ Active Loans: 0",
            font=FONT_BODY_BOLD,
            text_color=("#2563EB", "#60A5FA")
        )
        self.active_stat_badge.pack(side="left", padx=(0, 16))

        self.overdue_stat_badge = ctk.CTkLabel(
            stats_frame,
            text="⚠️ Overdue: 0",
            font=FONT_BODY_BOLD,
            text_color=("#DC2626", "#F87171")
        )
        self.overdue_stat_badge.pack(side="left", padx=(0, 16))

        self.avail_stat_badge = ctk.CTkLabel(
            stats_frame,
            text="📚 Catalog Available: 0 copies",
            font=FONT_SMALL,
            text_color=("gray40", "gray70")
        )
        self.avail_stat_badge.pack(side="left")

        # Jump to Full History Tab Button
        if self.on_view_history:
            history_jump_btn = ctk.CTkButton(
                top_bar,
                text="📜 Full Transaction History & Audit Log ➔",
                font=FONT_SMALL,
                fg_color=("#EEF2FF", "#1E1B4B"),
                text_color=("#4338CA", "#A5B4FC"),
                hover_color=("#E0E7FF", "#312E81"),
                height=30,
                corner_radius=6,
                command=self.on_view_history
            )
            history_jump_btn.pack(side="right", padx=10)

        # -----------------------------
        # 2. Main Workspace Split (Left: Issue Desk, Right: Active Loans Desk)
        # -----------------------------
        workspace = ctk.CTkFrame(self, fg_color="transparent")
        workspace.grid(row=1, column=0, sticky="nsew")
        workspace.columnconfigure(0, weight=0, minsize=400)
        workspace.columnconfigure(1, weight=1)
        workspace.rowconfigure(0, weight=1)

        # ==========================================
        # LEFT PANEL: 📤 Issue Book Desk
        # ==========================================
        issue_card = ctk.CTkFrame(workspace, corner_radius=12)
        issue_card.grid(row=0, column=0, sticky="nsew", padx=(0, 12))

        # Title
        issue_header = ctk.CTkFrame(issue_card, fg_color="transparent")
        issue_header.pack(fill="x", padx=16, pady=(14, 8))

        ctk.CTkLabel(issue_header, text="📤 Issue Book to Patron", font=FONT_SUBTITLE).pack(side="left")
        ctk.CTkLabel(issue_header, text="Fast Checkout", font=FONT_SMALL, text_color=("gray40", "gray70")).pack(side="right")

        # --- Section 1: Book Selection ---
        book_sec_hdr = ctk.CTkFrame(issue_card, fg_color="transparent")
        book_sec_hdr.pack(fill="x", padx=16, pady=(4, 4))
        ctk.CTkLabel(book_sec_hdr, text="1. Select Book *", font=FONT_BODY_BOLD).pack(side="left")

        choose_book_btn = ctk.CTkButton(
            book_sec_hdr,
            text="📚 Browse Catalog...",
            font=FONT_SMALL,
            width=130,
            height=28,
            corner_radius=6,
            fg_color=COLOR_PRIMARY,
            hover_color=COLOR_PRIMARY_HOVER,
            command=self._open_book_picker
        )
        choose_book_btn.pack(side="right")

        # Book Preview Frame
        self.book_card_frame = ctk.CTkFrame(issue_card, corner_radius=8, fg_color=("#F1F5F9", "#1E293B"))
        self.book_card_frame.pack(fill="x", padx=16, pady=(0, 10))

        self.book_title_lbl = ctk.CTkLabel(
            self.book_card_frame,
            text="No book selected",
            font=FONT_BODY_BOLD,
            anchor="w",
            text_color=("gray40", "gray70")
        )
        self.book_title_lbl.pack(fill="x", padx=12, pady=(8, 2))

        self.book_desc_lbl = ctk.CTkLabel(
            self.book_card_frame,
            text="Click 'Browse Catalog...' above to choose an available copy",
            font=FONT_SMALL,
            anchor="w",
            text_color=("gray50", "gray60")
        )
        self.book_desc_lbl.pack(fill="x", padx=12, pady=(0, 8))

        # --- Section 2: Patron & Merit Verification ---
        patron_sec_hdr = ctk.CTkFrame(issue_card, fg_color="transparent")
        patron_sec_hdr.pack(fill="x", padx=16, pady=(4, 4))
        ctk.CTkLabel(patron_sec_hdr, text="2. Customer / Member *", font=FONT_BODY_BOLD).pack(side="left")

        pick_member_btn = ctk.CTkButton(
            patron_sec_hdr,
            text="👤 Pick Member...",
            font=FONT_SMALL,
            width=130,
            height=28,
            corner_radius=6,
            fg_color=("#4F46E5", "#4338CA"),
            hover_color=("#4338CA", "#3730A3"),
            command=self._open_member_picker
        )
        pick_member_btn.pack(side="right")

        self.cust_name_entry = ctk.CTkEntry(
            issue_card,
            placeholder_text="Enter customer name or pick member above...",
            height=34,
            corner_radius=8,
            font=FONT_BODY
        )
        self.cust_name_entry.pack(fill="x", padx=16, pady=(0, 4))
        self.cust_name_entry.bind("<KeyRelease>", lambda _: self._preview_patron_merit())

        # Patron Merit & Borrowing Limits Badge
        self.patron_merit_badge = ctk.CTkLabel(
            issue_card,
            text="Select member to verify Merit Standing & borrowing quota",
            font=FONT_SMALL,
            fg_color=("#F1F5F9", "#27272A"),
            text_color=("gray40", "gray70"),
            corner_radius=6,
            height=28
        )
        self.patron_merit_badge.pack(fill="x", padx=16, pady=(0, 6))

        # Patron Email (Optional/Auto-filled)
        ctk.CTkLabel(issue_card, text="Customer Email", font=FONT_SMALL, text_color=("gray40", "gray70"), anchor="w").pack(fill="x", padx=16, pady=(2, 2))
        self.cust_email_entry = ctk.CTkEntry(
            issue_card,
            placeholder_text="name@example.com",
            height=32,
            corner_radius=8,
            font=FONT_BODY
        )
        self.cust_email_entry.pack(fill="x", padx=16, pady=(0, 10))

        # --- Section 3: Loan Duration & Live Due Date ---
        ctk.CTkLabel(issue_card, text="3. Loan Duration & Scheduled Due Date", font=FONT_BODY_BOLD, anchor="w").pack(fill="x", padx=16, pady=(2, 2))

        duration_row = ctk.CTkFrame(issue_card, fg_color="transparent")
        duration_row.pack(fill="x", padx=16, pady=(0, 6))

        self.loan_days_cb = ctk.CTkOptionMenu(
            duration_row,
            values=["7 days", "14 days (Standard)", "21 days", "30 days"],
            height=34,
            corner_radius=8,
            font=FONT_BODY,
            command=lambda _: self._update_due_date_preview()
        )
        self.loan_days_cb.set("14 days (Standard)")
        self.loan_days_cb.pack(side="left", fill="x", expand=True, padx=(0, 8))

        # Live Due Date Display Box
        self.due_date_badge = ctk.CTkLabel(
            issue_card,
            text="📅 Scheduled Due: Calculating...",
            font=FONT_BODY_BOLD,
            fg_color=("#EFF6FF", "#1E293B"),
            text_color=("#2563EB", "#93C5FD"),
            corner_radius=6,
            height=32
        )
        self.due_date_badge.pack(fill="x", padx=16, pady=(0, 14))
        self._update_due_date_preview()

        # Action Buttons Row
        action_row = ctk.CTkFrame(issue_card, fg_color="transparent")
        action_row.pack(fill="x", padx=16, pady=(0, 16))
        action_row.columnconfigure(0, weight=3)
        action_row.columnconfigure(1, weight=1)

        self.issue_btn = ctk.CTkButton(
            action_row,
            text="🚀 Confirm & Issue Loan",
            font=FONT_BODY_BOLD,
            fg_color=COLOR_PRIMARY,
            hover_color=COLOR_PRIMARY_HOVER,
            height=38,
            corner_radius=8,
            command=self._on_issue_book
        )
        self.issue_btn.grid(row=0, column=0, sticky="ew", padx=(0, 6))

        clear_btn = ctk.CTkButton(
            action_row,
            text="🔄 Reset",
            font=FONT_BODY,
            fg_color=("#E2E8F0", "#27272A"),
            text_color=("#0F172A", "#F8FAFC"),
            hover_color=("#CBD5E1", "#3F3F46"),
            height=38,
            corner_radius=8,
            command=self._reset_issue_form
        )
        clear_btn.grid(row=0, column=1, sticky="ew")

        # ==========================================
        # RIGHT PANEL: 📥 Active Loans & Returns Desk
        # ==========================================
        right_panel = ctk.CTkFrame(workspace, fg_color="transparent")
        right_panel.grid(row=0, column=1, sticky="nsew")
        right_panel.columnconfigure(0, weight=1)
        right_panel.rowconfigure(1, weight=1)

        # Filters Card
        filter_card = ctk.CTkFrame(right_panel, corner_radius=12)
        filter_card.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        search_row = ctk.CTkFrame(filter_card, fg_color="transparent")
        search_row.pack(fill="x", padx=14, pady=12)

        self.search_entry = ctk.CTkEntry(
            search_row,
            placeholder_text="🔍 Search active loans by member ID, customer name, book, or Trans ID...",
            font=FONT_BODY,
            height=36,
            corner_radius=8
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.search_entry.bind("<KeyRelease>", lambda _: self.refresh())

        self.status_segment = ctk.CTkSegmentedButton(
            search_row,
            values=["All Active", "⚠️ Overdue Only", "🟢 Due Soon (≤3d)"],
            height=34,
            corner_radius=8,
            command=lambda _: self.refresh()
        )
        self.status_segment.set("All Active")
        self.status_segment.pack(side="left", padx=(0, 8))

        refresh_btn = ctk.CTkButton(
            search_row,
            text="🔄 Refresh",
            font=FONT_BODY,
            fg_color=("#F1F5F9", "#27272A"),
            text_color=("#0F172A", "#F8FAFC"),
            hover_color=("#E2E8F0", "#3F3F46"),
            width=80,
            height=34,
            corner_radius=8,
            command=self.refresh
        )
        refresh_btn.pack(side="right")

        # Table Container
        table_container = ctk.CTkFrame(right_panel, corner_radius=12)
        table_container.grid(row=1, column=0, sticky="nsew")
        table_container.rowconfigure(0, weight=1)
        table_container.columnconfigure(0, weight=1)

        tree_scroll_y = ttk.Scrollbar(table_container, orient="vertical")
        tree_scroll_x = ttk.Scrollbar(table_container, orient="horizontal")

        columns = (
            ("TransID", "Trans ID", 65, "center"),
            ("BookTitle", "Book Title", 180, "w"),
            ("MemberID", "Member ID", 80, "center"),
            ("CustomerName", "Customer", 130, "w"),
            ("IssueDate", "Issued", 85, "center"),
            ("DueDate", "Due Date", 85, "center"),
            ("Status", "Status / Days", 110, "center"),
            ("FineAmount", "Accrued Fine", 80, "e"),
        )

        self.tree = ttk.Treeview(
            table_container,
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
            self.tree.column(col_id, width=width, minwidth=40, anchor=align)

        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)
        self.tree.bind("<Double-1>", lambda _: self._on_return_selected())

        # Action & Return Desk Card (Bottom of Right Panel)
        return_card = ctk.CTkFrame(right_panel, corner_radius=12)
        return_card.grid(row=2, column=0, sticky="ew", pady=(10, 0))

        # Dynamic Status Banner
        self.return_info_badge = ctk.CTkLabel(
            return_card,
            text="💡 Select an active loan from the table above to process return, renew, or view circulation receipt.",
            font=FONT_SMALL,
            fg_color=("#EFF6FF", "#1E293B"),
            text_color=("#1D4ED8", "#93C5FD"),
            corner_radius=8,
            anchor="w",
            padx=12,
            pady=8
        )
        self.return_info_badge.pack(fill="x", padx=14, pady=(12, 10))

        # Return Actions Row
        action_desk_row = ctk.CTkFrame(return_card, fg_color="transparent")
        action_desk_row.pack(fill="x", padx=14, pady=(0, 12))

        # Fine Rate Config
        rate_box = ctk.CTkFrame(action_desk_row, fg_color="transparent")
        rate_box.pack(side="left", padx=(0, 14))

        ctk.CTkLabel(rate_box, text="Fine rate: ₹", font=FONT_SMALL, text_color=("gray40", "gray70")).pack(side="left")
        self.fine_rate_entry = ctk.CTkEntry(rate_box, width=54, height=32, corner_radius=6, font=FONT_SMALL)
        self.fine_rate_entry.insert(0, str(DEFAULT_FINE_PER_DAY))
        self.fine_rate_entry.pack(side="left", padx=4)
        ctk.CTkLabel(rate_box, text="/day overdue", font=FONT_SMALL, text_color=("gray40", "gray70")).pack(side="left")

        # Action Buttons
        self.receipt_btn = ctk.CTkButton(
            action_desk_row,
            text="🧾 View Last Slip",
            font=FONT_BODY,
            fg_color=("#F1F5F9", "#27272A"),
            text_color=("#0F172A", "#F8FAFC"),
            hover_color=("#E2E8F0", "#3F3F46"),
            height=34,
            corner_radius=8,
            state="disabled",
            command=self._show_last_receipt
        )
        self.receipt_btn.pack(side="right", padx=(6, 0))

        self.renew_btn = ctk.CTkButton(
            action_desk_row,
            text="🔄 Renew (+7d)",
            font=FONT_BODY_BOLD,
            fg_color=("#6366F1", "#4F46E5"),
            hover_color=("#4F46E5", "#4338CA"),
            width=120,
            height=34,
            corner_radius=8,
            state="disabled",
            command=self._on_renew_selected
        )
        self.renew_btn.pack(side="right", padx=6)

        self.return_btn = ctk.CTkButton(
            action_desk_row,
            text="✅ Return Book",
            font=FONT_BODY_BOLD,
            fg_color=COLOR_SUCCESS,
            hover_color=COLOR_SUCCESS_HOVER,
            width=130,
            height=34,
            corner_radius=8,
            state="disabled",
            command=self._on_return_selected
        )
        self.return_btn.pack(side="right", padx=6)

    def _update_due_date_preview(self) -> None:
        """Calculate and show the prospective due date based on duration selection."""
        dur_text = self.loan_days_cb.get()
        days = int(dur_text.split()[0]) if dur_text.split()[0].isdigit() else DEFAULT_LOAN_DAYS
        target_dt = datetime.now() + pd.Timedelta(days=days)
        formatted_dt = target_dt.strftime("%d %b %Y (%A)")
        self.due_date_badge.configure(
            text=f"📅 Return Due Date: {formatted_dt} ({days} days)"
        )

    def _open_book_picker(self) -> None:
        """Open the interactive Book Selection modal dialog."""
        BookPickerDialog(self, self.db, on_select=self.set_selected_book)

    def _open_member_picker(self) -> None:
        """Open the interactive Member Selection modal dialog."""
        MemberPickerDialog(self, self.db, on_select=self._on_member_selected)

    def set_selected_book(self, book_data: Any) -> None:
        """Set the book to issue from dialog, catalog, or BookID."""
        if isinstance(book_data, int):
            book = self.db.get_book_by_id(book_data)
        elif isinstance(book_data, dict):
            book = book_data
        else:
            return

        if not book:
            return

        avail = int(book.get('AvailableCopies', 0))
        total = int(book.get('TotalCopies', 1))
        self.selected_book = book

        self.book_title_lbl.configure(
            text=f"📚 {book['Title']} (ID #{book['BookID']})",
            font=("Segoe UI", 12, "bold"),
            text_color=("#18181B", "#F4F4F5")
        )

        if avail > 0:
            status_text = f"✅ {avail} of {total} copies available in catalog"
            self.book_card_frame.configure(fg_color=("#ECFDF5", "#064E3B"))
        else:
            status_text = f"❌ 0 of {total} copies available (All Checked Out)"
            self.book_card_frame.configure(fg_color=("#FEF3C7", "#78350F"))

        desc = f"Author: {book.get('Author', 'Unknown')} • Genre: {book.get('Genre', 'General')}\n{status_text}"
        self.book_desc_lbl.configure(text=desc)

    def _on_member_selected(self, patron: Dict[str, Any]) -> None:
        """Handle member chosen from MemberPickerDialog."""
        self.selected_member_id = patron.get('MemberID')
        self.cust_name_entry.delete(0, tk.END)
        self.cust_name_entry.insert(0, patron['Name'])

        self.cust_email_entry.delete(0, tk.END)
        self.cust_email_entry.insert(0, patron['Email'])

        self._preview_patron_merit()

    def _preview_patron_merit(self) -> None:
        name = self.cust_name_entry.get().strip()
        if not name:
            self.selected_member_id = None
            self.patron_merit_badge.configure(
                text="Select member to verify Merit Standing & borrowing quota",
                fg_color=("#F1F5F9", "#27272A"),
                text_color=("gray40", "gray70")
            )
            return

        patron = None
        if self.selected_member_id:
            patron = self.db.get_patron_by_member_id(self.selected_member_id)

        if not patron and name.upper().startswith("MEM-"):
            patron = self.db.get_patron_by_member_id(name)

        if not patron:
            patron = self.db.get_patron_by_name(name)

        if not patron:
            self.selected_member_id = None
            next_m = self.db.get_next_member_id()
            self.patron_merit_badge.configure(
                text=f"✨ New Member ({next_m}): Will receive 100 Initial Merit",
                fg_color=("#EFF6FF", "#1E3A8A"),
                text_color=("#2563EB", "#93C5FD")
            )
            return

        self.selected_member_id = patron.get('MemberID')
        m_id = self.selected_member_id
        merit = patron['MeritScore']
        tier = get_merit_tier(merit)
        active = patron['CurrentLoans']
        max_b = tier['max_books']

        if not tier['can_borrow']:
            self.patron_merit_badge.configure(
                text=f"🚫 [{m_id}] Suspended ({merit} pts): Borrowing blocked",
                fg_color=("#FEE2E2", "#7F1D1D"),
                text_color=("#B91C1C", "#FCA5A5")
            )
        elif active >= max_b:
            self.patron_merit_badge.configure(
                text=f"⚠️ [{m_id}] Limit Reached: {active}/{max_b} loans ({tier['badge']})",
                fg_color=("#FEF3C7", "#78350F"),
                text_color=("#B45309", "#FDE68A")
            )
        else:
            self.patron_merit_badge.configure(
                text=f"⭐ [{m_id}] {patron['Name']} • Merit: {merit} ({tier['badge']}) • Loans: {active}/{max_b}",
                fg_color=("#ECFDF5", "#064E3B"),
                text_color=("#047857", "#6EE7B7")
            )

    def _reset_issue_form(self) -> None:
        """Reset the issue form back to pristine empty state."""
        self.selected_book = None
        self.selected_member_id = None
        self.book_title_lbl.configure(text="No book selected", text_color=("gray40", "gray70"))
        self.book_desc_lbl.configure(text="Click 'Browse Catalog...' above to choose an available copy")
        self.book_card_frame.configure(fg_color=("#F1F5F9", "#1E293B"))

        self.cust_name_entry.delete(0, tk.END)
        self.cust_email_entry.delete(0, tk.END)
        self._preview_patron_merit()
        self._update_due_date_preview()

    def refresh(self) -> None:
        """Reload active loans from database and update quick stat badges."""
        apply_treeview_row_tags(self.tree, "loans", ctk.get_appearance_mode())

        for item in self.tree.get_children():
            self.tree.delete(item)

        # Update Top Bar Metric Counters
        all_trans = self.db.transactions_df
        today_str = datetime.now().strftime("%Y-%m-%d")

        active_count = 0
        overdue_count = 0
        if not all_trans.empty:
            active_mask = (all_trans['Status'] == TRANS_STATUS_ISSUED)
            active_count = len(all_trans[active_mask])
            overdue_mask = active_mask & (all_trans['DueDate'] < today_str)
            overdue_count = len(all_trans[overdue_mask])

        total_avail_copies = int(self.db.books_df['AvailableCopies'].sum()) if not self.db.books_df.empty else 0

        self.active_stat_badge.configure(text=f"⚡ Active Loans: {active_count}")
        self.overdue_stat_badge.configure(text=f"⚠️ Overdue: {overdue_count}")
        self.avail_stat_badge.configure(text=f"📚 Catalog Available: {total_avail_copies} copies")

        # Load Active Loans for table
        search_query = self.search_entry.get().strip()
        df = self.db.get_transactions(filter_status="Active", search_query=search_query)

        filter_mode = self.status_segment.get()
        today_dt = datetime.now().date()

        for _, row in df.iterrows():
            t_id = row['TransactionID']
            due_date = str(row['DueDate'])
            m_id = str(row.get('MemberID', ''))

            # Calculate days relative to today
            try:
                due_dt = pd.to_datetime(due_date).date()
                diff_days = (due_dt - today_dt).days
            except Exception:
                diff_days = 0

            is_overdue = (due_date < today_str)

            # Filtering
            if filter_mode == "⚠️ Overdue Only" and not is_overdue:
                continue
            elif filter_mode == "🟢 Due Soon (≤3d)" and (diff_days < 0 or diff_days > 3):
                continue

            # Tagging and display text
            if is_overdue:
                overdue_days = self.db.calculate_overdue_days(due_date)
                display_status = f"⚠️ {overdue_days}d Overdue"
                tag = "active_overdue"
                rate_val = self.fine_rate_entry.get().strip()
                rate = float(rate_val) if rate_val.replace('.', '', 1).isdigit() else DEFAULT_FINE_PER_DAY
                fine_str = f"{overdue_days * rate:.2f}"
            elif diff_days <= 3:
                display_status = f"🟡 Due in {diff_days}d" if diff_days > 0 else "🟡 Due Today!"
                tag = "active_soon"
                fine_str = "0.00"
            else:
                display_status = f"🟢 {diff_days}d Left"
                tag = "active_ontime"
                fine_str = "0.00"

            self.tree.insert(
                "",
                tk.END,
                iid=str(t_id),
                values=(
                    t_id,
                    row['BookTitle'],
                    m_id,
                    row['CustomerName'],
                    row['IssueDate'],
                    row['DueDate'],
                    display_status,
                    fine_str
                ),
                tags=(tag,)
            )

        self._reset_return_card()

    def _on_tree_select(self, event=None) -> None:
        selection = self.tree.selection()
        if not selection:
            self._reset_return_card()
            return

        t_id = int(selection[0])
        self.selected_trans_id = t_id

        match = self.db.transactions_df[self.db.transactions_df['TransactionID'] == t_id]
        if match.empty:
            return

        row = match.iloc[0]
        cust = row['CustomerName']
        trans_m_id = str(row.get('MemberID', ''))
        book_id = row['BookID']
        due = str(row['DueDate'])

        book = self.db.get_book_by_id(book_id)
        title = book['Title'] if book else f"Book #{book_id}"

        patron = None
        if trans_m_id:
            patron = self.db.get_patron_by_member_id(trans_m_id)
        if not patron:
            patron = self.db.get_patron_by_name(cust)

        patron_merit_text = f"• Merit: {patron['MeritScore']} pts" if patron else ""
        mem_tag = f"[{trans_m_id}] " if trans_m_id else ""

        overdue_days = self.db.calculate_overdue_days(due)
        rate_val = self.fine_rate_entry.get().strip()
        rate = float(rate_val) if rate_val.replace('.', '', 1).isdigit() else DEFAULT_FINE_PER_DAY
        estimated_fine = round(overdue_days * rate, 2)

        if overdue_days > 0:
            msg = (
                f"⚠️ OVERDUE by {overdue_days} days! Book: '{title}' to {mem_tag}{cust} {patron_merit_text}\n"
                f"Due: {due} | Fine Assessed: ₹{estimated_fine:.2f} | Merit Penalty: -{overdue_days * 2} pts"
            )
            self.return_info_badge.configure(
                text=msg,
                fg_color=("#FEE2E2", "#7F1D1D"),
                text_color=("#B91C1C", "#FCA5A5")
            )
            self.renew_btn.configure(state="disabled")
        else:
            msg = (
                f"Ready to Return / Renew: '{title}' issued to {mem_tag}{cust} (Due {due}) {patron_merit_text}.\n"
                f"On-time return earns +5 Merit Points bonus! ⭐"
            )
            self.return_info_badge.configure(
                text=msg,
                fg_color=("#ECFDF5", "#064E3B"),
                text_color=("#047857", "#6EE7B7")
            )
            self.renew_btn.configure(state="normal")

        self.return_btn.configure(state="normal")

    def _reset_return_card(self) -> None:
        self.selected_trans_id = None
        self.return_info_badge.configure(
            text="💡 Select an active loan from the table above to process return, renew, or view circulation receipt.",
            fg_color=("#EFF6FF", "#1E293B"),
            text_color=("#1D4ED8", "#93C5FD")
        )
        self.return_btn.configure(state="disabled")
        self.renew_btn.configure(state="disabled")

    def _on_issue_book(self) -> None:
        if self.selected_book is None:
            messagebox.showwarning(
                "Book Selection Required",
                "Please click the '📚 Browse Catalog...' button to choose an available book first."
            )
            return

        book_id = self.selected_book['BookID']
        name = self.cust_name_entry.get().strip()
        email = self.cust_email_entry.get().strip()

        if not name and not self.selected_member_id:
            messagebox.showerror("Validation Error", "Customer Name or Member ID is required.")
            return

        dur_text = self.loan_days_cb.get()
        days = int(dur_text.split()[0]) if dur_text.split()[0].isdigit() else DEFAULT_LOAN_DAYS

        try:
            result = self.db.issue_book(
                book_id=book_id,
                customer_name=name,
                customer_email=email,
                member_id=self.selected_member_id,
                loan_days=days
            )

            # Generate digital issue slip
            slip = (
                "=========================================\n"
                "       📚 LIBRARY CIRCULATION SLIP       \n"
                "=========================================\n"
                f"Transaction ID : #{result['transaction_id']}\n"
                f"Date Issued    : {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
                f"Book Title     : {result['book_title']}\n"
                f"Member ID      : {result['member_id']}\n"
                f"Patron Name    : {result['customer_name']}\n"
                f"Scheduled Due  : {result['due_date']} ({days} days)\n"
                "-----------------------------------------\n"
                f"Patron Merit   : {result['merit_score']} Points\n"
                f"Standing Tier  : {result['merit_tier']}\n"
                "=========================================\n"
                "Please return on or before due date to\n"
                "earn +5 Merit Points!\n"
            )
            self.last_receipt = slip
            self.receipt_btn.configure(state="normal")

            messagebox.showinfo(
                "Loan Issued Successfully",
                f"🎉 Book '{result['book_title']}' has been issued to [{result['member_id']}] {result['customer_name']}.\n\n"
                f"Member ID: {result['member_id']}\n"
                f"Due Date: {result['due_date']} (in {days} days)\n"
                f"Patron Merit: {result['merit_score']} ({result['merit_tier']})\n"
                f"Transaction ID: #{result['transaction_id']}"
            )

            self._reset_issue_form()
            self.refresh()
            self.on_change_callback()
        except Exception as e:
            messagebox.showerror("Issue Failed", str(e))

    def _on_return_selected(self) -> None:
        if self.selected_trans_id is None:
            messagebox.showwarning("Notice", "Please select an active transaction from the table to return.")
            return

        try:
            rate_val = self.fine_rate_entry.get().strip()
            rate = float(rate_val) if rate_val.replace('.', '', 1).isdigit() else DEFAULT_FINE_PER_DAY
            
            result = self.db.return_book(transaction_id=self.selected_trans_id, fine_per_day=rate)

            fine = result['fine_amount']
            overdue = result['overdue_days']
            delta = result['merit_delta']
            score = result['new_merit_score']
            tier = result['merit_tier']

            if overdue > 0:
                fine_msg = f"⚠️ Overdue: {overdue} days late\nFine Assessed: ₹{fine:.2f}\nMerit Deduction: {delta} points"
            else:
                fine_msg = f"✅ On-time Return: No late fine!\nMerit Awarded: +{delta} Points Bonus ⭐"

            receipt = (
                "=========================================\n"
                "       📥 LIBRARY RETURN RECEIPT        \n"
                "=========================================\n"
                f"Transaction ID : #{result['transaction_id']}\n"
                f"Book Title     : {result['book_title']}\n"
                f"Patron Name    : {result['customer_name']}\n"
                f"Member ID      : {result['member_id']}\n"
                f"Scheduled Due  : {result['due_date']}\n"
                f"Actual Return  : {result['return_date']}\n"
                "-----------------------------------------\n"
                f"Days Overdue   : {overdue} days\n"
                f"Late Fine Paid : ₹{fine:.2f}\n"
                "-----------------------------------------\n"
                f"Merit Change   : {delta:+d} Points\n"
                f"New Merit Score: {score} Points\n"
                f"Merit Standing : {tier}\n"
                "=========================================\n"
                "Thank you for returning your library book!\n"
            )
            self.last_receipt = receipt
            self.receipt_btn.configure(state="normal")

            messagebox.showinfo(
                "Return Processed Successfully",
                f"Book: '{result['book_title']}'\n"
                f"Customer: [{result['member_id']}] {result['customer_name']}\n\n"
                f"{fine_msg}\n"
                f"Current Merit: {score} Points ({tier})"
            )

            self.refresh()
            self.on_change_callback()
        except Exception as e:
            messagebox.showerror("Return Failed", str(e))

    def _on_renew_selected(self) -> None:
        if self.selected_trans_id is None:
            messagebox.showwarning("Notice", "Please select an active transaction to renew.")
            return

        try:
            res = self.db.renew_loan(self.selected_trans_id, additional_days=7)
            messagebox.showinfo(
                "Loan Renewed",
                f"🎉 Loan #{res['transaction_id']} renewed successfully for {res['customer_name']}!\n\n"
                f"New Due Date: {res['new_due_date']} (+7 days extension)"
            )
            self.refresh()
            self.on_change_callback()
        except Exception as e:
            messagebox.showerror("Renewal Failed", str(e))

    def _show_last_receipt(self) -> None:
        if not self.last_receipt:
            return
        TransactionReceiptDialog(self, self.last_receipt, title="🧾 Digital Circulation Receipt")
