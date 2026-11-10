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

def find_by_category(data, category):
	result = []
	for expense in data["expenses"]:
		if expense["category"].lower() == category.lower():
			result.append(expense)
	return result

def total_by_category(data):
	totals = {}
	for expense in data["expenses"]:
		cat = expense["category"]
		totals[cat] = totals.get(cat, 0) + expense["amount"]
	return totals