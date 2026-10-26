"""
Unit tests for LibraryDatabase operations, loan circulation, and User Merit System.
"""
import os
import tempfile
import unittest
from datetime import datetime
import pandas as pd

from src.database import LibraryDatabase
from src.models import (
    INITIAL_MERIT_SCORE,
    ON_TIME_MERIT_BONUS,
    STATUS_AVAILABLE,
    STATUS_CHECKED_OUT,
    TRANS_STATUS_ISSUED,
    TRANS_STATUS_RETURNED,
    get_merit_tier,
)


class TestLibraryDatabase(unittest.TestCase):
    def setUp(self):
        # Create a temporary excel file for isolated testing
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_excel = os.path.join(self.temp_dir.name, "test_library.xlsx")
        self.db = LibraryDatabase(self.temp_excel)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_initialization(self):
        """Test default creation of books, transactions, and patrons."""
        self.assertTrue(os.path.exists(self.temp_excel))
        self.assertGreater(len(self.db.books_df), 0)
        self.assertEqual(len(self.db.transactions_df), 0)
        self.assertGreaterEqual(len(self.db.patrons_df), 0)

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

    def test_patron_registration_and_initial_merit(self):
        """Test registering a new member with initial 100 merit."""
        p_id = self.db.register_patron(
            name="Charlie Brown",
            email="charlie@email.com",
            phone="+91 99999 11111",
            membership_type="Student",
            initial_merit=INITIAL_MERIT_SCORE
        )
        patron = self.db.get_patron_by_id(p_id)
        self.assertIsNotNone(patron)
        self.assertEqual(patron['Name'], "Charlie Brown")
        self.assertEqual(patron['MeritScore'], 100)
        self.assertEqual(patron['Status'], "Active")
        self.assertEqual(patron['TotalBorrowed'], 0)
        self.assertEqual(patron['CurrentLoans'], 0)

        # Duplicate email test
        with self.assertRaises(ValueError):
            self.db.register_patron(name="Duplicate User", email="charlie@email.com")

    def test_issue_book_and_merit_checking(self):
        """Test issuing a book updates patron loans and checks merit tier."""
        new_book_id = self.db.add_book(title="Single Copy", author="Author", total_copies=1)
        issue_res = self.db.issue_book(
            book_id=new_book_id,
            customer_name="Patron One",
            customer_email="p1@email.com",
            loan_days=14
        )
        self.assertEqual(issue_res['customer_name'], "Patron One")
        self.assertEqual(issue_res['merit_score'], 100)

        # Verify book status becomes Checked Out
        book = self.db.get_book_by_id(new_book_id)
        self.assertEqual(book['AvailableCopies'], 0)
        self.assertEqual(book['Status'], STATUS_CHECKED_OUT)

        # Verify patron has 1 current loan
        patron = self.db.get_patron_by_name("Patron One")
        self.assertEqual(patron['CurrentLoans'], 1)
        self.assertEqual(patron['TotalBorrowed'], 1)

    def test_merit_on_time_reward_and_overdue_penalty(self):
        """Test on-time return earns +5 merit, and overdue return penalizes merit."""
        b_id1 = self.db.add_book(title="Book 1", author="Author", total_copies=2)
        b_id2 = self.db.add_book(title="Book 2", author="Author", total_copies=2)

        p_id = self.db.register_patron("Responsible Member", email="resp@member.com", initial_merit=100)

        # 1. On-time loan & return -> +5 merit
        res1 = self.db.issue_book(b_id1, customer_name="Responsible Member")
        t_id1 = res1['transaction_id']
        ret1 = self.db.return_book(transaction_id=t_id1)

        self.assertEqual(ret1['overdue_days'], 0)
        self.assertEqual(ret1['merit_delta'], ON_TIME_MERIT_BONUS)
        self.assertEqual(ret1['new_merit_score'], 105)

        # 2. Overdue loan & return -> penalty
        res2 = self.db.issue_book(b_id2, customer_name="Responsible Member")
        t_id2 = res2['transaction_id']
        # Set due date 5 days ago
        idx = self.db.transactions_df.index[self.db.transactions_df['TransactionID'] == t_id2][0]
        self.db.transactions_df.at[idx, 'DueDate'] = (datetime.now() - pd.Timedelta(days=5)).strftime("%Y-%m-%d")

        ret2 = self.db.return_book(transaction_id=t_id2, fine_per_day=5.0)
        self.assertEqual(ret2['overdue_days'], 5)
        self.assertEqual(ret2['fine_amount'], 25.0)
        self.assertEqual(ret2['merit_delta'], -10)  # -2 * 5 days
        self.assertEqual(ret2['new_merit_score'], 95)  # 105 - 10 = 95

    def test_merit_suspended_borrowing_block(self):
        """Test that patrons with merit < 50 are blocked from borrowing."""
        p_id = self.db.register_patron("Delinquent Member", email="delinq@test.com", initial_merit=40)
        b_id = self.db.add_book(title="Book", author="Author", total_copies=3)

        with self.assertRaises(ValueError) as ctx:
            self.db.issue_book(b_id, customer_name="Delinquent Member")
        self.assertIn("Borrowing Blocked", str(ctx.exception))

    def test_loan_renewal(self):
        """Test renewing an active non-overdue loan extends due date."""
        b_id = self.db.add_book(title="Renewable Book", author="Author", total_copies=2)
        res = self.db.issue_book(b_id, customer_name="Reader", loan_days=14)
        t_id = res['transaction_id']

        renew_res = self.db.renew_loan(t_id, additional_days=7)
        self.assertIsNotNone(renew_res['new_due_date'])

    def test_search_and_sort(self):
        """Test searching across titles, authors, and sorting."""
        df_search = self.db.get_books(search_query="Gatsby")
        self.assertGreaterEqual(len(df_search), 1)

        df_sorted = self.db.get_books(sort_by="Cost", ascending=False)
        self.assertGreaterEqual(df_sorted.iloc[0]['Cost'], df_sorted.iloc[-1]['Cost'])

    def test_persistence_all_sheets(self):
        """Test saving and loading across Books, Transactions, and Patrons sheets."""
        p_id = self.db.register_patron(name="Persistent Member", email="persist@mail.com", initial_merit=100)
        b_id = self.db.add_book(title="Persistent Book", author="Writer", total_copies=3)
        self.db.save_data()

        # Reopen with fresh instance
        db2 = LibraryDatabase(self.temp_excel)
        book = db2.get_book_by_id(b_id)
        patron = db2.get_patron_by_id(p_id)

        self.assertIsNotNone(book)
        self.assertEqual(book['Title'], "Persistent Book")
        self.assertIsNotNone(patron)
        self.assertEqual(patron['Name'], "Persistent Member")
        self.assertEqual(patron['MeritScore'], 100)


    def test_same_name_members_with_distinct_member_ids(self):
        """Test that two members with the exact same name receive unique Member IDs and distinct loan tracking."""
        p1_id = self.db.register_patron(name="John Doe", email="john1@example.com")
        p2_id = self.db.register_patron(name="John Doe", email="john2@example.com")

        p1 = self.db.get_patron_by_id(p1_id)
        p2 = self.db.get_patron_by_id(p2_id)

        self.assertNotEqual(p1['MemberID'], p2['MemberID'])
        self.assertTrue(p1['MemberID'].startswith("MEM-"))
        self.assertTrue(p2['MemberID'].startswith("MEM-"))

        # Issue book to p1 using exact MemberID
        b_id = self.db.add_book(title="Disambiguation Book", author="Author", total_copies=5)
        res = self.db.issue_book(book_id=b_id, customer_name="John Doe", member_id=p1['MemberID'])
        self.assertEqual(res['member_id'], p1['MemberID'])

        # Verify only p1 has active loan, p2 has 0
        p1_updated = self.db.get_patron_by_member_id(p1['MemberID'])
        p2_updated = self.db.get_patron_by_member_id(p2['MemberID'])
        self.assertEqual(p1_updated['CurrentLoans'], 1)
        self.assertEqual(p2_updated['CurrentLoans'], 0)

        # Return p1's book
        ret = self.db.return_book(transaction_id=res['transaction_id'])
        self.assertEqual(ret['member_id'], p1['MemberID'])

        # Merit only awarded to p1
        p1_final = self.db.get_patron_by_member_id(p1['MemberID'])
        p2_final = self.db.get_patron_by_member_id(p2['MemberID'])
        self.assertEqual(p1_final['MeritScore'], 105)
        self.assertEqual(p2_final['MeritScore'], 100)


if __name__ == "__main__":
    unittest.main()
