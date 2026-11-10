import os
import sqlite3
from datetime import datetime

from models import Item


def connect():
    # the path is read here, at connect time, so tests can point to another database
    conn = sqlite3.connect(os.environ.get("DB_PATH", "data.db"))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")      # without this SQLite ignores links between tables
    return conn


def init():
    """Create the tables if they do not exist yet."""
    with connect() as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            monthly_limit REAL)""")
        conn.execute("""CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            category_id INTEGER NOT NULL REFERENCES categories(id),
            amount REAL NOT NULL,
            title TEXT)""")
        conn.execute("""CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT NOT NULL,
            action TEXT NOT NULL,
            item_id INTEGER,
            details TEXT)""")


def _log(conn, action, item_id, details):
    """One row in the action log, inside the same transaction as the action itself."""
    conn.execute(
        "INSERT INTO audit_log (ts, action, item_id, details) VALUES (?, ?, ?, ?)",
        (datetime.now().isoformat(), action, item_id, details))


def load(category=None):
    """Return a list of Item objects, optionally only one category."""
    query = """SELECT e.id, e.date, c.name AS category, e.amount, e.title
               FROM expenses e JOIN categories c ON c.id = e.category_id"""
    params = ()
    if category is not None:
        query += " WHERE c.name = ?"
        params = (category,)
    query += " ORDER BY e.date, e.id"
    with connect() as conn:
        rows = conn.execute(query, params).fetchall()
    result = []
    for row in rows:
        result.append(Item.from_row(row))
    return result


def add(date, category, amount, title):
    """Add an expense (and its category if it is new) and return its id."""
    with connect() as conn:
        conn.execute("INSERT OR IGNORE INTO categories (name) VALUES (?)", (category,))
        category_id = conn.execute(
            "SELECT id FROM categories WHERE name = ?", (category,)).fetchone()["id"]
        cur = conn.execute(
            "INSERT INTO expenses (date, category_id, amount, title) VALUES (?, ?, ?, ?)",
            (date, category_id, amount, title))
        new_id = cur.lastrowid
        _log(conn, "add", new_id, f"{category} {amount}")
        return new_id


def delete(expense_id):
    """Delete an expense. Return True if it existed."""
    with connect() as conn:
        row = conn.execute(
            """SELECT c.name AS category, e.amount
               FROM expenses e JOIN categories c ON c.id = e.category_id
               WHERE e.id = ?""", (expense_id,)).fetchone()
        if row is None:
            return False
        conn.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
        _log(conn, "delete", expense_id, f"{row['category']} {row['amount']}")
        return True


def totals_with_limits(month=None):
    """The JOIN report: total per category next to its monthly limit.
    month is optional, for example "2026-11"."""
    query = """SELECT c.name AS name, SUM(e.amount) AS total, c.monthly_limit AS monthly_limit
               FROM expenses e JOIN categories c ON c.id = e.category_id"""
    params = ()
    if month is not None:
        query += " WHERE e.date LIKE ?"
        params = (month + "-%",)
    query += " GROUP BY c.id ORDER BY total DESC"
    with connect() as conn:
        rows = conn.execute(query, params).fetchall()
    return [dict(row) for row in rows]


def log_entries(limit=50):
    """The latest rows of the action log, newest first."""
    with connect() as conn:
        rows = conn.execute(
            "SELECT id, ts, action, item_id, details FROM audit_log ORDER BY id DESC LIMIT ?",
            (limit,)).fetchall()
    return [dict(row) for row in rows]
