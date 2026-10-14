"""
Main entry point for Library Management System Pro (CustomTkinter Edition).
"""
import sys
import customtkinter as ctk

try:
    import pandas
    import openpyxl
    import matplotlib
except ImportError as err:
    print(f"Error: Required dependency is missing: {err}")
    print("Please install requirements using: pip install -r requirements.txt")
    sys.exit(1)

from src.gui.app import LibraryApp


def main():
    # Initialize modern CustomTkinter window
    root = ctk.CTk()
    
    # Optional custom excel path argument
    custom_excel = sys.argv[1] if len(sys.argv) > 1 else None
    
    app = LibraryApp(root, excel_path=custom_excel)
    root.mainloop()


if __name__ == "__main__":
    main()
