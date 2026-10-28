# Expense Tracker

A command-line program for tracking personal expenses. Each expense has a date, a category, an amount and a title. Data is stored in a JSON file, so it is kept between runs.

## Requirements

Python 3. No extra libraries are needed.

## How to run

    python cli.py add DATE CATEGORY AMOUNT TITLE
    python cli.py list
    python cli.py find CATEGORY
    python cli.py report
    python cli.py delete ID

Examples:

    python cli.py add 2026-10-20 food 45,5 Milk
    python cli.py add 2026-10-20 transport 12 Bus ticket
    python cli.py list
    python cli.py find food
    python cli.py report
    python cli.py delete 1

## Commands

- `add`: adds an expense. The date must look like `2026-10-20`. The amount must be a positive number (a comma or a dot both work). The title is everything after the amount, so it can have several words. The category is saved in lowercase.
- `list`: prints all expenses.
- `find`: prints the expenses of one category (capital letters are ignored).
- `report`: prints the total amount for each category.
- `delete`: removes the expense with the given ID.

Wrong input (a bad date, a text instead of a number, a missing argument, an unknown command) prints a hint instead of crashing.

## Data format

Data is stored in `data.json`, which is created automatically on the first `add`:

    {
      "next_id": 3,
      "expenses": [
        {
          "id": 2,
          "title": "gym",
          "amount": 670.0,
          "category": "entertainment",
          "date": "2026-10-28"
        }
      ]
    }

- `next_id`: the ID that the next new expense will get. IDs are never reused, even after a delete.
- `expenses`: the list of expenses. Each expense has:
  - `id`: a whole number, unique for every expense
  - `title`: text
  - `amount`: a number greater than zero
  - `category`: text, lowercase
  - `date`: text in the format `YYYY-MM-DD`

If `data.json` is missing or damaged, the program starts with an empty list.

## Files

- `cli.py`: the command-line interface (all input and output)
- `logic.py`: functions for adding, finding, deleting and summing expenses (no `print` or `input`)
- `storage.py`: loading and saving `data.json`
- `tests.py`: checks for the functions in `logic.py`
- `main.py`: an older menu version of the program (optional)

## Tests

    python tests.py

It prints `All tests passed` if everything works.
