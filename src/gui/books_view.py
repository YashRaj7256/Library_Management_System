"""
Modern Books Management View built with CustomTkinter.
"""
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Callable, Optional
import customtkinter as ctk

from ..database import LibraryDatabase
from ..models import GENRE_CHOICES, STATUS_AVAILABLE, STATUS_CHECKED_OUT
from .styles import (
    COLOR_DANGER,
    COLOR_DANGER_HOVER,
    COLOR_PRIMARY,
    COLOR_PRIMARY_HOVER,
    COLOR_SUCCESS,
    COLOR_SUCCESS_HOVER,
    FONT_BODY,
    FONT_BODY_BOLD,
    FONT_HEADING,
    FONT_SECTION,
    FONT_SMALL,
    FONT_SUBTITLE,
    apply_treeview_row_tags,
)


class BooksView(ctk.CTkFrame):
    """Modern view component for catalog CRUD, search, and sorting."""

    def __init__(self, parent, db: LibraryDatabase, on_change_callback: Callable[[], None]):
        super().__init__(parent, fg_color="transparent")
        self.db = db
        self.on_change_callback = on_change_callback
        self.selected_book_id: Optional[int] = None

        self._create_widgets()
        self.refresh()

    def _create_widgets(self) -> None:
        self.columnconfigure(0, weight=0, minsize=350)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        # -----------------------------
        # Left Panel: Book Form Card
        # -----------------------------
        self.form_card = ctk.CTkFrame(self, corner_radius=12)
        self.form_card.grid(row=0, column=0, sticky="nsew", padx=(0, 12), pady=4)
        self.form_card.columnconfigure(0, weight=1)

        form_title = ctk.CTkLabel(
            self.form_card,
            text="📖 Book Details",
            font=FONT_SUBTITLE,
            anchor="w"
        )
        form_title.pack(fill="x", padx=16, pady=(16, 6))

        self.mode_badge = ctk.CTkLabel(
            self.form_card,
            text="Mode: Adding New Book",
            font=FONT_SMALL,
            fg_color=("#DBEAFE", "#1E3A8A"),
            text_color=("#1E40AF", "#93C5FD"),
            corner_radius=6,
            height=26
        )
        self.mode_badge.pack(fill="x", padx=16, pady=(0, 12))

        # Scrollable form fields
        form_scroll = ctk.CTkScrollableFrame(self.form_card, fg_color="transparent")
        form_scroll.pack(fill="both", expand=True, padx=12, pady=(0, 10))

        self.entries = {}
        fields = [
            ("Book Title *", "title", "entry"),
            ("Author *", "author", "entry"),
            ("ISBN", "isbn", "entry"),
            ("Genre", "genre", "optionmenu"),
            ("Publication Year", "year", "entry"),
            ("Total Copies *", "total_copies", "entry"),
            ("Cost (₹)", "cost", "entry"),
        ]

        for label_text, key, widget_type in fields:
            lbl = ctk.CTkLabel(form_scroll, text=label_text, font=FONT_BODY_BOLD, anchor="w")
            lbl.pack(fill="x", pady=(6, 2))

            if widget_type == "entry":
                entry = ctk.CTkEntry(
                    form_scroll,
                    font=FONT_BODY,
                    height=34,
                    corner_radius=8,
                    placeholder_text=f"Enter {label_text.replace('*', '').strip().lower()}..."
                )
                entry.pack(fill="x", pady=(0, 4))
                self.entries[key] = entry
            elif widget_type == "optionmenu":
                opt = ctk.CTkOptionMenu(
                    form_scroll,
                    values=GENRE_CHOICES,
                    height=34,
                    corner_radius=8,
                    font=FONT_BODY
                )
                opt.set(GENRE_CHOICES[0])
                opt.pack(fill="x", pady=(0, 4))
                self.entries[key] = opt

        # Form Buttons Grid
        btn_frame = ctk.CTkFrame(self.form_card, fg_color="transparent")
        btn_frame.pack(fill="x", padx=16, pady=(0, 16))
        btn_frame.columnconfigure((0, 1), weight=1)

        self.add_btn = ctk.CTkButton(
            btn_frame,
            text="➕ Add Book",
            font=FONT_BODY_BOLD,
            fg_color=COLOR_SUCCESS,
            hover_color=COLOR_SUCCESS_HOVER,
            height=36,
            corner_radius=8,
            command=self._on_add_book
        )
        self.add_btn.grid(row=0, column=0, padx=(0, 4), pady=4, sticky="ew")

        self.update_btn = ctk.CTkButton(
            btn_frame,
            text="✏️ Update",
            font=FONT_BODY_BOLD,
            fg_color=COLOR_PRIMARY,
            hover_color=COLOR_PRIMARY_HOVER,
            height=36,
            corner_radius=8,
            state="disabled",
            command=self._on_update_book
        )
        self.update_btn.grid(row=0, column=1, padx=(4, 0), pady=4, sticky="ew")

        self.delete_btn = ctk.CTkButton(
            btn_frame,
            text="🗑️ Delete",
            font=FONT_BODY_BOLD,
            fg_color=COLOR_DANGER,
            hover_color=COLOR_DANGER_HOVER,
            height=36,
            corner_radius=8,
            state="disabled",
            command=self._on_delete_book
        )
        self.delete_btn.grid(row=1, column=0, padx=(0, 4), pady=4, sticky="ew")

        self.clear_btn = ctk.CTkButton(
            btn_frame,
            text="🔄 Clear",
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
        # Right Panel: Search, Filter & Table
        # -----------------------------
        right_panel = ctk.CTkFrame(self, fg_color="transparent")
        right_panel.grid(row=0, column=1, sticky="nsew")
        right_panel.columnconfigure(0, weight=1)
        right_panel.rowconfigure(1, weight=1)

        # Controls Header Card
        ctrl_card = ctk.CTkFrame(right_panel, corner_radius=12)
        ctrl_card.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        # Search Bar
        search_row = ctk.CTkFrame(ctrl_card, fg_color="transparent")
        search_row.pack(fill="x", padx=14, pady=(12, 8))

        self.search_entry = ctk.CTkEntry(
            search_row,
            placeholder_text="🔍 Search titles, authors, genres, ISBN, or Book ID...",
            font=FONT_BODY,
            height=36,
            corner_radius=8
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.search_entry.bind("<KeyRelease>", lambda _: self.refresh())

        self.status_segment = ctk.CTkSegmentedButton(
            search_row,
            values=["All", STATUS_AVAILABLE, STATUS_CHECKED_OUT],
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
            values=["BookID", "Title", "Author", "Genre", "Year", "AvailableCopies", "Cost"],
            width=140,
            height=30,
            corner_radius=6,
            font=FONT_SMALL,
            command=lambda _: self.refresh()
        )
        self.sort_option.set("BookID")
        self.sort_option.pack(side="left", padx=(0, 8))

        self.ascending_order = True
        self.order_btn = ctk.CTkButton(
            sort_row,
            text="▲ Ascending",
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
            ("BookID", "ID", 50, "center"),
            ("Title", "Title", 190, "w"),
            ("Author", "Author", 140, "w"),
            ("ISBN", "ISBN", 120, "w"),
            ("Genre", "Genre", 100, "w"),
            ("Year", "Year", 60, "center"),
            ("AvailableCopies", "Avail", 60, "center"),
            ("TotalCopies", "Total", 60, "center"),
            ("Status", "Status", 95, "center"),
            ("Cost", "Cost (₹)", 80, "e"),
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
            self.tree.column(col_id, width=width, minwidth=40, anchor=align)

        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)
        self.tree.bind("<Double-1>", self._on_double_click)

        # Status Bar / Count label
        self.count_label = ctk.CTkLabel(
            right_panel,
            text="Showing 0 books",
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
            self.ascending_order = True
            self.order_btn.configure(text="▲ Ascending")
            self.refresh()

    def refresh(self) -> None:
        """Reload books table respecting search, filter, and sort."""
        # Dynamically apply tag colors for current mode (Light/Dark)
        apply_treeview_row_tags(self.tree, "books", ctk.get_appearance_mode())

        for item in self.tree.get_children():
            self.tree.delete(item)

        is_dark = ctk.get_appearance_mode() == "Dark"

        df = self.db.get_books(
            search_query=self.search_entry.get(),
            sort_by=self.sort_option.get(),
            ascending=self.ascending_order,
            filter_status=self.status_segment.get()
        )

        for i, (_, row) in enumerate(df.iterrows()):
            b_id = row['BookID']
            avail = row['AvailableCopies']
            cost_str = f"{row['Cost']:.2f}" if row['Cost'] > 0 else "0.00"

            tag = "unavailable" if avail == 0 else ("evenrow" if i % 2 == 0 else "oddrow")

            self.tree.insert(
                "",
                tk.END,
                iid=str(b_id),
                values=(
                    b_id,
                    row['Title'],
                    row['Author'],
                    row['ISBN'],
                    row['Genre'],
                    row['Year'] if row['Year'] > 0 else "-",
                    avail,
                    row['TotalCopies'],
                    row['Status'],
                    cost_str
                ),
                tags=(tag,)
            )

        total_in_db = len(self.db.books_df)
        self.count_label.configure(text=f"Showing {len(df)} of {total_in_db} catalog titles")

    def _on_tree_select(self, event=None) -> None:
        selection = self.tree.selection()
        if not selection:
            return

        book_id = int(selection[0])
        book = self.db.get_book_by_id(book_id)
        if not book:
            return

        self.selected_book_id = book_id
        self.mode_badge.configure(
            text=f"Editing Book ID #{book_id}",
            fg_color=("#FEF3C7", "#78350F"),
            text_color=("#92400E", "#FDE68A")
        )

        # Populate form
        self.entries['title'].delete(0, tk.END)
        self.entries['title'].insert(0, str(book['Title']))

        self.entries['author'].delete(0, tk.END)
        self.entries['author'].insert(0, str(book['Author']))

        self.entries['isbn'].delete(0, tk.END)
        self.entries['isbn'].insert(0, str(book['ISBN']))

        if book['Genre'] in GENRE_CHOICES:
            self.entries['genre'].set(book['Genre'])
        else:
            self.entries['genre'].set("Other")

        self.entries['year'].delete(0, tk.END)
        self.entries['year'].insert(0, str(book['Year']) if book['Year'] > 0 else "")

        self.entries['total_copies'].delete(0, tk.END)
        self.entries['total_copies'].insert(0, str(book['TotalCopies']))

        self.entries['cost'].delete(0, tk.END)
        self.entries['cost'].insert(0, str(book['Cost']) if book['Cost'] > 0 else "")

        self.update_btn.configure(state="normal")
        self.delete_btn.configure(state="normal")

    def _on_double_click(self, event=None) -> None:
        selection = self.tree.selection()
        if not selection:
            return
        book_id = int(selection[0])
        book = self.db.get_book_by_id(book_id)
        if not book:
            return

        details = (
            f"📚 Title: {book['Title']}\n"
            f"✍️ Author: {book['Author']}\n"
            f"🔢 ISBN: {book['ISBN'] or 'N/A'}\n"
            f"🏷️ Genre: {book['Genre']}\n"
            f"📅 Year: {book['Year'] or 'N/A'}\n"
            f"📦 Inventory: {book['AvailableCopies']} available of {book['TotalCopies']} total\n"
            f"📌 Status: {book['Status']}\n"
            f"💵 Cost: ₹{book['Cost']:.2f}\n"
            f"🕒 Added: {book['AddedDate']}"
        )
        messagebox.showinfo(f"Book Details - ID #{book_id}", details)

    def clear_form(self) -> None:
        self.selected_book_id = None
        self.mode_badge.configure(
            text="Mode: Adding New Book",
            fg_color=("#DBEAFE", "#1E3A8A"),
            text_color=("#1E40AF", "#93C5FD")
        )

        for key, widget in self.entries.items():
            if isinstance(widget, ctk.CTkOptionMenu):
                widget.set(GENRE_CHOICES[0])
            else:
                widget.delete(0, tk.END)

        self.update_btn.configure(state="disabled")
        self.delete_btn.configure(state="disabled")
        self.tree.selection_remove(self.tree.selection())

    def _on_add_book(self) -> None:
        try:
            title = self.entries['title'].get().strip()
            author = self.entries['author'].get().strip()
            isbn = self.entries['isbn'].get().strip()
            genre = self.entries['genre'].get().strip()
            year_str = self.entries['year'].get().strip()
            copies_str = self.entries['total_copies'].get().strip()
            cost_str = self.entries['cost'].get().strip()

            if not title or not author:
                messagebox.showerror("Validation Error", "Title and Author are required fields.")
                return

            year = int(year_str) if year_str.isdigit() else 0
            total_copies = int(copies_str) if copies_str.isdigit() else 1
            cost = float(cost_str) if cost_str.replace('.', '', 1).isdigit() else 0.0

            new_id = self.db.add_book(
                title=title,
                author=author,
                isbn=isbn,
                genre=genre,
                year=year,
                total_copies=total_copies,
                cost=cost
            )

            messagebox.showinfo("Success", f"Book '{title}' added successfully with ID #{new_id}!")
            self.clear_form()
            self.refresh()
            self.on_change_callback()
        except Exception as e:
            messagebox.showerror("Error Adding Book", str(e))

    def _on_update_book(self) -> None:
        if self.selected_book_id is None:
            messagebox.showwarning("Warning", "Please select a book to update.")
            return

        try:
            title = self.entries['title'].get().strip()
            author = self.entries['author'].get().strip()
            isbn = self.entries['isbn'].get().strip()
            genre = self.entries['genre'].get().strip()
            year_str = self.entries['year'].get().strip()
            copies_str = self.entries['total_copies'].get().strip()
            cost_str = self.entries['cost'].get().strip()

            year = int(year_str) if year_str.isdigit() else 0
            total_copies = int(copies_str) if copies_str.isdigit() else 1
            cost = float(cost_str) if cost_str.replace('.', '', 1).isdigit() else 0.0

            self.db.update_book(
                book_id=self.selected_book_id,
                title=title,
                author=author,
                isbn=isbn,
                genre=genre,
                year=year,
                total_copies=total_copies,
                cost=cost
            )

            messagebox.showinfo("Success", f"Book ID #{self.selected_book_id} updated successfully!")
            self.clear_form()
            self.refresh()
            self.on_change_callback()
        except Exception as e:
            messagebox.showerror("Error Updating Book", str(e))

    def _on_delete_book(self) -> None:
        if self.selected_book_id is None:
            messagebox.showwarning("Warning", "Please select a book to delete.")
            return

        confirm = messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to permanently delete Book ID #{self.selected_book_id}?\n\n"
            "This action cannot be undone."
        )
        if not confirm:
            return

        try:
            self.db.delete_book(self.selected_book_id)
            messagebox.showinfo("Success", f"Book ID #{self.selected_book_id} has been removed.")
            self.clear_form()
            self.refresh()
            self.on_change_callback()
        except Exception as e:
            messagebox.showerror("Delete Error", str(e))

    def _on_export_csv(self) -> None:
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Export Books Catalog as CSV"
        )
        if file_path:
            try:
                self.db.export_data_to_csv('books', file_path)
                messagebox.showinfo("Export Successful", f"Books catalog exported to:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Export Failed", str(e))
