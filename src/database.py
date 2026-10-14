"""
Database layer managing Excel-based data persistence with Pandas & OpenPyXL.
"""
from datetime import datetime, date
import os
from pathlib import Path
import re
from typing import Dict, List, Optional, Tuple, Any

import pandas as pd

from .models import (
    DEFAULT_FINE_PER_DAY,
    DEFAULT_LOAN_DAYS,
    STATUS_AVAILABLE,
    STATUS_CHECKED_OUT,
    TRANS_STATUS_ISSUED,
    TRANS_STATUS_RETURNED,
)


class LibraryDatabase:
    """Manages Excel storage and in-memory DataFrames for books and transactions."""

    def __init__(self, excel_path: Optional[str] = None):
        if excel_path is None:
            # Default to library_system.xlsx located in project root
            base_dir = Path(__file__).resolve().parent.parent
            self.excel_file = str(base_dir / "library_system.xlsx")
        else:
            self.excel_file = str(Path(excel_path).resolve())

        self.books_df: pd.DataFrame = pd.DataFrame()
        self.transactions_df: pd.DataFrame = pd.DataFrame()
        self.is_dirty: bool = False  # Track unsaved changes
        self.last_saved_time: Optional[str] = None

        self.initialize_and_load()

    def initialize_and_load(self) -> None:
        """Initialize Excel structure if missing, then load data."""
        if not os.path.exists(self.excel_file):
            self._create_initial_excel_file()
        self.load_data()

    def _create_initial_excel_file(self) -> None:
        """Create a new Excel file populated with starter book catalog."""
        books_data = {
            'BookID': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            'Title': [
                'The Great Gatsby', 'To Kill a Mockingbird', '1984',
                'Pride and Prejudice', 'The Hobbit', 'The Lord of the Rings',
                "Harry Potter and the Philosopher's Stone", 'The Catcher in the Rye',
                'The Da Vinci Code', 'The Alchemist'
            ],
            'Author': [
                'F. Scott Fitzgerald', 'Harper Lee', 'George Orwell',
                'Jane Austen', 'J.R.R. Tolkien', 'J.R.R. Tolkien',
                'J.K. Rowling', 'J.D. Salinger', 'Dan Brown', 'Paulo Coelho'
            ],
            'ISBN': [
                '978-0-7432-7356-5', '978-0-06-112008-4', '978-0-452-28423-4',
                '978-0-14-143951-8', '978-0-547-92822-7', '978-0-618-64015-7',
                '978-0-7475-3269-9', '978-0-316-76948-0', '978-0-385-50420-5', '978-0-06-112241-5'
            ],
            'Genre': [
                'Fiction', 'Fiction', 'Dystopian', 'Romance', 'Fantasy', 'Fantasy',
                'Fantasy', 'Fiction', 'Mystery', 'Adventure'
            ],
            'Year': [1925, 1960, 1949, 1813, 1937, 1954, 1997, 1951, 2003, 1988],
            'AddedDate': [datetime.now().strftime("%Y-%m-%d")] * 10,
            'TotalCopies': [3, 2, 4, 3, 5, 3, 6, 2, 4, 3],
            'AvailableCopies': [3, 2, 4, 3, 5, 3, 6, 2, 4, 3],
            'Status': [STATUS_AVAILABLE] * 10,
            'Cost': [350.00, 299.00, 399.00, 250.00, 450.00, 599.00, 499.00, 290.00, 380.00, 320.00]
        }

        transactions_data = {
            'TransactionID': [],
            'BookID': [],
            'CustomerName': [],
            'CustomerEmail': [],
            'IssueDate': [],
            'DueDate': [],
            'ReturnDate': [],
            'FineAmount': [],
            'Status': []
        }

        self.books_df = pd.DataFrame(books_data)
        self.transactions_df = pd.DataFrame(transactions_data)
        self.save_data()

    def load_data(self) -> None:
        """Load books and transactions from Excel with type normalization."""
        try:
            with pd.ExcelFile(self.excel_file) as excel:
                # Load Books sheet
                if 'Books' in excel.sheet_names:
                    self.books_df = pd.read_excel(excel, sheet_name='Books')
                else:
                    self.books_df = pd.DataFrame()

                # Load Transactions sheet
                if 'Transactions' in excel.sheet_names:
                    self.transactions_df = pd.read_excel(excel, sheet_name='Transactions')
                else:
                    self.transactions_df = pd.DataFrame()

            # Ensure columns exist
            expected_book_cols = [
                'BookID', 'Title', 'Author', 'ISBN', 'Genre', 'Year',
                'AddedDate', 'TotalCopies', 'AvailableCopies', 'Status', 'Cost'
            ]
            for col in expected_book_cols:
                if col not in self.books_df.columns:
                    self.books_df[col] = []

            expected_trans_cols = [
                'TransactionID', 'BookID', 'CustomerName', 'CustomerEmail',
                'IssueDate', 'DueDate', 'ReturnDate', 'FineAmount', 'Status'
            ]
            for col in expected_trans_cols:
                if col not in self.transactions_df.columns:
                    self.transactions_df[col] = []

            # Normalize data types
            if not self.books_df.empty:
                self.books_df['BookID'] = pd.to_numeric(self.books_df['BookID'], errors='coerce').fillna(0).astype(int)
                self.books_df['Year'] = pd.to_numeric(self.books_df['Year'], errors='coerce').fillna(0).astype(int)
                self.books_df['TotalCopies'] = pd.to_numeric(self.books_df['TotalCopies'], errors='coerce').fillna(1).astype(int)
                self.books_df['AvailableCopies'] = pd.to_numeric(self.books_df['AvailableCopies'], errors='coerce').fillna(0).astype(int)
                self.books_df['Cost'] = pd.to_numeric(self.books_df['Cost'], errors='coerce').fillna(0.0).astype(float)
                self.books_df['Title'] = self.books_df['Title'].fillna('').astype(str)
                self.books_df['Author'] = self.books_df['Author'].fillna('').astype(str)
                self.books_df['ISBN'] = self.books_df['ISBN'].fillna('').astype(str)
                self.books_df['Genre'] = self.books_df['Genre'].fillna('Other').astype(str)
                self.books_df['Status'] = self.books_df['Status'].fillna(STATUS_AVAILABLE).astype(str)

            if not self.transactions_df.empty:
                self.transactions_df['TransactionID'] = pd.to_numeric(self.transactions_df['TransactionID'], errors='coerce').fillna(0).astype(int)
                self.transactions_df['BookID'] = pd.to_numeric(self.transactions_df['BookID'], errors='coerce').fillna(0).astype(int)
                self.transactions_df['FineAmount'] = pd.to_numeric(self.transactions_df['FineAmount'], errors='coerce').fillna(0.0).astype(float)
                self.transactions_df['CustomerName'] = self.transactions_df['CustomerName'].fillna('').astype(str)
                self.transactions_df['CustomerEmail'] = self.transactions_df['CustomerEmail'].fillna('').astype(str)
                self.transactions_df['Status'] = self.transactions_df['Status'].fillna(TRANS_STATUS_ISSUED).astype(str)
                # Normalize dates to string YYYY-MM-DD
                for d_col in ['IssueDate', 'DueDate', 'ReturnDate']:
                    if d_col in self.transactions_df.columns:
                        self.transactions_df[d_col] = self.transactions_df[d_col].apply(self._format_date_val)

            self.is_dirty = False
            self.last_saved_time = datetime.now().strftime("%H:%M:%S")

        except Exception as e:
            raise RuntimeError(f"Failed to load Excel data from {self.excel_file}: {e}")

    def _format_date_val(self, val: Any) -> str:
        """Format a date or timestamp value to clean YYYY-MM-DD string."""
        if pd.isna(val) or val is None or str(val).strip().lower() in ('nat', 'nan', ''):
            return ''
        if isinstance(val, (datetime, date, pd.Timestamp)):
            return val.strftime('%Y-%m-%d')
        # Attempt parsing string
        val_str = str(val).strip()
        try:
            parsed = pd.to_datetime(val_str)
            return parsed.strftime('%Y-%m-%d')
        except Exception:
            return val_str

    def save_data(self) -> None:
        """Write current DataFrames to Excel file."""
        try:
            with pd.ExcelWriter(self.excel_file, engine='openpyxl') as writer:
                self.books_df.to_excel(writer, sheet_name='Books', index=False)
                self.transactions_df.to_excel(writer, sheet_name='Transactions', index=False)

            self.is_dirty = False
            self.last_saved_time = datetime.now().strftime("%H:%M:%S")
        except Exception as e:
            raise RuntimeError(f"Failed to save data to Excel: {e}")

    # ==========================
    # Book Operations
    # ==========================
    def add_book(
        self,
        title: str,
        author: str,
        isbn: str = "",
        genre: str = "Fiction",
        year: int = 0,
        total_copies: int = 1,
        cost: float = 0.0
    ) -> int:
        """Add a new book record and return the generated BookID."""
        title = title.strip()
        author = author.strip()
        if not title:
            raise ValueError("Book title cannot be empty.")
        if not author:
            raise ValueError("Author cannot be empty.")
        if total_copies < 1:
            raise ValueError("Total copies must be at least 1.")

        new_id = (self.books_df['BookID'].max() + 1) if not self.books_df.empty else 1

        new_book = {
            'BookID': int(new_id),
            'Title': title,
            'Author': author,
            'ISBN': isbn.strip(),
            'Genre': genre.strip() or 'Other',
            'Year': int(year),
            'AddedDate': datetime.now().strftime("%Y-%m-%d"),
            'TotalCopies': int(total_copies),
            'AvailableCopies': int(total_copies),
            'Status': STATUS_AVAILABLE,
            'Cost': float(cost)
        }

        new_row_df = pd.DataFrame([new_book])
        if self.books_df.empty:
            self.books_df = new_row_df
        else:
            self.books_df = pd.concat([self.books_df, new_row_df], ignore_index=True)

        self.is_dirty = True
        return int(new_id)

    def update_book(
        self,
        book_id: int,
        title: Optional[str] = None,
        author: Optional[str] = None,
        isbn: Optional[str] = None,
        genre: Optional[str] = None,
        year: Optional[int] = None,
        total_copies: Optional[int] = None,
        cost: Optional[float] = None
    ) -> bool:
        """Update fields for an existing book."""
        idx = self.books_df.index[self.books_df['BookID'] == book_id].tolist()
        if not idx:
            raise ValueError(f"Book with ID {book_id} not found.")

        row_idx = idx[0]

        if title is not None and title.strip():
            self.books_df.at[row_idx, 'Title'] = title.strip()
        if author is not None and author.strip():
            self.books_df.at[row_idx, 'Author'] = author.strip()
        if isbn is not None:
            self.books_df.at[row_idx, 'ISBN'] = isbn.strip()
        if genre is not None and genre.strip():
            self.books_df.at[row_idx, 'Genre'] = genre.strip()
        if year is not None:
            self.books_df.at[row_idx, 'Year'] = int(year)
        if cost is not None:
            self.books_df.at[row_idx, 'Cost'] = max(0.0, float(cost))

        if total_copies is not None:
            new_total = int(total_copies)
            current_total = int(self.books_df.at[row_idx, 'TotalCopies'])
            current_avail = int(self.books_df.at[row_idx, 'AvailableCopies'])
            issued_copies = current_total - current_avail

            if new_total < issued_copies:
                raise ValueError(
                    f"Cannot set total copies to {new_total}. "
                    f"{issued_copies} copies are currently issued to patrons."
                )

            diff = new_total - current_total
            new_avail = max(0, current_avail + diff)
            self.books_df.at[row_idx, 'TotalCopies'] = new_total
            self.books_df.at[row_idx, 'AvailableCopies'] = new_avail
            self.books_df.at[row_idx, 'Status'] = STATUS_AVAILABLE if new_avail > 0 else STATUS_CHECKED_OUT

        self.is_dirty = True
        return True

    def delete_book(self, book_id: int) -> bool:
        """Delete a book record if there are no active issued copies."""
        idx = self.books_df.index[self.books_df['BookID'] == book_id].tolist()
        if not idx:
            raise ValueError(f"Book with ID {book_id} not found.")

        # Check for active transactions
        if not self.transactions_df.empty:
            active_loans = self.transactions_df[
                (self.transactions_df['BookID'] == book_id) &
                (self.transactions_df['Status'] == TRANS_STATUS_ISSUED)
            ]
            if not active_loans.empty:
                raise ValueError(
                    f"Cannot delete Book ID {book_id}: "
                    f"{len(active_loans)} copies are currently issued."
                )

        self.books_df = self.books_df[self.books_df['BookID'] != book_id].reset_index(drop=True)
        self.is_dirty = True
        return True

    def get_books(
        self,
        search_query: Optional[str] = None,
        sort_by: Optional[str] = None,
        ascending: bool = True,
        filter_status: Optional[str] = None
    ) -> pd.DataFrame:
        """Return a filtered and sorted copy of books DataFrame."""
        if self.books_df.empty:
            return pd.DataFrame()

        df = self.books_df.copy()

        # Status filter
        if filter_status and filter_status != "All":
            df = df[df['Status'] == filter_status]

        # Search query
        if search_query:
            term = str(search_query).strip().lower()
            if term:
                mask = (
                    df['Title'].astype(str).str.lower().str.contains(term, na=False) |
                    df['Author'].astype(str).str.lower().str.contains(term, na=False) |
                    df['Genre'].astype(str).str.lower().str.contains(term, na=False) |
                    df['ISBN'].astype(str).str.lower().str.contains(term, na=False) |
                    df['BookID'].astype(str).str.contains(term, na=False)
                )
                df = df[mask]

        # Sorting
        if sort_by and sort_by in df.columns:
            if sort_by in ('Cost', 'Year', 'BookID', 'TotalCopies', 'AvailableCopies'):
                df = df.sort_values(sort_by, ascending=ascending)
            else:
                df = df.sort_values(
                    sort_by,
                    ascending=ascending,
                    key=lambda s: s.astype(str).str.lower()
                )

        return df

    def get_book_by_id(self, book_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve a book as a dictionary by BookID."""
        match = self.books_df[self.books_df['BookID'] == book_id]
        if match.empty:
            return None
        return match.iloc[0].to_dict()

    # ==========================
    # Transaction Operations
    # ==========================
    def issue_book(
        self,
        book_id: int,
        customer_name: str,
        customer_email: str = "",
        loan_days: int = DEFAULT_LOAN_DAYS
    ) -> Dict[str, Any]:
        """Issue a book to a customer, returning transaction details."""
        customer_name = customer_name.strip()
        if not customer_name:
            raise ValueError("Customer name is required.")

        idx = self.books_df.index[self.books_df['BookID'] == book_id].tolist()
        if not idx:
            raise ValueError(f"Book with ID {book_id} not found.")

        row_idx = idx[0]
        avail = int(self.books_df.at[row_idx, 'AvailableCopies'])
        if avail <= 0:
            raise ValueError(f"Book '{self.books_df.at[row_idx, 'Title']}' has 0 available copies.")

        # Update available copies
        new_avail = avail - 1
        self.books_df.at[row_idx, 'AvailableCopies'] = new_avail
        if new_avail == 0:
            self.books_df.at[row_idx, 'Status'] = STATUS_CHECKED_OUT

        # Generate TransactionID
        new_trans_id = (self.transactions_df['TransactionID'].max() + 1) if not self.transactions_df.empty else 1

        issue_dt = datetime.now()
        due_dt = issue_dt + pd.Timedelta(days=max(1, loan_days))

        new_trans = {
            'TransactionID': int(new_trans_id),
            'BookID': int(book_id),
            'CustomerName': customer_name,
            'CustomerEmail': customer_email.strip(),
            'IssueDate': issue_dt.strftime("%Y-%m-%d"),
            'DueDate': due_dt.strftime("%Y-%m-%d"),
            'ReturnDate': '',
            'FineAmount': 0.0,
            'Status': TRANS_STATUS_ISSUED
        }

        new_row_df = pd.DataFrame([new_trans])
        if self.transactions_df.empty:
            self.transactions_df = new_row_df
        else:
            self.transactions_df = pd.concat([self.transactions_df, new_row_df], ignore_index=True)

        self.is_dirty = True

        return {
            'transaction_id': new_trans_id,
            'book_title': self.books_df.at[row_idx, 'Title'],
            'customer_name': customer_name,
            'due_date': due_dt.strftime("%Y-%m-%d")
        }

    def return_book(
        self,
        transaction_id: Optional[int] = None,
        book_id: Optional[int] = None,
        customer_name: Optional[str] = None,
        fine_per_day: float = DEFAULT_FINE_PER_DAY
    ) -> Dict[str, Any]:
        """
        Return an issued book, calculate overdue fine automatically.
        Can look up by transaction_id OR by book_id + optional customer_name.
        """
        if self.transactions_df.empty:
            raise ValueError("No transaction records found.")

        trans_idx = None
        if transaction_id is not None:
            matches = self.transactions_df.index[
                (self.transactions_df['TransactionID'] == transaction_id) &
                (self.transactions_df['Status'] == TRANS_STATUS_ISSUED)
            ].tolist()
            if matches:
                trans_idx = matches[0]
            else:
                raise ValueError(f"No active loan found for Transaction ID {transaction_id}.")
        elif book_id is not None:
            query = (self.transactions_df['BookID'] == book_id) & (self.transactions_df['Status'] == TRANS_STATUS_ISSUED)
            if customer_name and customer_name.strip():
                query = query & (self.transactions_df['CustomerName'].str.lower() == customer_name.strip().lower())
            matches = self.transactions_df.index[query].tolist()
            if matches:
                trans_idx = matches[0]
            else:
                raise ValueError(f"No active loan found for Book ID {book_id}.")
        else:
            raise ValueError("Either transaction_id or book_id must be provided.")

        # Extract transaction info
        actual_trans_id = int(self.transactions_df.at[trans_idx, 'TransactionID'])
        b_id = int(self.transactions_df.at[trans_idx, 'BookID'])
        cust_name = str(self.transactions_df.at[trans_idx, 'CustomerName'])
        due_date_str = str(self.transactions_df.at[trans_idx, 'DueDate'])
        today_str = datetime.now().strftime("%Y-%m-%d")

        # Calculate overdue days & fine
        overdue_days = self.calculate_overdue_days(due_date_str, today_str)
        fine_amount = round(overdue_days * max(0.0, fine_per_day), 2)

        # Update transaction
        self.transactions_df.at[trans_idx, 'ReturnDate'] = today_str
        self.transactions_df.at[trans_idx, 'FineAmount'] = fine_amount
        self.transactions_df.at[trans_idx, 'Status'] = TRANS_STATUS_RETURNED

        # Update book availability
        b_indices = self.books_df.index[self.books_df['BookID'] == b_id].tolist()
        book_title = "Unknown"
        if b_indices:
            b_row = b_indices[0]
            book_title = str(self.books_df.at[b_row, 'Title'])
            self.books_df.at[b_row, 'AvailableCopies'] += 1
            self.books_df.at[b_row, 'Status'] = STATUS_AVAILABLE

        self.is_dirty = True

        return {
            'transaction_id': actual_trans_id,
            'book_id': b_id,
            'book_title': book_title,
            'customer_name': cust_name,
            'due_date': due_date_str,
            'return_date': today_str,
            'overdue_days': overdue_days,
            'fine_amount': fine_amount
        }

    @staticmethod
    def calculate_overdue_days(due_date_str: str, ref_date_str: Optional[str] = None) -> int:
        """Calculate number of days past due. Returns 0 if not overdue."""
        try:
            due_dt = pd.to_datetime(due_date_str).date()
            if ref_date_str:
                ref_dt = pd.to_datetime(ref_date_str).date()
            else:
                ref_dt = datetime.now().date()
            diff = (ref_dt - due_dt).days
            return max(0, diff)
        except Exception:
            return 0

    def get_transactions(
        self,
        filter_status: Optional[str] = None,
        search_query: Optional[str] = None
    ) -> pd.DataFrame:
        """Return transactions merged with Book titles for rich viewing."""
        if self.transactions_df.empty:
            return pd.DataFrame()

        df = self.transactions_df.copy()

        # Merge with book title
        if not self.books_df.empty:
            title_map = dict(zip(self.books_df['BookID'], self.books_df['Title']))
            df['BookTitle'] = df['BookID'].map(title_map).fillna('Deleted / Unknown')
        else:
            df['BookTitle'] = 'Unknown'

        # Filter status
        if filter_status == 'Issued' or filter_status == 'Active':
            df = df[df['Status'] == TRANS_STATUS_ISSUED]
        elif filter_status == 'Returned':
            df = df[df['Status'] == TRANS_STATUS_RETURNED]
        elif filter_status == 'Overdue':
            # Check issued items where due date < today
            today_str = datetime.now().strftime("%Y-%m-%d")
            overdue_mask = (df['Status'] == TRANS_STATUS_ISSUED) & (df['DueDate'] < today_str)
            df = df[overdue_mask]

        # Search query
        if search_query:
            term = str(search_query).strip().lower()
            if term:
                mask = (
                    df['CustomerName'].astype(str).str.lower().str.contains(term, na=False) |
                    df['CustomerEmail'].astype(str).str.lower().str.contains(term, na=False) |
                    df['BookTitle'].astype(str).str.lower().str.contains(term, na=False) |
                    df['BookID'].astype(str).str.contains(term, na=False) |
                    df['TransactionID'].astype(str).str.contains(term, na=False)
                )
                df = df[mask]

        return df.sort_values('TransactionID', ascending=False)

    # ==========================
    # Analytics & Summary
    # ==========================
    def get_statistics(self) -> Dict[str, Any]:
        """Aggregate key performance indicators across catalog and loans."""
        total_titles = len(self.books_df)
        total_copies = int(self.books_df['TotalCopies'].sum()) if total_titles > 0 else 0
        available_copies = int(self.books_df['AvailableCopies'].sum()) if total_titles > 0 else 0
        checked_out_copies = max(0, total_copies - available_copies)

        total_transactions = len(self.transactions_df)
        if total_transactions > 0:
            active_loans = len(self.transactions_df[self.transactions_df['Status'] == TRANS_STATUS_ISSUED])
            today_str = datetime.now().strftime("%Y-%m-%d")
            overdue_loans = len(self.transactions_df[
                (self.transactions_df['Status'] == TRANS_STATUS_ISSUED) &
                (self.transactions_df['DueDate'] < today_str)
            ])
            total_fines = float(self.transactions_df['FineAmount'].sum())
        else:
            active_loans = 0
            overdue_loans = 0
            total_fines = 0.0

        return {
            'total_titles': total_titles,
            'total_copies': total_copies,
            'available_copies': available_copies,
            'checked_out_copies': checked_out_copies,
            'total_transactions': total_transactions,
            'active_loans': active_loans,
            'overdue_loans': overdue_loans,
            'total_fines': round(total_fines, 2)
        }

    def get_genre_distribution(self) -> List[Tuple[str, int]]:
        """Return genre breakdown as (genre_name, count) sorted descending."""
        if self.books_df.empty or 'Genre' not in self.books_df.columns:
            return []
        counts = self.books_df['Genre'].value_counts()
        return [(str(genre), int(count)) for genre, count in counts.items()]

    def export_data_to_csv(self, sheet_type: str, export_path: str) -> None:
        """Export either 'books' or 'transactions' to a standalone CSV."""
        if sheet_type.lower() == 'books':
            self.books_df.to_csv(export_path, index=False)
        elif sheet_type.lower() == 'transactions':
            self.transactions_df.to_csv(export_path, index=False)
        else:
            raise ValueError(f"Unknown export sheet type: {sheet_type}")
