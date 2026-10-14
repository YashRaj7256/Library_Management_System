# 📚 Library Management System Pro (LibraryOS)

A modern desktop application built with **Python**, **CustomTkinter**, **Matplotlib**, **Pandas**, and **Microsoft Excel** (`openpyxl`).

---

## 🌟 Modern UI Features & Enhancements

- **🎨 Modern Fluent Interface (CustomTkinter)**:
  - **Dark / Light Mode**: Dynamic switcher that seamlessly updates widgets and data tables.
  - **Modern Sidebar Navigation**: Intuitive sidebar with smooth view switching and UI scaling controls.
  - **Rounded Cards & Form Fields**: Clean layout with visual feedback badges.
- **📊 Embedded Visual Charts (Matplotlib)**:
  - **Donut Chart**: Live ratio of Available Copies vs. Checked Out Copies.
  - **Bar Chart**: Breakdown of Top Book Genres in the catalog.
  - Charts adapt to Dark/Light theme automatically.
- **📖 Full Catalog Management**: Complete Create, Read, Update, and Delete (CRUD) operations for books with real-time field validation.
- **🔄 Smart Loan & Circulation Workflow**:
  - Issue books with patron details, live availability checking, and customizable loan durations (7, 14, 21, 30 days).
  - One-click book returns directly from active loan selections.
  - **Automated Overdue & Fine Calculation**: Accurately computes days overdue and calculates fines (configurable rate, default ₹5.00/day).
- **⚡ Instant Search & Column Sorting**: Real-time filtering across Title, Author, Genre, and ISBN, plus sortable columns.
- **💾 Safe Excel Persistence & CSV Exports**: Direct synchronized saving to `library_system.xlsx` with unsaved change tracking and one-click CSV report exports.

---

## 📁 Project Structure

```text
Library_Management_System/
├── main.py                     # Primary application entry point (CustomTkinter)
├── requirements.txt           # Python package dependencies
├── .gitignore                 # Configured gitignore (excludes venvs, caches, temp files)
├── README.md                  # Comprehensive project documentation
├── library_system.xlsx        # Primary Excel database (Books & Transactions sheets)
├── transactions.xlsx          # Transactions reference file
├── Library Management System project.pdf  # Original project presentation report
│
├── src/                       # Application source code
│   ├── __init__.py
│   ├── models.py              # Data models, genres, and status constants
│   ├── database.py            # Pandas & Excel database engine with business logic
│   └── gui/                   # User interface components
│       ├── __init__.py
│       ├── styles.py          # Modern theme palette, typography, and Treeview theme synchronizer
│       ├── books_view.py      # Modern Book catalog management (Add, Edit, Delete, Search)
│       ├── transactions_view.py # Circulation management (Issue, Return, Overdue fines)
│       ├── analytics_view.py  # Visual dashboard with embedded Matplotlib charts
│       └── app.py             # Main application window with navigation sidebar & header
│
└── tests/                     # Automated test suite
    ├── __init__.py
    └── test_database.py       # Unit tests for database CRUD, loans, fines & persistence
```

---

## 🚀 How to Run the Project

### 1. Run the Application
Launch the modern interface:

```bash
python main.py
```

### 2. Run the Automated Tests
Verify the database engine, loan rules, fine calculations, and Excel persistence:

```bash
python -m unittest discover tests
```
*(All 8 unit tests pass in under 0.5s).*
