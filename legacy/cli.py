import sys
from datetime import datetime

from storage import load_data, save_data
from logic import (add_expense, get_all, find_by_category,
                   total_by_category, delete_expense)


def print_expenses(expenses):
	if not expenses:
		print("Nothing found.")
		return
	for e in expenses:
		print(f'{e["id"]}. {e["date"]} | {e["title"]} | {e["amount"]} | {e["category"]}')


def main():
	if len(sys.argv) < 2:
		print("Usage: python cli.py add|list|find|report|delete ...")
		return

	command = sys.argv[1]
	data = load_data()

	if command == "add":
		if len(sys.argv) < 6:
			print("Usage: python cli.py add DATE CATEGORY AMOUNT TITLE")
			return
		day = sys.argv[2]
		category = sys.argv[3].lower()
		try:
			datetime.strptime(day, "%Y-%m-%d")
		except ValueError:
			print("Date must look like 2026-10-20")
			return
		try:
			amount = float(sys.argv[4].replace(",", "."))
		except ValueError:
			print("Amount must be a number, for example 45.5")
			return
		if amount <= 0:
			print("Amount must be greater than zero.")
			return
		title = " ".join(sys.argv[5:])
		add_expense(data, title, amount, category, day)
		save_data(data)
		print("Added.")

	elif command == "list":
		print_expenses(get_all(data))

	elif command == "find":
		if len(sys.argv) < 3:
			print("Usage: python cli.py find CATEGORY")
			return
		print_expenses(find_by_category(data, sys.argv[2]))

	elif command == "report":
		totals = total_by_category(data)
		if not totals:
			print("No expenses yet.")
			return
		for category, total in totals.items():
			print(f"{category}: {total}")

	elif command == "delete":
		if len(sys.argv) < 3:
			print("Usage: python cli.py delete ID")
			return
		try:
			expense_id = int(sys.argv[2])
		except ValueError:
			print("ID must be a whole number.")
			return
		if delete_expense(data, expense_id):
			save_data(data)
			print("Deleted.")
		else:
			print("No expense with that ID.")

	else:
		print("Unknown command:", command)


if __name__ == "__main__":
	main()