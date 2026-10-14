"""
Modern Transactions View built with CustomTkinter.
"""
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Callable, Optional
import customtkinter as ctk

from ..database import LibraryDatabase
from ..models import (
    DEFAULT_FINE_PER_DAY,
    DEFAULT_LOAN_DAYS,
    STATUS_AVAILABLE,
    TRANS_STATUS_ISSUED,
    TRANS_STATUS_RETURNED,
)
from .styles import (
    COLOR_DANGER,
    COLOR_PRIMARY,
    COLOR_PRIMARY_HOVER,
    COLOR_SUCCESS,
    COLOR_SUCCESS_HOVER,
    FONT_BODY,
    FONT_BODY_BOLD,
    FONT_SECTION,
    FONT_SMALL,
    FONT_SUBTITLE,
)


class TransactionsView(ctk.CTkFrame):
    """Modern view for loan issuance, returns, overdue fine computing, and circulation tracking."""

    def __init__(self, parent, db: LibraryDatabase, on_change_callback: Callable[[], None]):
        super().__init__(parent, fg_color="transparent")
        self.db = db
        self.on_change_callback = on_change_callback
        self.selected_trans_id: Optional[int] = None

        self._create_widgets()
        self.refresh()

    def _create_widgets(self) -> None:
        self.columnconfigure(0, weight=0, minsize=350)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        # -----------------------------
        # Left Panel: Issue & Return Cards
        # -----------------------------
        left_panel = ctk.CTkFrame(self, fg_color="transparent")
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 12), pady=4)
        left_panel.rowconfigure(0, weight=0)
        left_panel.rowconfigure(1, weight=1)
        left_panel.columnconfigure(0, weight=1)

        # 1. Issue Book Card
        issue_card = ctk.CTkFrame(left_panel, corner_radius=12)
        issue_card.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        ctk.CTkLabel(issue_card, text="📤 Issue Book to Patron", font=FONT_SUBTITLE).pack(fill="x", padx=16, pady=(14, 6))

        # Book ID + Auto preview
        ctk.CTkLabel(issue_card, text="Book ID *", font=FONT_BODY_BOLD, anchor="w").pack(fill="x", padx=16, pady=(4, 2))
        self.book_id_entry = ctk.CTkEntry(
            issue_card,
            placeholder_text="e.g. 1, 2, 3...",
            height=34,
            corner_radius=8,
            font=FONT_BODY
        )
        self.book_id_entry.pack(fill="x", padx=16, pady=(0, 4))
        self.book_id_entry.bind("<KeyRelease>", lambda _: self._preview_book_info())

        self.book_preview_badge = ctk.CTkLabel(
            issue_card,
            text="Enter Book ID to verify availability",
            font=FONT_SMALL,
            fg_color=("#F1F5F9", "#27272A"),
            text_color=("gray40", "gray70"),
            corner_radius=6,
            height=28
        )
        self.book_preview_badge.pack(fill="x", padx=16, pady=(0, 8))

        # Patron Name
        ctk.CTkLabel(issue_card, text="Customer Name *", font=FONT_BODY_BOLD, anchor="w").pack(fill="x", padx=16, pady=(4, 2))
        self.cust_name_entry = ctk.CTkEntry(
            issue_card,
            placeholder_text="Full patron name...",
            height=34,
            corner_radius=8,
            font=FONT_BODY
        )
        self.cust_name_entry.pack(fill="x", padx=16, pady=(0, 6))

        # Patron Email
        ctk.CTkLabel(issue_card, text="Customer Email", font=FONT_BODY_BOLD, anchor="w").pack(fill="x", padx=16, pady=(4, 2))
        self.cust_email_entry = ctk.CTkEntry(
            issue_card,
            placeholder_text="name@example.com",
            height=34,
            corner_radius=8,
            font=FONT_BODY
        )
        self.cust_email_entry.pack(fill="x", padx=16, pady=(0, 6))

        # Loan Duration
        ctk.CTkLabel(issue_card, text="Loan Duration", font=FONT_BODY_BOLD, anchor="w").pack(fill="x", padx=16, pady=(4, 2))
        self.loan_days_cb = ctk.CTkOptionMenu(
            issue_card,
            values=["7 days", "14 days (Standard)", "21 days", "30 days"],
            height=34,
            corner_radius=8,
            font=FONT_BODY
        )
        self.loan_days_cb.set("14 days (Standard)")
        self.loan_days_cb.pack(fill="x", padx=16, pady=(0, 12))

        # Issue Button
        self.issue_btn = ctk.CTkButton(
            issue_card,
            text="🚀 Confirm & Issue Loan",
            font=FONT_BODY_BOLD,
            fg_color=COLOR_PRIMARY,
            hover_color=COLOR_PRIMARY_HOVER,
            height=38,
            corner_radius=8,
            command=self._on_issue_book
        )
        self.issue_btn.pack(fill="x", padx=16, pady=(0, 16))

        # 2. Return Selected Card
        return_card = ctk.CTkFrame(left_panel, corner_radius=12)
        return_card.grid(row=1, column=0, sticky="nsew")

        ctk.CTkLabel(return_card, text="📥 Return Book & Check In", font=FONT_SUBTITLE).pack(fill="x", padx=16, pady=(14, 6))

        self.return_info_badge = ctk.CTkLabel(
            return_card,
            text="Select an active loan from the table to process its return.",
            font=FONT_SMALL,
            fg_color=("#EFF6FF", "#1E293B"),
            text_color=("#1D4ED8", "#93C5FD"),
            corner_radius=8,
            wraplength=280,
            justify="left",
            padx=12,
            pady=10
        )
        return_card.columnconfigure(0, weight=1)
        self.return_info_badge.pack(fill="x", padx=16, pady=(0, 10))

        # Fine Rate Config
        rate_row = ctk.CTkFrame(return_card, fg_color="transparent")
        rate_row.pack(fill="x", padx=16, pady=(0, 12))
        ctk.CTkLabel(rate_row, text="Fine rate:", font=FONT_SMALL, text_color=("gray40", "gray70")).pack(side="left")
        self.fine_rate_entry = ctk.CTkEntry(rate_row, width=60, height=28, corner_radius=6, font=FONT_SMALL)
        self.fine_rate_entry.insert(0, str(DEFAULT_FINE_PER_DAY))
        self.fine_rate_entry.pack(side="left", padx=6)
        ctk.CTkLabel(rate_row, text="₹/day overdue", font=FONT_SMALL, text_color=("gray40", "gray70")).pack(side="left")

        self.return_btn = ctk.CTkButton(
            return_card,
            text="✅ Return Selected Book",
            font=FONT_BODY_BOLD,
            fg_color=COLOR_SUCCESS,
            hover_color=COLOR_SUCCESS_HOVER,
            height=38,
            corner_radius=8,
            state="disabled",
            command=self._on_return_selected
        )
        self.return_btn.pack(fill="x", padx=16, pady=(0, 16))

        # -----------------------------
        # Right Panel: Search, Filters & Transactions Table
        # -----------------------------
        right_panel = ctk.CTkFrame(self, fg_color="transparent")
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
            placeholder_text="🔍 Search patron, book title, email, or Transaction ID...",
            font=FONT_BODY,
            height=36,
            corner_radius=8
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.search_entry.bind("<KeyRelease>", lambda _: self.refresh())

        self.status_segment = ctk.CTkSegmentedButton(
            search_row,
            values=["Active", "Overdue", "Returned", "All"],
            height=34,
            corner_radius=8,
            command=lambda _: self.refresh()
        )
        self.status_segment.set("Active")
        self.status_segment.pack(side="left", padx=(0, 8))

        export_btn = ctk.CTkButton(
            search_row,
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

        # Table Container
        table_container = ctk.CTkFrame(right_panel, corner_radius=12)
        table_container.grid(row=1, column=0, sticky="nsew")
        table_container.rowconfigure(0, weight=1)
        table_container.columnconfigure(0, weight=1)

        tree_scroll_y = ttk.Scrollbar(table_container, orient="vertical")
        tree_scroll_x = ttk.Scrollbar(table_container, orient="horizontal")

        columns = (
            ("TransID", "Trans ID", 70, "center"),
            ("BookID", "Book ID", 65, "center"),
            ("BookTitle", "Book Title", 180, "w"),
            ("CustomerName", "Customer", 140, "w"),
            ("CustomerEmail", "Email", 150, "w"),
            ("IssueDate", "Issued", 90, "center"),
            ("DueDate", "Due Date", 90, "center"),
            ("ReturnDate", "Returned", 90, "center"),
            ("Status", "Status", 100, "center"),
            ("FineAmount", "Fine (₹)", 80, "e"),
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

        # Tags
        is_dark = ctk.get_appearance_mode() == "Dark"
        self.tree.tag_configure("active_ontime", background="#2D2814" if is_dark else "#FEFCE8")
        self.tree.tag_configure("active_overdue", background="#7F1D1D" if is_dark else "#FEE2E2", foreground="#FCA5A5" if is_dark else "#991B1B")
        self.tree.tag_configure("returned", background="#18181B" if is_dark else "#FFFFFF")

        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)
        self.tree.bind("<Double-1>", lambda _: self._on_return_selected())

        self.count_label = ctk.CTkLabel(
            right_panel,
            text="Showing 0 transactions",
            font=FONT_SMALL,
            text_color=("gray40", "gray70"),
            anchor="w"
        )
        self.count_label.grid(row=2, column=0, sticky="ew", padx=6, pady=(4, 0))

    def _preview_book_info(self) -> None:
        val = self.book_id_entry.get().strip()
        if not val.isdigit():
            self.book_preview_badge.configure(
                text="Enter Book ID to verify availability",
                fg_color=("#F1F5F9", "#27272A"),
                text_color=("gray40", "gray70")
            )
            return

        book = self.db.get_book_by_id(int(val))
        if not book:
            self.book_preview_badge.configure(
                text="❌ No book found with this ID",
                fg_color=("#FEE2E2", "#7F1D1D"),
                text_color=("#B91C1C", "#FCA5A5")
            )
            return

        avail = book['AvailableCopies']
        title = book['Title']
        if avail > 0:
            self.book_preview_badge.configure(
                text=f"✅ '{title}' ({avail} copies available)",
                fg_color=("#ECFDF5", "#064E3B"),
                text_color=("#047857", "#6EE7B7")
            )
        else:
            self.book_preview_badge.configure(
                text=f"⚠️ '{title}' (0 available - Checked Out)",
                fg_color=("#FEF3C7", "#78350F"),
                text_color=("#B45309", "#FDE68A")
            )

    def refresh(self) -> None:
        """Reload transactions from database."""
        for item in self.tree.get_children():
            self.tree.delete(item)

        df = self.db.get_transactions(
            filter_status=self.status_segment.get(),
            search_query=self.search_entry.get()
        )

        today_str = datetime.now().strftime("%Y-%m-%d")

        for _, row in df.iterrows():
            t_id = row['TransactionID']
            status = row['Status']
            due_date = str(row['DueDate'])
            fine = row['FineAmount']

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

        self.count_label.configure(text=f"Showing {len(df)} transactions")
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
        status = row['Status']
        cust = row['CustomerName']
        book_id = row['BookID']
        due = str(row['DueDate'])

        book = self.db.get_book_by_id(book_id)
        title = book['Title'] if book else f"Book #{book_id}"

        if status == TRANS_STATUS_ISSUED:
            overdue_days = self.db.calculate_overdue_days(due)
            rate_val = self.fine_rate_entry.get().strip()
            rate = float(rate_val) if rate_val.replace('.', '', 1).isdigit() else DEFAULT_FINE_PER_DAY
            estimated_fine = round(overdue_days * rate, 2)

            if overdue_days > 0:
                msg = (
                    f"⚠️ OVERDUE by {overdue_days} days!\n"
                    f"Book: '{title}' to {cust}\n"
                    f"Due: {due} | Estimated Fine: ₹{estimated_fine:.2f}"
                )
                self.return_info_badge.configure(
                    text=msg,
                    fg_color=("#FEE2E2", "#7F1D1D"),
                    text_color=("#B91C1C", "#FCA5A5")
                )
            else:
                msg = f"Ready to Return:\n'{title}' issued to {cust} (Due {due})."
                self.return_info_badge.configure(
                    text=msg,
                    fg_color=("#ECFDF5", "#064E3B"),
                    text_color=("#047857", "#6EE7B7")
                )
            self.return_btn.configure(state="normal")
        else:
            self.return_info_badge.configure(
                text=f"Transaction #{t_id} is already returned on {row['ReturnDate']}.\nFine Paid: ₹{row['FineAmount']:.2f}",
                fg_color=("#F1F5F9", "#27272A"),
                text_color=("gray40", "gray70")
            )
            self.return_btn.configure(state="disabled")

    def _reset_return_card(self) -> None:
        self.selected_trans_id = None
        self.return_info_badge.configure(
            text="Select an active loan from the table to process its return.",
            fg_color=("#EFF6FF", "#1E293B"),
            text_color=("#1D4ED8", "#93C5FD")
        )
        self.return_btn.configure(state="disabled")

    def _on_issue_book(self) -> None:
        try:
            b_val = self.book_id_entry.get().strip()
            if not b_val.isdigit():
                messagebox.showerror("Validation Error", "Please provide a valid numeric Book ID.")
                return

            book_id = int(b_val)
            name = self.cust_name_entry.get().strip()
            email = self.cust_email_entry.get().strip()

            if not name:
                messagebox.showerror("Validation Error", "Customer Name is required.")
                return

            dur_text = self.loan_days_cb.get()
            days = int(dur_text.split()[0]) if dur_text.split()[0].isdigit() else DEFAULT_LOAN_DAYS

            result = self.db.issue_book(
                book_id=book_id,
                customer_name=name,
                customer_email=email,
                loan_days=days
            )

            messagebox.showinfo(
                "Loan Issued Successfully",
                f"🎉 Book '{result['book_title']}' has been issued to {result['customer_name']}.\n\n"
                f"Due Date: {result['due_date']} (in {days} days)\n"
                f"Transaction ID: #{result['transaction_id']}"
            )

            self.book_id_entry.delete(0, tk.END)
            self.cust_name_entry.delete(0, tk.END)
            self.cust_email_entry.delete(0, tk.END)
            self._preview_book_info()

            self.refresh()
            self.on_change_callback()
        except Exception as e:
            messagebox.showerror("Issue Failed", str(e))

    def _on_return_selected(self) -> None:
        if self.selected_trans_id is None:
            messagebox.showwarning("Notice", "Please select an active transaction to return.")
            return

        try:
            rate_val = self.fine_rate_entry.get().strip()
            rate = float(rate_val) if rate_val.replace('.', '', 1).isdigit() else DEFAULT_FINE_PER_DAY
            
            result = self.db.return_book(transaction_id=self.selected_trans_id, fine_per_day=rate)

            fine = result['fine_amount']
            overdue = result['overdue_days']
            if overdue > 0:
                fine_msg = f"⚠️ Book was overdue by {overdue} days.\nTotal Fine Assessed: ₹{fine:.2f}"
            else:
                fine_msg = "✅ Returned on time. No fine incurred."

            messagebox.showinfo(
                "Return Processed",
                f"Book: '{result['book_title']}'\n"
                f"Customer: {result['customer_name']}\n"
                f"Return Date: {result['return_date']}\n\n"
                f"{fine_msg}"
            )

            self.refresh()
            self.on_change_callback()
        except Exception as e:
            messagebox.showerror("Return Failed", str(e))

    def _on_export_csv(self) -> None:
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Export Transactions as CSV"
        )
        if file_path:
            try:
                self.db.export_data_to_csv('transactions', file_path)
                messagebox.showinfo("Export Successful", f"Transactions exported to:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Export Failed", str(e))
