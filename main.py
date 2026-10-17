from datetime import date

from storage import load_data, save_data
from logic import add_expense, get_all, delete_expense


def ask_amount():
	while True:
		text = input("Amount: ").replace(",", ".")
		try:
			amount = float(text)
		except ValueError:
			print("Enter a number, for example 45.5")
			continue
		if amount <= 0:
			print ("Amount must be greater than zero.")
			continue
		return amount





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
		print("\n1. Add expense\n2. Show all\n3. Delete\n0. Exit")
		choice = input("Your choice: ").strip()
		if choice == "1":
			title = input("Title: ").strip()
			amount = ask_amount()
			category = input("Category: ").strip()
			add_expense(data, title, amount, category, str(date.today()))
			save_data(data)
			print("Added.")
		elif choice == "2":
			show_all(data)
		elif choice == "3":
			try:
				expense_id = int(input("ID to delete: "))
			except ValueError:
				print("ID must be a whole number.")
				continue
			if delete_expense(data, expense_id):
				save_data(data)
				print("Deleted.")
			else:
				print("No expense with that ID.")

		elif choice == "0":
			break
		else:
			print("Invalid choice.")


if __name__ == "__main__":
	main()