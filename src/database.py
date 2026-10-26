"""
Database layer managing Excel-based data persistence with Pandas & OpenPyXL.
Includes full support for Books, Loans, Patrons, and the User Merit System.
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
    INITIAL_MERIT_SCORE,
    ON_TIME_MERIT_BONUS,
    OVERDUE_PENALTY_PER_DAY,
    STATUS_AVAILABLE,
    STATUS_CHECKED_OUT,
    TRANS_STATUS_ISSUED,
    TRANS_STATUS_RETURNED,
    get_merit_tier,
)


def format_member_id(patron_id: Any) -> str:
    """Format an ID into a standard Member ID (e.g. 1 -> MEM-1001, 1001 -> MEM-1001)."""
    try:
        clean_num = int(re.sub(r"[^\d]", "", str(patron_id)))
        if clean_num >= 1000:
            return f"MEM-{clean_num}"
        return f"MEM-{1000 + clean_num}"
    except Exception:
        return f"MEM-{patron_id}"


class LibraryDatabase:
    """Manages Excel storage and DataFrames for books, transactions, and patrons."""

    def __init__(self, excel_path: Optional[str] = None):
        if excel_path is None:
            base_dir = Path(__file__).resolve().parent.parent
            self.excel_file = str(base_dir / "library_system.xlsx")
        else:
            self.excel_file = str(Path(excel_path).resolve())

        self.books_df: pd.DataFrame = pd.DataFrame()
        self.transactions_df: pd.DataFrame = pd.DataFrame()
        self.patrons_df: pd.DataFrame = pd.DataFrame()
        self.is_dirty: bool = False
        self.last_saved_time: Optional[str] = None

        self.initialize_and_load()

    def initialize_and_load(self) -> None:
        """Initialize Excel structure if missing, then load data."""
        if not os.path.exists(self.excel_file):
            self._create_initial_excel_file()
        self.load_data()

    def _create_initial_excel_file(self) -> None:
        """Create a new Excel file populated with starter book catalog and patrons."""
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
            'MemberID': [],
            'CustomerName': [],
            'CustomerEmail': [],
            'IssueDate': [],
            'DueDate': [],
            'ReturnDate': [],
            'FineAmount': [],
            'Status': []
        }

        patrons_data = {
            'MemberID': ['MEM-1001', 'MEM-1002'],
            'PatronID': [1, 2],
            'Name': ['Alice Johnson', 'Bob Wilson'],
            'Email': ['alice.j@email.com', 'bob.w@email.com'],
            'Phone': ['+91 98765 43210', '+91 98765 43211'],
            'MembershipType': ['Student', 'Faculty'],
            'MeritScore': [100, 100],
            'TotalBorrowed': [0, 0],
            'CurrentLoans': [0, 0],
            'Status': ['Active', 'Active'],
            'RegisteredDate': [datetime.now().strftime("%Y-%m-%d")] * 2
        }

        self.books_df = pd.DataFrame(books_data)
        self.transactions_df = pd.DataFrame(transactions_data)
        self.patrons_df = pd.DataFrame(patrons_data)
        self.save_data()

    def load_data(self) -> None:
        """Load books, transactions, and patrons from Excel with schema enforcement."""
        try:
            with pd.ExcelFile(self.excel_file) as excel:
                # 1. Books
                if 'Books' in excel.sheet_names:
                    self.books_df = pd.read_excel(excel, sheet_name='Books')
                else:
                    self.books_df = pd.DataFrame()

                # 2. Transactions
                if 'Transactions' in excel.sheet_names:
                    self.transactions_df = pd.read_excel(excel, sheet_name='Transactions')
                else:
                    self.transactions_df = pd.DataFrame()

                # 3. Patrons
                if 'Patrons' in excel.sheet_names:
                    self.patrons_df = pd.read_excel(excel, sheet_name='Patrons')
                else:
                    self.patrons_df = pd.DataFrame()

            # Ensure expected columns exist
            expected_book_cols = [
                'BookID', 'Title', 'Author', 'ISBN', 'Genre', 'Year',
                'AddedDate', 'TotalCopies', 'AvailableCopies', 'Status', 'Cost'
            ]
            for col in expected_book_cols:
                if col not in self.books_df.columns:
                    self.books_df[col] = []

            expected_trans_cols = [
                'TransactionID', 'BookID', 'MemberID', 'CustomerName', 'CustomerEmail',
                'IssueDate', 'DueDate', 'ReturnDate', 'FineAmount', 'Status'
            ]
            for col in expected_trans_cols:
                if col not in self.transactions_df.columns:
                    self.transactions_df[col] = []

            expected_patron_cols = [
                'MemberID', 'PatronID', 'Name', 'Email', 'Phone', 'MembershipType',
                'MeritScore', 'TotalBorrowed', 'CurrentLoans', 'Status', 'RegisteredDate'
            ]
            for col in expected_patron_cols:
                if col not in self.patrons_df.columns:
                    self.patrons_df[col] = []

            # Normalize books
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

            # Seed Patrons if empty or not present before normalizing transactions
            if self.patrons_df.empty and not self.transactions_df.empty:
                self._seed_patrons_from_transactions()

            # Normalize patrons
            if not self.patrons_df.empty:
                self.patrons_df['PatronID'] = pd.to_numeric(self.patrons_df['PatronID'], errors='coerce').fillna(0).astype(int)
                self.patrons_df['MemberID'] = self.patrons_df['MemberID'].fillna('').astype(str)
                # Auto-generate MemberID for any row missing it
                for idx, row in self.patrons_df.iterrows():
                    m_val = str(row['MemberID']).strip()
                    if not m_val or m_val.lower() == 'nan':
                        self.patrons_df.at[idx, 'MemberID'] = format_member_id(row['PatronID'])

                self.patrons_df['MeritScore'] = pd.to_numeric(self.patrons_df['MeritScore'], errors='coerce').fillna(INITIAL_MERIT_SCORE).astype(int)
                self.patrons_df['TotalBorrowed'] = pd.to_numeric(self.patrons_df['TotalBorrowed'], errors='coerce').fillna(0).astype(int)
                self.patrons_df['CurrentLoans'] = pd.to_numeric(self.patrons_df['CurrentLoans'], errors='coerce').fillna(0).astype(int)
                self.patrons_df['Name'] = self.patrons_df['Name'].fillna('').astype(str)
                self.patrons_df['Email'] = self.patrons_df['Email'].fillna('').astype(str)
                self.patrons_df['Phone'] = self.patrons_df['Phone'].fillna('').astype(str)
                self.patrons_df['MembershipType'] = self.patrons_df['MembershipType'].fillna('Student').astype(str)
                self.patrons_df['Status'] = self.patrons_df['Status'].fillna('Active').astype(str)
                self.patrons_df['RegisteredDate'] = self.patrons_df['RegisteredDate'].apply(self._format_date_val)

            # Normalize transactions
            if not self.transactions_df.empty:
                self.transactions_df['TransactionID'] = pd.to_numeric(self.transactions_df['TransactionID'], errors='coerce').fillna(0).astype(int)
                self.transactions_df['BookID'] = pd.to_numeric(self.transactions_df['BookID'], errors='coerce').fillna(0).astype(int)
                self.transactions_df['MemberID'] = self.transactions_df['MemberID'].fillna('').astype(str)
                self.transactions_df['FineAmount'] = pd.to_numeric(self.transactions_df['FineAmount'], errors='coerce').fillna(0.0).astype(float)
                self.transactions_df['CustomerName'] = self.transactions_df['CustomerName'].fillna('').astype(str)
                self.transactions_df['CustomerEmail'] = self.transactions_df['CustomerEmail'].fillna('').astype(str)
                self.transactions_df['Status'] = self.transactions_df['Status'].fillna(TRANS_STATUS_ISSUED).astype(str)

                # Back-fill MemberID in transactions if missing
                if not self.patrons_df.empty:
                    name_to_mem = dict(zip(self.patrons_df['Name'].astype(str).str.lower(), self.patrons_df['MemberID']))
                    email_to_mem = dict(zip(self.patrons_df['Email'].astype(str).str.lower(), self.patrons_df['MemberID']))
                    for idx, row in self.transactions_df.iterrows():
                        curr_m = str(row['MemberID']).strip()
                        if not curr_m or curr_m.lower() == 'nan':
                            c_email = str(row['CustomerEmail']).strip().lower()
                            c_name = str(row['CustomerName']).strip().lower()
                            resolved_m = email_to_mem.get(c_email) or name_to_mem.get(c_name) or ""
                            if resolved_m:
                                self.transactions_df.at[idx, 'MemberID'] = resolved_m

                for d_col in ['IssueDate', 'DueDate', 'ReturnDate']:
                    if d_col in self.transactions_df.columns:
                        self.transactions_df[d_col] = self.transactions_df[d_col].apply(self._format_date_val)

            self.is_dirty = False
            self.last_saved_time = datetime.now().strftime("%H:%M:%S")

        except Exception as e:
            raise RuntimeError(f"Failed to load Excel data from {self.excel_file}: {e}")

    def _seed_patrons_from_transactions(self) -> None:
        """Seed patrons table from unique transaction customers with initial 100 merit."""
        if self.transactions_df.empty:
            return

        unique_patrons = self.transactions_df[['CustomerName', 'CustomerEmail']].drop_duplicates()
        patrons_list = []
        for i, (_, row) in enumerate(unique_patrons.iterrows(), start=1):
            name = str(row['CustomerName']).strip()
            email = str(row['CustomerEmail']).strip()
            if not name:
                continue

            # Calculate actual loans from transactions
            total_borrowed = len(self.transactions_df[self.transactions_df['CustomerName'] == name])
            current_loans = len(self.transactions_df[
                (self.transactions_df['CustomerName'] == name) &
                (self.transactions_df['Status'] == TRANS_STATUS_ISSUED)
            ])

            member_id = format_member_id(i)

            patrons_list.append({
                'MemberID': member_id,
                'PatronID': i,
                'Name': name,
                'Email': email,
                'Phone': '+91 98000 00000',
                'MembershipType': 'Student',
                'MeritScore': INITIAL_MERIT_SCORE,
                'TotalBorrowed': total_borrowed,
                'CurrentLoans': current_loans,
                'Status': 'Active',
                'RegisteredDate': datetime.now().strftime("%Y-%m-%d")
            })

        self.patrons_df = pd.DataFrame(patrons_list)
        self.is_dirty = True

    def _format_date_val(self, val: Any) -> str:
        """Format a date or timestamp value to clean YYYY-MM-DD string."""
        if pd.isna(val) or val is None or str(val).strip().lower() in ('nat', 'nan', ''):
            return ''
        if isinstance(val, (datetime, date, pd.Timestamp)):
            return val.strftime('%Y-%m-%d')
        val_str = str(val).strip()
        try:
            parsed = pd.to_datetime(val_str)
            return parsed.strftime('%Y-%m-%d')
        except Exception:
            return val_str

    def save_data(self) -> None:
        """Write current DataFrames to Excel file across all three sheets."""
        try:
            parent = os.path.dirname(os.path.abspath(self.excel_file))
            if parent:
                os.makedirs(parent, exist_ok=True)
            with pd.ExcelWriter(self.excel_file, engine='openpyxl') as writer:
                self.books_df.to_excel(writer, sheet_name='Books', index=False)
                self.transactions_df.to_excel(writer, sheet_name='Transactions', index=False)
                self.patrons_df.to_excel(writer, sheet_name='Patrons', index=False)

            self.is_dirty = False
            self.last_saved_time = datetime.now().strftime("%H:%M:%S")
        except Exception as e:
            raise RuntimeError(f"Failed to save data to Excel: {e}")

    # ==========================
    # Patron & Merit Operations
    # ==========================
    def register_patron(
        self,
        name: str,
        email: str = "",
        phone: str = "",
        membership_type: str = "Student",
        initial_merit: int = INITIAL_MERIT_SCORE,
        custom_member_id: Optional[str] = None
    ) -> int:
        """Register a new patron with unique Member ID and initial merit score (100)."""
        name = name.strip()
        if not name:
            raise ValueError("Patron name cannot be empty.")

        # Check for duplicate email if provided
        if email.strip() and not self.patrons_df.empty:
            existing = self.patrons_df[self.patrons_df['Email'].str.lower() == email.strip().lower()]
            if not existing.empty:
                raise ValueError(f"A member with email '{email}' is already registered.")

        new_id = int((self.patrons_df['PatronID'].max() + 1) if not self.patrons_df.empty else 1)
        member_id = custom_member_id.strip().upper() if custom_member_id and custom_member_id.strip() else format_member_id(new_id)

        # Check for duplicate Member ID
        if not self.patrons_df.empty and 'MemberID' in self.patrons_df.columns:
            if member_id in self.patrons_df['MemberID'].astype(str).str.upper().values:
                # If custom or generated collided, bump numeric suffix
                member_id = f"MEM-{1000 + new_id}"

        new_patron = {
            'MemberID': member_id,
            'PatronID': int(new_id),
            'Name': name,
            'Email': email.strip(),
            'Phone': phone.strip(),
            'MembershipType': membership_type.strip() or 'Student',
            'MeritScore': int(initial_merit),
            'TotalBorrowed': 0,
            'CurrentLoans': 0,
            'Status': 'Active',
            'RegisteredDate': datetime.now().strftime("%Y-%m-%d")
        }

        new_row = pd.DataFrame([new_patron])
        if self.patrons_df.empty:
            self.patrons_df = new_row
        else:
            self.patrons_df = pd.concat([self.patrons_df, new_row], ignore_index=True)

        self.is_dirty = True
        return int(new_id)

    def get_next_member_id(self) -> str:
        """Return the next auto-generated Member ID string (e.g. MEM-1003)."""
        new_id = (self.patrons_df['PatronID'].max() + 1) if not self.patrons_df.empty else 1
        return format_member_id(new_id)

    def get_patron_by_member_id(self, member_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve patron dictionary by exact Member ID (e.g. 'MEM-1001')."""
        if self.patrons_df.empty or not member_id:
            return None
        m_id = str(member_id).strip().upper()
        match = self.patrons_df[self.patrons_df['MemberID'].astype(str).str.upper() == m_id]
        if match.empty:
            return None
        return match.iloc[0].to_dict()

    def update_patron(
        self,
        patron_id: int,
        name: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        membership_type: Optional[str] = None,
        merit_score: Optional[int] = None
    ) -> bool:
        """Update patron profile information."""
        idx = self.patrons_df.index[self.patrons_df['PatronID'] == patron_id].tolist()
        if not idx:
            raise ValueError(f"Member with ID {patron_id} not found.")

        row_idx = idx[0]
        if name is not None and name.strip():
            self.patrons_df.at[row_idx, 'Name'] = name.strip()
        if email is not None:
            self.patrons_df.at[row_idx, 'Email'] = email.strip()
        if phone is not None:
            self.patrons_df.at[row_idx, 'Phone'] = phone.strip()
        if membership_type is not None and membership_type.strip():
            self.patrons_df.at[row_idx, 'MembershipType'] = membership_type.strip()
        if merit_score is not None:
            score = max(0, int(merit_score))
            self.patrons_df.at[row_idx, 'MeritScore'] = score
            self.patrons_df.at[row_idx, 'Status'] = 'Suspended' if score < 50 else ('Warning' if score < 85 else 'Active')

        self.is_dirty = True
        return True

    def get_patron_by_id(self, identifier: Any) -> Optional[Dict[str, Any]]:
        """Retrieve patron dictionary by PatronID (int) or MemberID (str)."""
        if self.patrons_df.empty or identifier is None:
            return None

        # Check if string MemberID like 'MEM-1001'
        if isinstance(identifier, str):
            clean_str = identifier.strip().upper()
            if clean_str.startswith("MEM-"):
                return self.get_patron_by_member_id(clean_str)
            try:
                numeric_id = int(clean_str)
                match = self.patrons_df[self.patrons_df['PatronID'] == numeric_id]
                if not match.empty:
                    return match.iloc[0].to_dict()
            except ValueError:
                pass
            return self.get_patron_by_member_id(clean_str)

        try:
            numeric_id = int(identifier)
            match = self.patrons_df[self.patrons_df['PatronID'] == numeric_id]
            if not match.empty:
                return match.iloc[0].to_dict()
        except (ValueError, TypeError):
            pass
        return None

    def get_patron_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Find patron by name (case-insensitive) or Member ID."""
        if self.patrons_df.empty or not name:
            return None
        term = name.strip()
        if term.upper().startswith("MEM-"):
            by_mem = self.get_patron_by_member_id(term)
            if by_mem:
                return by_mem
        match = self.patrons_df[self.patrons_df['Name'].str.lower() == term.lower()]
        if match.empty:
            return None
        return match.iloc[0].to_dict()

    def get_patrons(
        self,
        search_query: Optional[str] = None,
        sort_by: Optional[str] = None,
        ascending: bool = True,
        filter_status: Optional[str] = None
    ) -> pd.DataFrame:
        """Return filtered and sorted DataFrame of registered members."""
        if self.patrons_df.empty:
            return pd.DataFrame()

        df = self.patrons_df.copy()

        if filter_status and filter_status != "All":
            df = df[df['Status'] == filter_status]

        if search_query:
            term = str(search_query).strip().lower()
            if term:
                mask = (
                    df['MemberID'].astype(str).str.lower().str.contains(term, na=False) |
                    df['Name'].astype(str).str.lower().str.contains(term, na=False) |
                    df['Email'].astype(str).str.lower().str.contains(term, na=False) |
                    df['Phone'].astype(str).str.contains(term, na=False) |
                    df['MembershipType'].astype(str).str.lower().str.contains(term, na=False) |
                    df['PatronID'].astype(str).str.contains(term, na=False)
                )
                df = df[mask]

        if sort_by and sort_by in df.columns:
            if sort_by in ('PatronID', 'MeritScore', 'TotalBorrowed', 'CurrentLoans'):
                df = df.sort_values(sort_by, ascending=ascending)
            else:
                df = df.sort_values(
                    sort_by,
                    ascending=ascending,
                    key=lambda s: s.astype(str).str.lower()
                )

        return df

    def adjust_patron_merit(self, patron_id: int, delta: int, reason: str = "") -> int:
        """Manually or automatically adjust patron merit points."""
        idx = self.patrons_df.index[self.patrons_df['PatronID'] == patron_id].tolist()
        if not idx:
            raise ValueError(f"Patron ID {patron_id} not found.")

        row_idx = idx[0]
        current_score = int(self.patrons_df.at[row_idx, 'MeritScore'])
        new_score = max(0, min(150, current_score + delta))

        self.patrons_df.at[row_idx, 'MeritScore'] = new_score
        self.patrons_df.at[row_idx, 'Status'] = 'Suspended' if new_score < 50 else ('Warning' if new_score < 85 else 'Active')
        self.is_dirty = True
        return new_score

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

        if filter_status and filter_status != "All":
            df = df[df['Status'] == filter_status]

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
    # Transaction Operations (with Merit Integration)
    # ==========================
    def issue_book(
        self,
        book_id: int,
        customer_name: str,
        customer_email: str = "",
        member_id: Optional[str] = None,
        patron_id: Optional[int] = None,
        loan_days: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Issue a book to a customer, validating Merit Score and borrowing limits.
        Uses exact Member ID to avoid ambiguity when patrons share the same name.
        Automatically registers new patrons with 100 merit if not present.
        """
        customer_name = customer_name.strip()
        if not customer_name and not member_id:
            raise ValueError("Customer name or Member ID is required.")

        # 1. Validate Book
        idx = self.books_df.index[self.books_df['BookID'] == book_id].tolist()
        if not idx:
            raise ValueError(f"Book with ID {book_id} not found.")

        row_idx = idx[0]
        avail = int(self.books_df.at[row_idx, 'AvailableCopies'])
        if avail <= 0:
            raise ValueError(f"Book '{self.books_df.at[row_idx, 'Title']}' has 0 available copies.")

        # 2. Lookup Patron (prioritizing Member ID/Patron ID over Name)
        patron = None
        if member_id:
            patron = self.get_patron_by_member_id(member_id)
        elif patron_id is not None:
            patron = self.get_patron_by_id(patron_id)
        elif customer_name.upper().startswith("MEM-"):
            patron = self.get_patron_by_member_id(customer_name)

        if not patron and customer_name:
            patron = self.get_patron_by_name(customer_name)

        if not patron:
            # Auto-register with initial 100 merit
            reg_name = customer_name or f"Member {member_id}"
            p_id = self.register_patron(name=reg_name, email=customer_email, initial_merit=INITIAL_MERIT_SCORE)
            patron = self.get_patron_by_id(p_id)

        customer_name = patron['Name']
        patron_member_id = patron['MemberID']
        merit_score = patron['MeritScore']
        tier_info = get_merit_tier(merit_score)

        if not tier_info['can_borrow']:
            raise ValueError(
                f"Borrowing Blocked: Member '{customer_name}' ({patron_member_id}) has {merit_score} merit points ({tier_info['badge']}). "
                "Borrowing privileges are suspended until overdue fines are cleared."
            )

        if patron['CurrentLoans'] >= tier_info['max_books']:
            raise ValueError(
                f"Borrowing Limit Reached: Patron {patron_member_id} currently has {patron['CurrentLoans']} active loans. "
                f"Their tier ({tier_info['badge']}) permits a maximum of {tier_info['max_books']} concurrent loans."
            )

        # Determine loan days based on tier if not specified
        final_loan_days = loan_days or tier_info['max_loan_days']

        # Update available copies
        new_avail = avail - 1
        self.books_df.at[row_idx, 'AvailableCopies'] = new_avail
        if new_avail == 0:
            self.books_df.at[row_idx, 'Status'] = STATUS_CHECKED_OUT

        # Generate TransactionID
        new_trans_id = (self.transactions_df['TransactionID'].max() + 1) if not self.transactions_df.empty else 1

        issue_dt = datetime.now()
        due_dt = issue_dt + pd.Timedelta(days=max(1, final_loan_days))

        new_trans = {
            'TransactionID': int(new_trans_id),
            'BookID': int(book_id),
            'MemberID': str(patron_member_id),
            'CustomerName': customer_name,
            'CustomerEmail': customer_email.strip() or str(patron['Email']),
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

        # Update Patron Loan Counts
        p_idx = self.patrons_df.index[self.patrons_df['PatronID'] == patron['PatronID']].tolist()[0]
        self.patrons_df.at[p_idx, 'TotalBorrowed'] += 1
        self.patrons_df.at[p_idx, 'CurrentLoans'] += 1

        self.is_dirty = True

        return {
            'transaction_id': new_trans_id,
            'book_title': self.books_df.at[row_idx, 'Title'],
            'member_id': patron_member_id,
            'customer_name': customer_name,
            'due_date': due_dt.strftime("%Y-%m-%d"),
            'merit_score': merit_score,
            'merit_tier': tier_info['badge']
        }

    def return_book(
        self,
        transaction_id: Optional[int] = None,
        book_id: Optional[int] = None,
        member_id: Optional[str] = None,
        customer_name: Optional[str] = None,
        fine_per_day: float = DEFAULT_FINE_PER_DAY
    ) -> Dict[str, Any]:
        """
        Return an issued book, calculate overdue fine, and update User Merit score.
        Uses Member ID to identify the exact member when multiple patrons share a name.
        On-time: +5 bonus merit. Overdue: -2 merit/day late.
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
            if member_id and member_id.strip():
                query = query & (self.transactions_df['MemberID'].astype(str).str.upper() == member_id.strip().upper())
            elif customer_name and customer_name.strip():
                query = query & (self.transactions_df['CustomerName'].str.lower() == customer_name.strip().lower())
            matches = self.transactions_df.index[query].tolist()
            if matches:
                trans_idx = matches[0]
            else:
                raise ValueError(f"No active loan found for Book ID {book_id}.")
        else:
            raise ValueError("Either transaction_id or book_id must be provided.")

        actual_trans_id = int(self.transactions_df.at[trans_idx, 'TransactionID'])
        b_id = int(self.transactions_df.at[trans_idx, 'BookID'])
        cust_name = str(self.transactions_df.at[trans_idx, 'CustomerName'])
        trans_member_id = str(self.transactions_df.at[trans_idx, 'MemberID']) if 'MemberID' in self.transactions_df.columns else ""
        due_date_str = str(self.transactions_df.at[trans_idx, 'DueDate'])
        today_str = datetime.now().strftime("%Y-%m-%d")

        # Overdue & Fine
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

        # Adjust Patron Merit with exact MemberID match
        patron = None
        if trans_member_id and trans_member_id.strip():
            patron = self.get_patron_by_member_id(trans_member_id)
        if not patron and member_id:
            patron = self.get_patron_by_member_id(member_id)
        if not patron:
            patron = self.get_patron_by_name(cust_name)

        merit_delta = 0
        new_merit = INITIAL_MERIT_SCORE
        tier_badge = "🥈 Silver Standard"

        if patron:
            p_idx = self.patrons_df.index[self.patrons_df['PatronID'] == patron['PatronID']].tolist()[0]
            self.patrons_df.at[p_idx, 'CurrentLoans'] = max(0, self.patrons_df.at[p_idx, 'CurrentLoans'] - 1)

            if overdue_days == 0:
                merit_delta = ON_TIME_MERIT_BONUS  # +5
            else:
                merit_delta = -(overdue_days * OVERDUE_PENALTY_PER_DAY)  # -2/day

            new_merit = self.adjust_patron_merit(patron['PatronID'], merit_delta)
            tier_badge = get_merit_tier(new_merit)['badge']

        self.is_dirty = True

        return {
            'transaction_id': actual_trans_id,
            'book_id': b_id,
            'book_title': book_title,
            'member_id': trans_member_id or (patron['MemberID'] if patron else ""),
            'customer_name': cust_name,
            'due_date': due_date_str,
            'return_date': today_str,
            'overdue_days': overdue_days,
            'fine_amount': fine_amount,
            'merit_delta': merit_delta,
            'new_merit_score': new_merit,
            'merit_tier': tier_badge
        }

    def renew_loan(self, transaction_id: int, additional_days: int = 7) -> Dict[str, Any]:
        """Extend the due date of an active, non-overdue loan."""
        matches = self.transactions_df.index[
            (self.transactions_df['TransactionID'] == transaction_id) &
            (self.transactions_df['Status'] == TRANS_STATUS_ISSUED)
        ].tolist()

        if not matches:
            raise ValueError(f"No active loan found for Transaction ID {transaction_id}.")

        idx = matches[0]
        due_str = str(self.transactions_df.at[idx, 'DueDate'])
        today_str = datetime.now().strftime("%Y-%m-%d")

        if due_str < today_str:
            raise ValueError("Overdue loans cannot be renewed. Please return the book and clear fines.")

        current_due = pd.to_datetime(due_str)
        new_due = current_due + pd.Timedelta(days=max(1, additional_days))
        new_due_str = new_due.strftime("%Y-%m-%d")

        self.transactions_df.at[idx, 'DueDate'] = new_due_str
        self.is_dirty = True

        return {
            'transaction_id': transaction_id,
            'customer_name': self.transactions_df.at[idx, 'CustomerName'],
            'new_due_date': new_due_str
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

        if not self.books_df.empty:
            title_map = dict(zip(self.books_df['BookID'], self.books_df['Title']))
            df['BookTitle'] = df['BookID'].map(title_map).fillna('Deleted / Unknown')
        else:
            df['BookTitle'] = 'Unknown'

        if filter_status in ('Issued', 'Active'):
            df = df[df['Status'] == TRANS_STATUS_ISSUED]
        elif filter_status == 'Returned':
            df = df[df['Status'] == TRANS_STATUS_RETURNED]
        elif filter_status == 'Overdue':
            today_str = datetime.now().strftime("%Y-%m-%d")
            overdue_mask = (df['Status'] == TRANS_STATUS_ISSUED) & (df['DueDate'] < today_str)
            df = df[overdue_mask]

        if search_query:
            term = str(search_query).strip().lower()
            if term:
                mask = (
                    df['MemberID'].astype(str).str.lower().str.contains(term, na=False) |
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
        """Aggregate key performance indicators across catalog, patrons, and loans."""
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

        total_patrons = len(self.patrons_df)
        avg_merit = int(self.patrons_df['MeritScore'].mean()) if total_patrons > 0 else 100

        return {
            'total_titles': total_titles,
            'total_copies': total_copies,
            'available_copies': available_copies,
            'checked_out_copies': checked_out_copies,
            'total_transactions': total_transactions,
            'active_loans': active_loans,
            'overdue_loans': overdue_loans,
            'total_fines': round(total_fines, 2),
            'total_patrons': total_patrons,
            'avg_merit': avg_merit
        }

    def get_genre_distribution(self) -> List[Tuple[str, int]]:
        """Return genre breakdown as (genre_name, count) sorted descending."""
        if self.books_df.empty or 'Genre' not in self.books_df.columns:
            return []
        counts = self.books_df['Genre'].value_counts()
        return [(str(genre), int(count)) for genre, count in counts.items()]

    def export_data_to_csv(self, sheet_type: str, export_path: str) -> None:
        """Export 'books', 'transactions', or 'patrons' to a standalone CSV."""
        t = sheet_type.lower()
        if t == 'books':
            self.books_df.to_csv(export_path, index=False)
        elif t == 'transactions':
            self.transactions_df.to_csv(export_path, index=False)
        elif t == 'patrons':
            self.patrons_df.to_csv(export_path, index=False)
        else:
            raise ValueError(f"Unknown export sheet type: {sheet_type}")
