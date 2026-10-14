"""
Data models, merit system tiers, and constants for Library Management System.
"""
from dataclasses import dataclass
from typing import Dict, Any, Optional

# Book Status Constants
STATUS_AVAILABLE = "Available"
STATUS_CHECKED_OUT = "Checked Out"
STATUS_UNAVAILABLE = "Unavailable"

# Transaction Status Constants
TRANS_STATUS_ISSUED = "Issued"
TRANS_STATUS_RETURNED = "Returned"

# Merit System Constants
INITIAL_MERIT_SCORE = 100
ON_TIME_MERIT_BONUS = 5
OVERDUE_PENALTY_PER_DAY = 2
MIN_MERIT_TO_BORROW = 45

# Financial & Loan Defaults
DEFAULT_FINE_PER_DAY = 5.0  # ₹5.00 per day overdue
DEFAULT_LOAN_DAYS = 14      # 2 weeks standard loan

MEMBERSHIP_TYPES = [
    "Student",
    "Faculty",
    "Research Scholar",
    "General Public"
]

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


def get_merit_tier(score: int) -> Dict[str, Any]:
    """Return tier specifications, borrowing limits, and badges for a given merit score."""
    if score >= 120:
        return {
            "tier_name": "Gold Elite",
            "badge": "🌟 Gold Elite",
            "max_books": 5,
            "max_loan_days": 21,
            "can_borrow": True,
            "color_dark": "#10B981",
            "color_light": "#059669"
        }
    elif score >= 85:
        return {
            "tier_name": "Silver Standard",
            "badge": "🥈 Silver Standard",
            "max_books": 3,
            "max_loan_days": 14,
            "can_borrow": True,
            "color_dark": "#3B82F6",
            "color_light": "#2563EB"
        }
    elif score >= 50:
        return {
            "tier_name": "Bronze Probation",
            "badge": "🥉 Bronze Probation",
            "max_books": 1,
            "max_loan_days": 7,
            "can_borrow": True,
            "color_dark": "#F59E0B",
            "color_light": "#D97706"
        }
    else:
        return {
            "tier_name": "Suspended",
            "badge": "🚫 Suspended",
            "max_books": 0,
            "max_loan_days": 0,
            "can_borrow": False,
            "color_dark": "#EF4444",
            "color_light": "#DC2626"
        }


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
class Patron:
    patron_id: int
    name: str
    email: str
    phone: str
    membership_type: str
    merit_score: int
    total_borrowed: int
    current_loans: int
    status: str
    registered_date: str


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
