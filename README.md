# Expense Tracker

A console program for keeping track of personal expenses. Data is stored in a JSON file, so it stays between runs.

## How to run

    python main.py

## Menu

1. Add expense: asks for a title, amount and category, and saves today's date
2. Show all: prints every expense
3. Delete: removes an expense by its ID
0. Exit

## Files

- `main.py`: the menu and all input/output
- `logic.py`: functions for adding, finding and deleting expenses
- `storage.py`: loading and saving `data.json`
