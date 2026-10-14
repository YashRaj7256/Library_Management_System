# 📚 Library Management System Pro (LibraryOS)

A modern desktop application built with **Python**, **CustomTkinter**, **Matplotlib**, **Pandas**, and **Microsoft Excel** (`openpyxl`).

---

## 🌟 Modern Features & User Merit System

### ⭐ User Merit & Patron Tier System
- **Initial 100 Merit Points**: Every newly registered patron immediately receives a starting score of 100 points (`🥈 Silver Standard`).
- **Reward for Responsibility**: Returning a borrowed book on or before the due date awards **+5 Merit Points**.
- **Overdue Penalties**: Returning a book late deducts **-2 Merit Points per day overdue** in addition to the late fine.
- **Dynamic Borrowing Tiers**:
  - 🌟 **Gold Elite (120+ Points)**: Allowed up to **5 concurrent loans**, with an extended **21-day loan duration**.
  - 🥈 **Silver Standard (85 – 119 Points)**: Allowed up to **3 concurrent loans**, with standard **14-day loan duration**.
  - 🥉 **Bronze Probation (50 – 84 Points)**: Borrowing restricted to **1 book max**, with **7-day loan duration**.
  - 🚫 **Suspended (< 50 Points)**: Borrowing privileges **blocked** until all overdue loans and fines are resolved.

---

### 🔄 Advanced Issue & Return Features
- **Live Patron & Book Lookup**:
  - Typing a `Book ID` previews real-time title and copy availability.
  - Typing a `Patron Name` displays their live merit standing, tier badge, and current active loans count.
  - Automatic borrowing limit validation prevents patrons from exceeding their tier capacity.
- **Loan Renewals**:
  - One-click `🔄 Renew Loan (+7 Days)` for on-time active loans.
- **Digital Circulation Receipts & Slips**:
  - Instant printable receipt popup for every book issue and return.
  - Shows timestamp, book title, scheduled due date, late fines, merit points earned/deducted, and current merit score.

---

### 👥 Member Profiles & Registration Tab
- Dedicated **👥 Members & Merit** sidebar view.
- Register new patrons with Name, Email, Phone, and Membership Type (`Student`, `Faculty`, `General Public`).
- Search and filter patrons by Standing (`Active`, `Warning`, `Suspended`).
- Manual Merit Adjustment tool for librarians with documented reason.
- CSV directory export.

---

### 🎨 Modern UI & Embedded Visualizations
- **Dark / Light Mode**: Dynamic switcher in the sidebar that smoothly re-styles the entire UI, including data tables.
- **Embedded Matplotlib Charts**:
  - **Donut Chart**: Live ratio of Available vs. Borrowed Inventory.
  - **Horizontal Bar Chart**: Top Book Genres in collection.
- **Safe Multi-Sheet Excel Persistence**: Automatically persists across `Books`, `Transactions`, and `Patrons` sheets in `library_system.xlsx`.

---

## 📁 Project Structure

```text
Library_Management_System/
├── main.py                     # Primary application entry point (CustomTkinter)
├── requirements.txt           # Python package dependencies
├── .gitignore                 # Configured gitignore (excludes venvs, caches, temp files)
├── README.md                  # Comprehensive documentation
├── library_system.xlsx        # Excel database (Books, Transactions, Patrons sheets)
│
├── src/                       # Application source code
│   ├── __init__.py
│   ├── models.py              # Merit tiers, constants, and data models
│   ├── database.py            # Pandas & Excel database engine with business logic
│   └── gui/                   # User interface components
│       ├── __init__.py
│       ├── styles.py          # Modern theme palette & Treeview theme synchronizer
│       ├── books_view.py      # Book catalog management (Add, Edit, Delete, Search)
│       ├── transactions_view.py # Circulation management (Issue, Return, Overdue fines, Renew, Receipts)
│       ├── patrons_view.py    # Member registration and Merit score management
│       ├── analytics_view.py  # Visual dashboard with embedded Matplotlib charts
│       └── app.py             # Main application window with navigation sidebar & header
│
└── tests/                     # Automated test suite
    ├── __init__.py
    └── test_database.py       # 11 unit tests for CRUD, loans, fines, merit & persistence
```

---

## 🚀 How to Run the Project

### 1. Launch the Application
```powershell
python main.py
```

### 2. Run the Unit Test Suite
```powershell
python -m unittest discover tests
```
*(All 11 automated unit tests pass in ~0.6s).*
