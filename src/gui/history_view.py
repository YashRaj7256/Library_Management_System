"""
Dedicated Transaction History and Audit Trail View built with CustomTkinter.
Features full historical logging, multi-parameter filtering, date ranges, summary KPIs, and digital receipt generation.
"""
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Callable, Optional, Dict, Any
import customtkinter as ctk
import pandas as pd

from ..database import LibraryDatabase
from ..models import TRANS_STATUS_ISSUED, TRANS_STATUS_RETURNED, get_merit_tier
from .dialogs import TransactionReceiptDialog
from .styles import (
    COLOR_PRIMARY,
    COLOR_PRIMARY_HOVER,
    COLOR_SUCCESS,
    COLOR_SUCCESS_HOVER,
    COLOR_DANGER,
    FONT_BODY,
    FONT_BODY_BOLD,
    FONT_HEADING,
    FONT_SECTION,
    FONT_SMALL,
    FONT_SUBTITLE,
    FONT_MONO,
    apply_treeview_row_tags,
)


class HistoryView(ctk.CTkFrame):
    """Dedicated view for auditing all historical transactions, loans, and returns."""

    def __init__(self, parent, db: LibraryDatabase, on_change_callback: Callable[[], None]):
        super().__init__(parent, fg_color="transparent")
        self.db = db
        self.on_change_callback = on_change_callback
        self.selected_trans_id: Optional[int] = None

        self._create_widgets()
        self.refresh()

    def _create_widgets(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        # -----------------------------
        # 1. Top KPI Summary Cards Row
        # -----------------------------
        kpi_row = ctk.CTkFrame(self, fg_color="transparent")
        kpi_row.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        kpi_row.columnconfigure((0, 1, 2, 3), weight=1)

        # Total Card
        self.card_total = self._build_kpi_card(kpi_row, 0, "📜 Total Transactions", "0", ("#E0E7FF", "#1E1B4B"), ("#3730A3", "#A5B4FC"))
        # Active Loans Card
        self.card_active = self._build_kpi_card(kpi_row, 1, "⚡ Active Borrowings", "0", ("#ECFDF5", "#064E3B"), ("#065F46", "#6EE7B7"))
        # Returned Card
        self.card_returned = self._build_kpi_card(kpi_row, 2, "✅ Completed Returns", "0", ("#F1F5F9", "#1E293B"), ("#334155", "#94A3B8"))
        # Total Fines Card
        self.card_fines = self._build_kpi_card(kpi_row, 3, "💰 Fines Collected", "₹0.00", ("#FEF3C7", "#78350F"), ("#92400E", "#FDE68A"))

        # -----------------------------
        # 2. Filter & Controls Card
        # -----------------------------
        filter_card = ctk.CTkFrame(self, corner_radius=12)
        filter_card.grid(row=1, column=0, sticky="ew", pady=(0, 10))

        filter_layout = ctk.CTkFrame(filter_card, fg_color="transparent")
        filter_layout.pack(fill="x", padx=14, pady=12)

        # Search Bar
        self.search_entry = ctk.CTkEntry(
            filter_layout,
            placeholder_text="🔍 Search patron, book title, member ID, or transaction ID...",
            font=FONT_BODY,
            height=36,
            corner_radius=8
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.search_entry.bind("<KeyRelease>", lambda _: self.refresh())

        # Status Segmented Filter
        self.status_segment = ctk.CTkSegmentedButton(
            filter_layout,
            values=["All", "Active", "Returned", "Overdue"],
            height=34,
            corner_radius=8,
            command=lambda _: self.refresh()
        )
        self.status_segment.set("All")
        self.status_segment.pack(side="left", padx=(0, 8))

        # Date Range Filter
        self.date_filter_cb = ctk.CTkOptionMenu(
            filter_layout,
            values=["All Time", "Today", "Last 7 Days", "Last 30 Days"],
            height=34,
            corner_radius=8,
            font=FONT_BODY,
            command=lambda _: self.refresh()
        )
        self.date_filter_cb.set("All Time")
        self.date_filter_cb.pack(side="left", padx=(0, 8))

        # View Receipt / Details Button
        self.receipt_btn = ctk.CTkButton(
            filter_layout,
            text="🧾 View Slip",
            font=FONT_BODY_BOLD,
            fg_color=("#EEF2FF", "#2E1065"),
            text_color=("#4F46E5", "#C4B5FD"),
            hover_color=("#E0E7FF", "#3B0764"),
            width=100,
            height=34,
            corner_radius=8,
            state="disabled",
            command=self._show_selected_receipt
        )
        self.receipt_btn.pack(side="left", padx=(0, 6))

        # Export CSV Button
        export_btn = ctk.CTkButton(
            filter_layout,
            text="📥 Export CSV",
            font=FONT_BODY_BOLD,
            fg_color=("#E0E7FF", "#1E293B"),
            text_color=("#4338CA", "#A5B4FC"),
            hover_color=("#C7D2FE", "#334155"),
            width=100,
            height=34,
            corner_radius=8,
            command=self._on_export_csv
        )
        export_btn.pack(side="right")

        # -----------------------------
        # 3. Main Data Table
        # -----------------------------
        table_container = ctk.CTkFrame(self, corner_radius=12)
        table_container.grid(row=2, column=0, sticky="nsew")
        table_container.rowconfigure(0, weight=1)
        table_container.columnconfigure(0, weight=1)

        tree_scroll_y = ttk.Scrollbar(table_container, orient="vertical")
        tree_scroll_x = ttk.Scrollbar(table_container, orient="horizontal")

        columns = (
            ("TransID", "Trans ID", 65, "center"),
            ("BookID", "Book ID", 60, "center"),
            ("BookTitle", "Book Title", 180, "w"),
            ("MemberID", "Member ID", 80, "center"),
            ("CustomerName", "Customer", 135, "w"),
            ("CustomerEmail", "Email", 145, "w"),
            ("IssueDate", "Issued", 85, "center"),
            ("DueDate", "Due Date", 85, "center"),
            ("ReturnDate", "Returned", 85, "center"),
            ("Status", "Status", 100, "center"),
            ("FineAmount", "Fine (₹)", 75, "e"),
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
        self.tree.bind("<Double-1>", lambda _: self._show_selected_receipt())

        # -----------------------------
        # 4. Footer Status Row
        # -----------------------------
        self.footer_lbl = ctk.CTkLabel(
            self,
            text="Showing 0 transactions | Double-click any row to view full audit slip",
            font=FONT_SMALL,
            text_color=("gray40", "gray70"),
            anchor="w"
        )
        self.footer_lbl.grid(row=3, column=0, sticky="ew", padx=6, pady=(6, 0))

    def _build_kpi_card(self, parent, col: int, title: str, default_val: str, bg_color: tuple, text_color: tuple) -> ctk.CTkLabel:
        """Helper to create a modern KPI stat metric card."""
        frame = ctk.CTkFrame(parent, corner_radius=10, fg_color=bg_color)
        frame.grid(row=0, column=col, padx=(0 if col == 0 else 6, 0 if col == 3 else 6), sticky="nsew")

        ctk.CTkLabel(
            frame,
            text=title,
            font=FONT_SMALL,
            text_color=text_color,
            anchor="w"
        ).pack(fill="x", padx=12, pady=(10, 2))

        val_lbl = ctk.CTkLabel(
            frame,
            text=default_val,
            font=FONT_HEADING,
            text_color=text_color,
            anchor="w"
        )
        val_lbl.pack(fill="x", padx=12, pady=(0, 10))
        return val_lbl

    def refresh(self) -> None:
        """Reload historical transaction records and apply filters and date ranges."""
        apply_treeview_row_tags(self.tree, "history", ctk.get_appearance_mode())

        for item in self.tree.get_children():
            self.tree.delete(item)

        status_filter = self.status_segment.get()
        search_query = self.search_entry.get().strip()

        df = self.db.get_transactions(
            filter_status=status_filter,
            search_query=search_query
        )

        # Date Range Filter
        date_mode = self.date_filter_cb.get()
        today = datetime.now().date()
        today_str = today.strftime("%Y-%m-%d")

        if not df.empty and date_mode != "All Time":
            if date_mode == "Today":
                mask = (df['IssueDate'] == today_str) | (df['ReturnDate'] == today_str)
                df = df[mask]
            elif date_mode == "Last 7 Days":
                cutoff = (today - pd.Timedelta(days=7)).strftime("%Y-%m-%d")
                mask = (df['IssueDate'] >= cutoff) | (df['ReturnDate'] >= cutoff)
                df = df[mask]
            elif date_mode == "Last 30 Days":
                cutoff = (today - pd.Timedelta(days=30)).strftime("%Y-%m-%d")
                mask = (df['IssueDate'] >= cutoff) | (df['ReturnDate'] >= cutoff)
                df = df[mask]

        # Update KPI Cards based on full DB transactions
        all_trans = self.db.transactions_df
        total_count = len(all_trans)
        active_count = len(all_trans[all_trans['Status'] == TRANS_STATUS_ISSUED])
        returned_count = len(all_trans[all_trans['Status'] == TRANS_STATUS_RETURNED])
        total_fines = float(all_trans['FineAmount'].sum()) if 'FineAmount' in all_trans.columns else 0.0

        self.card_total.configure(text=f"{total_count:,}")
        self.card_active.configure(text=f"{active_count:,}")
        self.card_returned.configure(text=f"{returned_count:,}")
        self.card_fines.configure(text=f"₹{total_fines:,.2f}")

        # Populate Treeview
        for _, row in df.iterrows():
            t_id = row['TransactionID']
            status = row['Status']
            due_date = str(row['DueDate'])
            fine = row['FineAmount']
            m_id = str(row.get('MemberID', ''))

            if status == TRANS_STATUS_ISSUED:
                if due_date < today_str:
                    overdue_days = self.db.calculate_overdue_days(due_date)
                    display_status = f"⚠️ Overdue ({overdue_days}d)"
                    tag = "active_overdue"
                else:
                    display_status = "Issued"
                    tag = "active_ontime"
            else:
                display_status = "Returned"
                tag = "returned"

            fine_str = f"{fine:.2f}" if fine > 0 else "0.00"

            self.tree.insert(
                "",
                tk.END,
                iid=str(t_id),
                values=(
                    t_id,
                    row['BookID'],
                    row['BookTitle'],
                    m_id,
                    row['CustomerName'],
                    row['CustomerEmail'],
                    row['IssueDate'],
                    row['DueDate'],
                    row['ReturnDate'] if row['ReturnDate'] else "-",
                    display_status,
                    fine_str
                ),
                tags=(tag,)
            )

        self.footer_lbl.configure(
            text=f"Showing {len(df)} transactions | Double-click any row to view full audit slip"
        )
        self.selected_trans_id = None
        self.receipt_btn.configure(state="disabled")

    def _on_tree_select(self, event=None) -> None:
        selection = self.tree.selection()
        if not selection:
            self.selected_trans_id = None
            self.receipt_btn.configure(state="disabled")
            return

        self.selected_trans_id = int(selection[0])
        self.receipt_btn.configure(state="normal")

    def _show_selected_receipt(self) -> None:
        """Display an audit receipt modal for the selected transaction."""
        if self.selected_trans_id is None:
            return

        match = self.db.transactions_df[self.db.transactions_df['TransactionID'] == self.selected_trans_id]
        if match.empty:
            return

        row = match.iloc[0]
        slip_text = self._generate_audit_slip(row)
        TransactionReceiptDialog(self, slip_text, title=f"🧾 Audit Slip — Transaction #{self.selected_trans_id}")

    def _generate_audit_slip(self, row: pd.Series) -> str:
        """Generate a complete formatted digital audit slip for any historical transaction."""
        b_id = int(row['BookID'])
        book = self.db.get_book_by_id(b_id)
        title = book['Title'] if book else f"Book #{b_id}"
        author = book.get('Author', 'Unknown Author') if book else "Unknown Author"

        m_id = str(row.get('MemberID', ''))
        patron = None
        if m_id:
            patron = self.db.get_patron_by_member_id(m_id)
        if not patron:
            patron = self.db.get_patron_by_name(str(row['CustomerName']))

        merit_str = f"{patron['MeritScore']} Points ({get_merit_tier(patron['MeritScore'])['badge']})" if patron else "Standard Guest"
        phone_str = patron.get('Phone', 'N/A') if patron else "N/A"

        status = row['Status']
        fine = float(row.get('FineAmount', 0.0))
        ret_date = str(row['ReturnDate']) if row['ReturnDate'] else "Active (Not Returned)"

        lines = [
            "=========================================",
            "       📜 TRANSACTION AUDIT SLIP        ",
            "=========================================",
            f"Transaction ID : #{row['TransactionID']}",
            f"Current Status : {status.upper()}",
            "-----------------------------------------",
            "📖 BOOK DETAILS:",
            f"Book ID        : #{b_id}",
            f"Title          : {title}",
            f"Author         : {author}",
            "-----------------------------------------",
            "👤 PATRON DETAILS:",
            f"Member ID      : {m_id or 'Guest'}",
            f"Patron Name    : {row['CustomerName']}",
            f"Contact Email  : {row['CustomerEmail']}",
            f"Phone Number   : {phone_str}",
            f"Merit Standing : {merit_str}",
            "-----------------------------------------",
            "📅 CIRCULATION TIMELINE:",
            f"Issue Date     : {row['IssueDate']}",
            f"Scheduled Due  : {row['DueDate']}",
            f"Actual Return  : {ret_date}",
            "-----------------------------------------",
            f"Fine Assessed  : ₹{fine:.2f}",
            "=========================================",
            "Library Management System Pro — Audit Record",
        ]
        return "\n".join(lines)

    def _on_export_csv(self) -> None:
        """Export current filtered transaction history to a CSV file."""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Export Transaction History to CSV"
        )
        if file_path:
            try:
                self.db.export_data_to_csv('transactions', file_path)
                messagebox.showinfo("Export Successful", f"Transaction records exported successfully to:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Export Failed", str(e))
