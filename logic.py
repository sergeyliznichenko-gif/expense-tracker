def add_expense(data, title, amount, category, date):
	expense = {
	"id": data["next_id"],
	"title": title,
	"amount": amount,
	"category": category,
	"date": date
	}
	data["expenses"].append(expense)
	data["next_id"] += 1
	return expense

def get_all(data):
	return data["expenses"]

def find_by_id(data, expense_id):
	for expense in data["expenses"]:
		if expense["id"] == expense_id:
			return expense
	return None

def delete_expense(data, expense_id):
	expense = find_by_id(data, expense_id)
	if expense is None:
		return False
	data['expenses'].remove(expense)
	return True