from datetime import date

from storage import load_data, save_data
from logic import add_expense, get_all


def show_all(data):
	expenses = get_all(data)
	if not expenses:
		print("No expenses yet.")
		return
	for e in expenses:
		print(f'{e["id"]}. {e["date"]} | {e["title"]} | {e["amount"]} | {e["category"]}')


def main():
	data = load_data()
	while True:
		print("\n1. Add expense\n2. Show all\n0. Exit")
		choice = input("Your choice: ").strip()
		if choice == "1":
			title = input("Title: ").strip()
			amount = float(input("Amount: "))
			category = input("Category: ").strip()
			add_expense(data, title, amount, category, str(date.today()))
			save_data(data)
			print("Added.")
		elif choice == "2":
			show_all(data)
		elif choice == "0":
			break
		else:
			print("Invalid choice.")


if __name__ == "__main__":
	main()