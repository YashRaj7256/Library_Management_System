"""
Data models and constants for the Library Management System.
"""
from dataclasses import dataclass
from typing import Optional

# Status Constants
STATUS_AVAILABLE = "Available"
STATUS_CHECKED_OUT = "Checked Out"
STATUS_UNAVAILABLE = "Unavailable"

TRANS_STATUS_ISSUED = "Issued"
TRANS_STATUS_RETURNED = "Returned"

DEFAULT_FINE_PER_DAY = 5.0  # ₹5.00 per day overdue
DEFAULT_LOAN_DAYS = 14      # 2 weeks standard loan

GENRE_CHOICES = [
    "Fiction",
    "Non-Fiction",
    "Science Fiction",
    "Fantasy",
    "Mystery",
    "Romance",
    "Dystopian",
    "Historical",
    "Biography",
    "Self-Help",
    "Technology",
    "Poetry",
    "Horror",
    "Adventure",
    "Other"
]

@dataclass
class Book:
    book_id: int
    title: str
    author: str
    isbn: str
    genre: str
    year: int
    added_date: str
    total_copies: int
    available_copies: int
    status: str
    cost: float

@dataclass
class Transaction:
    transaction_id: int
    book_id: int
    customer_name: str
    customer_email: str
    issue_date: str
    due_date: str
    return_date: Optional[str]
    fine_amount: float
    status: str
