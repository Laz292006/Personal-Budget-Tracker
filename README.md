# Personal Budget Tracker

**Student:** Lazaro Ramirez  
**Course:** COP 1500  
**Project:** Individual Python Project

A beginner-friendly, menu-driven personal finance tracker written using the Python standard library.

## Run

1. Install Python 3.10 or later.
2. Open this folder in VS Code.
3. Open the terminal and run `python budget_tracker.py` (Windows may use `py budget_tracker.py`).
4. Type a menu number and follow the prompts.
5. Data is saved automatically in `budget_data.json` in the same folder.

## Test

Run `python -m unittest -v test_budget_tracker.py`.

## Features

- Add income and expenses
- View and filter transactions
- Summarize income, expenses, and balances
- Track monthly category budgets
- Search descriptions and categories
- Edit and delete transactions
- Export transactions to CSV
- Save and reload transactions from JSON
- Validate monetary values, dates, and menu choices

## Python concepts

Loops (`while`, `for`), conditional branches, strings, integers, floats for display, booleans, lists, tuples, dictionaries, functions, classes, class methods, exception handling, JSON, CSV, and file I/O.

## Demo script

1. Choose 1 to add income of $1500 on today's date.
2. Choose 1 to add a Food expense of $45.25.
3. Choose 3 to display a summary (balance: $1454.75).
4. Choose 4 to set a Food budget of $100 for the current month.
5. Choose 4 again to view remaining Food budget ($54.75).
6. Choose 5 to search for the expense description.
7. Choose 6 to edit the expense amount, and choose 3 to view updated totals.
8. Choose 1 and enter an invalid amount such as `abc`; explain that the program asks again.
9. Choose 8 to export CSV; choose 0 to exit.
10. Restart the program and choose 2 to show that saved data persists.

## Important

Do not commit personal financial information in `budget_data.json` to a public repository. The included `.gitignore` excludes it and CSV exports. Use invented sample transactions for your presentation.
