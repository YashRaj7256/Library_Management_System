"""
Modern Patrons and User Merit System View built with CustomTkinter.
"""
from datetime import datetime
import re
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from typing import Callable, Optional
import customtkinter as ctk

from ..database import LibraryDatabase
from ..models import (
    INITIAL_MERIT_SCORE,
    MEMBERSHIP_TYPES,
    get_merit_tier,
)
from .styles import (
    COLOR_DANGER,
    COLOR_DANGER_HOVER,
    COLOR_PRIMARY,
    COLOR_PRIMARY_HOVER,
    COLOR_SUCCESS,
    COLOR_SUCCESS_HOVER,
    COLOR_WARNING,
    FONT_BODY,
    FONT_BODY_BOLD,
    FONT_SECTION,
    FONT_SMALL,
    FONT_SUBTITLE,
)


class PatronsView(ctk.CTkFrame):
    """Modern view for member registration, profile management, and Merit score tracking."""

    def __init__(self, parent, db: LibraryDatabase, on_change_callback: Callable[[], None]):
        super().__init__(parent, fg_color="transparent")
        self.db = db
        self.on_change_callback = on_change_callback
        self.selected_patron_id: Optional[int] = None

        self._create_widgets()
        self.refresh()

    def _create_widgets(self) -> None:
        self.columnconfigure(0, weight=0, minsize=350)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        # -----------------------------
        # Left Panel: Registration & Form Card
        # -----------------------------
        self.form_card = ctk.CTkFrame(self, corner_radius=12)
        self.form_card.grid(row=0, column=0, sticky="nsew", padx=(0, 12), pady=4)
        self.form_card.columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self.form_card,
            text="👤 Member Registration & Profile",
            font=FONT_SUBTITLE,
            anchor="w"
        ).pack(fill="x", padx=16, pady=(16, 6))

        self.mode_badge = ctk.CTkLabel(
            self.form_card,
            text="✨ Initial Merit: 100 Points Given",
            font=FONT_SMALL,
            fg_color=("#ECFDF5", "#064E3B"),
            text_color=("#047857", "#6EE7B7"),
            corner_radius=6,
            height=28
        )
        self.mode_badge.pack(fill="x", padx=16, pady=(0, 12))

        # Scrollable form fields
        form_scroll = ctk.CTkScrollableFrame(self.form_card, fg_color="transparent")
        form_scroll.pack(fill="both", expand=True, padx=12, pady=(0, 10))

        # Fields
        ctk.CTkLabel(form_scroll, text="Full Name *", font=FONT_BODY_BOLD, anchor="w").pack(fill="x", pady=(4, 2))
        self.name_entry = ctk.CTkEntry(form_scroll, placeholder_text="e.g. Yash Raj...", height=34, corner_radius=8, font=FONT_BODY)
        self.name_entry.pack(fill="x", pady=(0, 6))

        ctk.CTkLabel(form_scroll, text="Email Address *", font=FONT_BODY_BOLD, anchor="w").pack(fill="x", pady=(4, 2))
        self.email_entry = ctk.CTkEntry(form_scroll, placeholder_text="patron@university.edu...", height=34, corner_radius=8, font=FONT_BODY)
        self.email_entry.pack(fill="x", pady=(0, 6))

        ctk.CTkLabel(form_scroll, text="Phone Number (10 Digits)", font=FONT_BODY_BOLD, anchor="w").pack(fill="x", pady=(4, 2))
        phone_row = ctk.CTkFrame(form_scroll, fg_color="transparent")
        phone_row.pack(fill="x", pady=(0, 6))

        prefix_badge = ctk.CTkLabel(
            phone_row,
            text="+91",
            font=FONT_BODY_BOLD,
            width=50,
            height=34,
            corner_radius=8,
            fg_color=("#E4E4E7", "#27272A"),
            text_color=("#18181B", "#F4F4F5")
        )
        prefix_badge.pack(side="left", padx=(0, 6))

        self.phone_entry = ctk.CTkEntry(
            phone_row,
            placeholder_text="Enter 10 digits (e.g. 9876543210)",
            height=34,
            corner_radius=8,
            font=FONT_BODY
        )
        self.phone_entry.pack(side="left", fill="x", expand=True)
        self.phone_entry.bind("<KeyRelease>", self._on_phone_key_release)

        ctk.CTkLabel(form_scroll, text="Membership Type", font=FONT_BODY_BOLD, anchor="w").pack(fill="x", pady=(4, 2))
        self.type_menu = ctk.CTkOptionMenu(form_scroll, values=MEMBERSHIP_TYPES, height=34, corner_radius=8, font=FONT_BODY)
        self.type_menu.set(MEMBERSHIP_TYPES[0])
        self.type_menu.pack(fill="x", pady=(0, 10))

        # Merit Tier Preview Box
        self.merit_box = ctk.CTkFrame(form_scroll, corner_radius=8, fg_color=("#F1F5F9", "#1E293B"))
        self.merit_box.pack(fill="x", pady=(0, 12), padx=2)
        ctk.CTkLabel(self.merit_box, text="⭐ Merit System Rules", font=FONT_BODY_BOLD, anchor="w").pack(fill="x", padx=10, pady=(8, 4))
        rules_text = (
            "• New Member Bonus: 100 Initial Merit\n"
            "• On-time Return: +5 Merit Points\n"
            "• Overdue Penalty: -2 Points / day late\n"
            "• Gold Tier (120+ pts): 5 Books limit\n"
            "• Suspended (< 50 pts): Borrowing blocked"
        )
        ctk.CTkLabel(self.merit_box, text=rules_text, font=FONT_SMALL, justify="left", text_color=("gray40", "gray70")).pack(fill="x", padx=10, pady=(0, 8))

        # Buttons Grid
        btn_frame = ctk.CTkFrame(self.form_card, fg_color="transparent")
        btn_frame.pack(fill="x", padx=16, pady=(0, 16))
        btn_frame.columnconfigure((0, 1), weight=1)

        self.register_btn = ctk.CTkButton(
            btn_frame,
            text="➕ Register Member",
            font=FONT_BODY_BOLD,
            fg_color=COLOR_SUCCESS,
            hover_color=COLOR_SUCCESS_HOVER,
            height=36,
            corner_radius=8,
            command=self._on_register_patron
        )
        self.register_btn.grid(row=0, column=0, padx=(0, 4), pady=4, sticky="ew")

        self.update_btn = ctk.CTkButton(
            btn_frame,
            text="✏️ Update Profile",
            font=FONT_BODY_BOLD,
            fg_color=COLOR_PRIMARY,
            hover_color=COLOR_PRIMARY_HOVER,
            height=36,
            corner_radius=8,
            state="disabled",
            command=self._on_update_patron
        )
        self.update_btn.grid(row=0, column=1, padx=(4, 0), pady=4, sticky="ew")

        self.adjust_merit_btn = ctk.CTkButton(
            btn_frame,
            text="⚖️ Adjust Merit",
            font=FONT_BODY_BOLD,
            fg_color=("#F59E0B", "#D97706"),
            hover_color=("#D97706", "#B45309"),
            height=36,
            corner_radius=8,
            state="disabled",
            command=self._on_adjust_merit
        )
        self.adjust_merit_btn.grid(row=1, column=0, padx=(0, 4), pady=4, sticky="ew")

        self.clear_btn = ctk.CTkButton(
            btn_frame,
            text="🔄 Clear Form",
            font=FONT_BODY,
            fg_color=("#E4E4E7", "#3F3F46"),
            hover_color=("#D4D4D8", "#52525B"),
            text_color=("#18181B", "#F4F4F5"),
            height=36,
            corner_radius=8,
            command=self.clear_form
        )
        self.clear_btn.grid(row=1, column=1, padx=(4, 0), pady=4, sticky="ew")

        # -----------------------------
        # Right Panel: Search, Table & Controls
        # -----------------------------
        right_panel = ctk.CTkFrame(self, fg_color="transparent")
        right_panel.grid(row=0, column=1, sticky="nsew")
        right_panel.columnconfigure(0, weight=1)
        right_panel.rowconfigure(1, weight=1)

        # Controls Card
        ctrl_card = ctk.CTkFrame(right_panel, corner_radius=12)
        ctrl_card.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        search_row = ctk.CTkFrame(ctrl_card, fg_color="transparent")
        search_row.pack(fill="x", padx=14, pady=(12, 8))

        self.search_entry = ctk.CTkEntry(
            search_row,
            placeholder_text="🔍 Search members by name, email, phone, or ID...",
            font=FONT_BODY,
            height=36,
            corner_radius=8
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.search_entry.bind("<KeyRelease>", lambda _: self.refresh())

        self.status_segment = ctk.CTkSegmentedButton(
            search_row,
            values=["All", "Active", "Warning", "Suspended"],
            height=34,
            corner_radius=8,
            command=lambda _: self.refresh()
        )
        self.status_segment.set("All")
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

        # Sort Row
        sort_row = ctk.CTkFrame(ctrl_card, fg_color="transparent")
        sort_row.pack(fill="x", padx=14, pady=(0, 12))

        ctk.CTkLabel(sort_row, text="Sort by:", font=FONT_SMALL, text_color=("gray40", "gray70")).pack(side="left", padx=(0, 6))

        self.sort_option = ctk.CTkOptionMenu(
            sort_row,
            values=["PatronID", "Name", "MeritScore", "CurrentLoans", "TotalBorrowed"],
            width=140,
            height=30,
            corner_radius=6,
            font=FONT_SMALL,
            command=lambda _: self.refresh()
        )
        self.sort_option.set("MeritScore")
        self.sort_option.pack(side="left", padx=(0, 8))

        self.ascending_order = False  # Default sort by Merit descending
        self.order_btn = ctk.CTkButton(
            sort_row,
            text="▼ Descending",
            font=FONT_SMALL,
            width=100,
            height=30,
            corner_radius=6,
            fg_color=("#F1F5F9", "#27272A"),
            text_color=("#0F172A", "#F8FAFC"),
            hover_color=("#E2E8F0", "#3F3F46"),
            command=self._toggle_sort_order
        )
        self.order_btn.pack(side="left")

        # Table Container
        table_container = ctk.CTkFrame(right_panel, corner_radius=12)
        table_container.grid(row=1, column=0, sticky="nsew")
        table_container.rowconfigure(0, weight=1)
        table_container.columnconfigure(0, weight=1)

        tree_scroll_y = ttk.Scrollbar(table_container, orient="vertical")
        tree_scroll_x = ttk.Scrollbar(table_container, orient="horizontal")

        columns = (
            ("MemberID", "Member ID", 85, "center"),
            ("Name", "Member Name", 160, "w"),
            ("Email", "Email", 170, "w"),
            ("Phone", "Phone", 110, "w"),
            ("MembershipType", "Type", 95, "center"),
            ("MeritScore", "Merit", 70, "center"),
            ("MeritTier", "Merit Standing", 130, "w"),
            ("CurrentLoans", "Active", 60, "center"),
            ("TotalBorrowed", "Lifetime", 65, "center"),
            ("Status", "Status", 85, "center"),
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
            self.tree.heading(col_id, text=heading_text, command=lambda c=col_id: self._sort_by_column(c))
            self.tree.column(col_id, width=width, minwidth=35, anchor=align)

        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)
        self.tree.bind("<Double-1>", self._on_double_click)

        self.count_label = ctk.CTkLabel(
            right_panel,
            text="Showing 0 members",
            font=FONT_SMALL,
            text_color=("gray40", "gray70"),
            anchor="w"
        )
        self.count_label.grid(row=2, column=0, sticky="ew", padx=6, pady=(4, 0))

    def _toggle_sort_order(self) -> None:
        self.ascending_order = not self.ascending_order
        self.order_btn.configure(text="▲ Ascending" if self.ascending_order else "▼ Descending")
        self.refresh()

    def _sort_by_column(self, col: str) -> None:
        if self.sort_option.get() == col:
            self._toggle_sort_order()
        else:
            self.sort_option.set(col)
            self.ascending_order = False
            self.order_btn.configure(text="▼ Descending")
            self.refresh()

    def refresh(self) -> None:
        """Reload patrons table respecting filters and theme."""
        is_dark = ctk.get_appearance_mode() == "Dark"

        # Dynamically set row tag colors
        self.tree.tag_configure("tier_gold", background="#064E3B" if is_dark else "#ECFDF5", foreground="#6EE7B7" if is_dark else "#065F46")
        self.tree.tag_configure("tier_silver", background="#18181B" if is_dark else "#FFFFFF", foreground="#F4F4F5" if is_dark else "#0F172A")
        self.tree.tag_configure("tier_bronze", background="#78350F" if is_dark else "#FEF3C7", foreground="#FDE68A" if is_dark else "#92400E")
        self.tree.tag_configure("tier_suspended", background="#7F1D1D" if is_dark else "#FEE2E2", foreground="#FCA5A5" if is_dark else "#991B1B")

        for item in self.tree.get_children():
            self.tree.delete(item)

        df = self.db.get_patrons(
            search_query=self.search_entry.get(),
            sort_by=self.sort_option.get(),
            ascending=self.ascending_order,
            filter_status=self.status_segment.get()
        )

        for _, row in df.iterrows():
            p_id = row['PatronID']
            m_id = str(row.get('MemberID', f"MEM-{1000 + int(p_id)}"))
            merit = int(row['MeritScore'])
            tier = get_merit_tier(merit)

            if merit >= 120:
                tag = "tier_gold"
            elif merit >= 85:
                tag = "tier_silver"
            elif merit >= 50:
                tag = "tier_bronze"
            else:
                tag = "tier_suspended"

            self.tree.insert(
                "",
                tk.END,
                iid=str(p_id),
                values=(
                    m_id,
                    row['Name'],
                    row['Email'],
                    row['Phone'],
                    row['MembershipType'],
                    merit,
                    tier['badge'],
                    row['CurrentLoans'],
                    row['TotalBorrowed'],
                    row['Status']
                ),
                tags=(tag,)
            )

        total_p = len(self.db.patrons_df)
        self.count_label.configure(text=f"Showing {len(df)} of {total_p} registered members")

    def _on_tree_select(self, event=None) -> None:
        selection = self.tree.selection()
        if not selection:
            return

        p_id = int(selection[0])
        patron = self.db.get_patron_by_id(p_id)
        if not patron:
            return

        self.selected_patron_id = p_id
        m_id = str(patron.get('MemberID', f"MEM-{1000 + p_id}"))
        merit = patron['MeritScore']
        tier = get_merit_tier(merit)

        self.mode_badge.configure(
            text=f"Editing Member {m_id} • Merit: {merit} ({tier['badge']})",
            fg_color=("#FEF3C7", "#78350F"),
            text_color=("#92400E", "#FDE68A")
        )

        self.name_entry.delete(0, tk.END)
        self.name_entry.insert(0, str(patron['Name']))

        self.email_entry.delete(0, tk.END)
        self.email_entry.insert(0, str(patron['Email']))

        phone_val = str(patron.get('Phone', ''))
        raw_digits = re.sub(r"\D", "", phone_val)
        if raw_digits.startswith("91") and len(raw_digits) == 12:
            raw_digits = raw_digits[2:]
        self.phone_entry.delete(0, tk.END)
        self.phone_entry.insert(0, raw_digits[:10])

        if patron['MembershipType'] in MEMBERSHIP_TYPES:
            self.type_menu.set(patron['MembershipType'])

        self.update_btn.configure(state="normal")
        self.adjust_merit_btn.configure(state="normal")

    def _on_phone_key_release(self, event=None) -> None:
        """Strip non-digits and limit input to 10 digits."""
        val = self.phone_entry.get()
        if val.startswith("+91"):
            val = val[3:]
        digits = re.sub(r"\D", "", val)[:10]
        if digits != val:
            self.phone_entry.delete(0, tk.END)
            self.phone_entry.insert(0, digits)

    def _get_formatted_phone(self) -> str:
        """Format 10-digit input into standard '+91 XXXXX XXXXX' string."""
        raw = re.sub(r"\D", "", self.phone_entry.get().strip())
        if not raw:
            return ""
        if len(raw) == 10:
            return f"+91 {raw[:5]} {raw[5:]}"
        return f"+91 {raw}"

    def _on_double_click(self, event=None) -> None:
        selection = self.tree.selection()
        if not selection:
            return
        p_id = int(selection[0])
        patron = self.db.get_patron_by_id(p_id)
        if not patron:
            return

        m_id = str(patron.get('MemberID', f"MEM-{1000 + p_id}"))
        tier = get_merit_tier(patron['MeritScore'])
        info = (
            f"🆔 Member ID: {m_id}\n"
            f"📛 Name: {patron['Name']}\n"
            f"📧 Email: {patron['Email']}\n"
            f"📞 Phone: {patron['Phone']}\n"
            f"🏷️ Type: {patron['MembershipType']}\n\n"
            f"⭐ Merit Score: {patron['MeritScore']} points\n"
            f"🎖️ Standing: {tier['badge']}\n"
            f"📚 Max Concurrent Loans: {tier['max_books']} books\n"
            f"⏱️ Max Loan Period: {tier['max_loan_days']} days\n"
            f"🔄 Currently Borrowed: {patron['CurrentLoans']} books\n"
            f"📦 Lifetime Loans: {patron['TotalBorrowed']} books\n"
            f"📅 Joined: {patron['RegisteredDate']}"
        )
        messagebox.showinfo(f"Patron Profile - [{m_id}] {patron['Name']}", info)

    def clear_form(self) -> None:
        self.selected_patron_id = None
        next_m_id = self.db.get_next_member_id()
        self.mode_badge.configure(
            text=f"✨ Register New Member ({next_m_id}) • 100 Initial Merit",
            fg_color=("#ECFDF5", "#064E3B"),
            text_color=("#047857", "#6EE7B7")
        )
        self.name_entry.delete(0, tk.END)
        self.email_entry.delete(0, tk.END)
        self.phone_entry.delete(0, tk.END)
        self.type_menu.set(MEMBERSHIP_TYPES[0])

        self.update_btn.configure(state="disabled")
        self.adjust_merit_btn.configure(state="disabled")
        self.tree.selection_remove(self.tree.selection())

    def _on_register_patron(self) -> None:
        try:
            name = self.name_entry.get().strip()
            email = self.email_entry.get().strip()
            raw_phone = re.sub(r"\D", "", self.phone_entry.get().strip())
            m_type = self.type_menu.get().strip()

            if not name:
                messagebox.showerror("Validation Error", "Full Name is required.")
                return

            if raw_phone and len(raw_phone) != 10:
                messagebox.showerror("Validation Error", "Please enter a valid 10-digit mobile number.")
                return

            phone = self._get_formatted_phone()

            new_id = self.db.register_patron(
                name=name,
                email=email,
                phone=phone,
                membership_type=m_type,
                initial_merit=INITIAL_MERIT_SCORE
            )
            patron = self.db.get_patron_by_id(new_id)
            m_id = patron['MemberID'] if patron else f"MEM-{1000 + new_id}"

            messagebox.showinfo(
                "Registration Successful",
                f"🎉 Member registered successfully!\n\n"
                f"👤 Name: {name}\n"
                f"🆔 Assigned Member ID: {m_id}\n"
                f"📞 Phone: {phone or 'Not Provided'}\n"
                f"⭐ Initial Merit Awarded: {INITIAL_MERIT_SCORE} Points\n"
                f"🥈 Borrowing Tier: Silver Standard (3 books allowed)\n\n"
                f"Note: This unique Member ID will distinguish them even if other members share the same name."
            )

            self.clear_form()
            self.refresh()
            self.on_change_callback()
        except Exception as e:
            messagebox.showerror("Registration Failed", str(e))

    def _on_update_patron(self) -> None:
        if self.selected_patron_id is None:
            messagebox.showwarning("Warning", "Please select a member to update.")
            return

        try:
            name = self.name_entry.get().strip()
            email = self.email_entry.get().strip()
            raw_phone = re.sub(r"\D", "", self.phone_entry.get().strip())
            m_type = self.type_menu.get().strip()

            if raw_phone and len(raw_phone) != 10:
                messagebox.showerror("Validation Error", "Please enter a valid 10-digit mobile number.")
                return

            phone = self._get_formatted_phone()

            self.db.update_patron(
                patron_id=self.selected_patron_id,
                name=name,
                email=email,
                phone=phone,
                membership_type=m_type
            )

            messagebox.showinfo("Success", f"Member profile #{self.selected_patron_id} updated successfully!")
            self.clear_form()
            self.refresh()
            self.on_change_callback()
        except Exception as e:
            messagebox.showerror("Update Error", str(e))

    def _on_adjust_merit(self) -> None:
        if self.selected_patron_id is None:
            return

        patron = self.db.get_patron_by_id(self.selected_patron_id)
        if not patron:
            return

        delta_str = simpledialog.askstring(
            "Manual Merit Adjustment",
            f"Current Merit for {patron['Name']}: {patron['MeritScore']} points.\n\n"
            "Enter merit adjustment delta (e.g. +10, -15, 20):"
        )
        if delta_str:
            try:
                delta = int(delta_str.replace("+", "").strip())
                new_score = self.db.adjust_patron_merit(self.selected_patron_id, delta)
                tier = get_merit_tier(new_score)
                messagebox.showinfo(
                    "Merit Updated",
                    f"Member: {patron['Name']}\n"
                    f"Merit Adjusted By: {delta:+d}\n"
                    f"New Merit Score: {new_score} Points ({tier['badge']})"
                )
                self.refresh()
                self._on_tree_select()
                self.on_change_callback()
            except ValueError:
                messagebox.showerror("Invalid Input", "Please enter a valid integer for merit adjustment.")

    def _on_export_csv(self) -> None:
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Export Members as CSV"
        )
        if file_path:
            try:
                self.db.export_data_to_csv('patrons', file_path)
                messagebox.showinfo("Export Successful", f"Members directory exported to:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Export Failed", str(e))
