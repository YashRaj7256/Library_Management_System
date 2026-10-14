"""
Unit tests for LibraryDatabase operations.
"""
import os
import tempfile
import unittest
from datetime import datetime
import pandas as pd

from src.database import LibraryDatabase
from src.models import STATUS_AVAILABLE, STATUS_CHECKED_OUT, TRANS_STATUS_ISSUED, TRANS_STATUS_RETURNED


class TestLibraryDatabase(unittest.TestCase):
    def setUp(self):
        # Create a temporary excel file for isolated testing
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_excel = os.path.join(self.temp_dir.name, "test_library.xlsx")
        self.db = LibraryDatabase(self.temp_excel)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_initialization(self):
        """Test default creation of books and empty transactions."""
        self.assertTrue(os.path.exists(self.temp_excel))
        self.assertGreater(len(self.db.books_df), 0)
        self.assertEqual(len(self.db.transactions_df), 0)

    def test_add_and_get_book(self):
        """Test adding a new book."""
        new_id = self.db.add_book(
            title="Clean Code",
            author="Robert C. Martin",
            isbn="978-0132350884",
            genre="Technology",
            year=2008,
            total_copies=5,
            cost=450.00
        )
        self.assertTrue(self.db.is_dirty)
        book = self.db.get_book_by_id(new_id)
        self.assertIsNotNone(book)
        self.assertEqual(book['Title'], "Clean Code")
        self.assertEqual(book['AvailableCopies'], 5)
        self.assertEqual(book['TotalCopies'], 5)
        self.assertEqual(book['Status'], STATUS_AVAILABLE)

    def test_update_book(self):
        """Test updating book attributes."""
        new_id = self.db.add_book(
            title="Old Title",
            author="Author One",
            total_copies=3,
            cost=200.0
        )
        self.db.update_book(new_id, title="Updated Title", cost=299.99)
        book = self.db.get_book_by_id(new_id)
        self.assertEqual(book['Title'], "Updated Title")
        self.assertEqual(book['Cost'], 299.99)

    def test_delete_book(self):
        """Test deleting a book without active loans."""
        new_id = self.db.add_book(title="Temp Book", author="Temp Author", total_copies=2)
        self.assertTrue(self.db.delete_book(new_id))
        self.assertIsNone(self.db.get_book_by_id(new_id))

    def test_issue_book(self):
        """Test issuing a book and tracking availability."""
        new_id = self.db.add_book(title="Single Copy", author="Author", total_copies=1)
        issue_res = self.db.issue_book(
            book_id=new_id,
            customer_name="John Tester",
            customer_email="john@test.com",
            loan_days=7
        )
        self.assertEqual(issue_res['customer_name'], "John Tester")
        
        # Verify book status becomes Checked Out
        book = self.db.get_book_by_id(new_id)
        self.assertEqual(book['AvailableCopies'], 0)
        self.assertEqual(book['Status'], STATUS_CHECKED_OUT)

        # Cannot issue again when 0 available
        with self.assertRaises(ValueError):
            self.db.issue_book(book_id=new_id, customer_name="Another Patron")

        # Cannot delete while issued
        with self.assertRaises(ValueError):
            self.db.delete_book(new_id)

    def test_return_book_ontime_and_overdue(self):
        """Test returning a book and overdue fine computation."""
        new_id = self.db.add_book(title="Returnable Book", author="Author", total_copies=2)
        issue_res = self.db.issue_book(new_id, customer_name="Alice", loan_days=14)
        trans_id = issue_res['transaction_id']

        # 1. Simulate on-time return
        ret_res = self.db.return_book(transaction_id=trans_id)
        self.assertEqual(ret_res['fine_amount'], 0.0)
        self.assertEqual(ret_res['overdue_days'], 0)

        # Verify book copies restored
        book = self.db.get_book_by_id(new_id)
        self.assertEqual(book['AvailableCopies'], 2)
        self.assertEqual(book['Status'], STATUS_AVAILABLE)

        # 2. Simulate overdue return by setting an old due date
        issue_res2 = self.db.issue_book(new_id, customer_name="Bob", loan_days=14)
        trans_id2 = issue_res2['transaction_id']
        # Manually alter DueDate to 10 days ago
        idx = self.db.transactions_df.index[self.db.transactions_df['TransactionID'] == trans_id2][0]
        self.db.transactions_df.at[idx, 'DueDate'] = (datetime.now() - pd.Timedelta(days=10)).strftime("%Y-%m-%d")

        ret_res2 = self.db.return_book(transaction_id=trans_id2, fine_per_day=5.0)
        self.assertGreaterEqual(ret_res2['overdue_days'], 9)
        self.assertGreaterEqual(ret_res2['fine_amount'], 45.0)

    def test_search_and_sort(self):
        """Test searching across titles, authors, and sorting."""
        df_search = self.db.get_books(search_query="Gatsby")
        self.assertGreaterEqual(len(df_search), 1)

        df_sorted = self.db.get_books(sort_by="Cost", ascending=False)
        self.assertGreaterEqual(df_sorted.iloc[0]['Cost'], df_sorted.iloc[-1]['Cost'])

    def test_persistence(self):
        """Test saving to Excel and reloading from disk."""
        new_id = self.db.add_book(title="Persistent Book", author="Writer", total_copies=3)
        self.db.save_data()

        # Reopen with new instance
        db2 = LibraryDatabase(self.temp_excel)
        book = db2.get_book_by_id(new_id)
        self.assertIsNotNone(book)
        self.assertEqual(book['Title'], "Persistent Book")


if __name__ == "__main__":
    unittest.main()
