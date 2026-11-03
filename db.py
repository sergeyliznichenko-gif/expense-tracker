import sqlite3

DB = "data.db"


def connect():
	conn = sqlite3.connect(DB)
	conn.row_factory = sqlite3.Row
	return conn


def init():
	"""Create the table if it does not exist yet."""
	with connect() as conn:
		conn.execute("""CREATE TABLE IF NOT EXISTS expenses (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			date TEXT NOT NULL,
			category TEXT NOT NULL,
			amount REAL NOT NULL,
			title TEXT)""")


def load(category=None):
	"""Return a list of dictionaries, optionally only one category."""
	with connect() as conn:
		if category is None:
			rows = conn.execute("SELECT * FROM expenses ORDER BY date, id").fetchall()
		else:
			rows = conn.execute(
				"SELECT * FROM expenses WHERE category = ? ORDER BY date, id",
				(category,)).fetchall()
	result = []
	for row in rows:
		result.append(dict(row))
	return result


def add(date, category, amount, title):
	"""Add an expense and return its id."""
	with connect() as conn:
		cur = conn.execute(
			"INSERT INTO expenses (date, category, amount, title) VALUES (?, ?, ?, ?)",
			(date, category, amount, title))
		return cur.lastrowid


def delete(expense_id):
	"""Delete an expense. Return True if it existed."""
	with connect() as conn:
		cur = conn.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
		return cur.rowcount > 0