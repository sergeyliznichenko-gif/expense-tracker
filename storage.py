import json
DATA_FILE = "data.json"
def load_data():
	"""Read data from the file. If it is missing or broken, return empty data"""
	try:
		with open(DATA_FILE, encoding="utf-8") as f:
			return json.load(f)
	except FileNotFoundError:
		return {"next_id": 1, "expenses": []}
	except json.JSONDecodeError:
		print("Data file is corrupted. Starting with an empty list.")
		return {"next_id": 1, "expenses": []}	


def save_data(data):
	"""Write data to the file."""
	try:
		with open(DATA_FILE, "w", encoding="utf-8") as f:
			json.dump(data, f, ensure_ascii=False, indent=2)

	except OSError as e:
		print(F"Could not save the file: {e}")