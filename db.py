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
        conn.execute("""CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            login TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            is_admin INTEGER NOT NULL DEFAULT 0,
            created TEXT NOT NULL)""")
        conn.execute("""CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id),
            date TEXT NOT NULL,
            category_id INTEGER NOT NULL REFERENCES categories(id),
            amount REAL NOT NULL,
            title TEXT)""")
        conn.execute("""CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT NOT NULL,
            action TEXT NOT NULL,
            item_id INTEGER,
            details TEXT,
            user_id INTEGER REFERENCES users(id))""")


def _log(conn, action, item_id, details, user_id):
    """One row in the action log, inside the same transaction as the action itself."""
    conn.execute(
        "INSERT INTO audit_log (ts, action, item_id, details, user_id) VALUES (?, ?, ?, ?, ?)",
        (datetime.now().isoformat(), action, item_id, details, user_id))


def add_user(login, password_hash, is_admin=0):
    """Create a user and return the id. A taken login raises sqlite3.IntegrityError."""
    with connect() as conn:
        cur = conn.execute(
            "INSERT INTO users (login, password_hash, is_admin, created) VALUES (?, ?, ?, ?)",
            (login, password_hash, is_admin, datetime.now().isoformat()))
        return cur.lastrowid


def get_user_by_login(login):
    with connect() as conn:
        row = conn.execute("SELECT * FROM users WHERE login = ?", (login,)).fetchone()
    return dict(row) if row else None


def get_user(user_id):
    with connect() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return dict(row) if row else None


def load(user_id, category=None):
    """The expenses of one user as Item objects, optionally only one category."""
    query = """SELECT e.id, e.date, c.name AS category, e.amount, e.title
               FROM expenses e JOIN categories c ON c.id = e.category_id
               WHERE e.user_id = ?"""
    params = [user_id]
    if category is not None:
        query += " AND c.name = ?"
        params.append(category)
    query += " ORDER BY e.date, e.id"
    with connect() as conn:
        rows = conn.execute(query, params).fetchall()
    result = []
    for row in rows:
        result.append(Item.from_row(row))
    return result


def add(user_id, date, category, amount, title):
    """Add an expense for a user (and its category if it is new) and return its id."""
    with connect() as conn:
        conn.execute("INSERT OR IGNORE INTO categories (name) VALUES (?)", (category,))
        category_id = conn.execute(
            "SELECT id FROM categories WHERE name = ?", (category,)).fetchone()["id"]
        cur = conn.execute(
            "INSERT INTO expenses (user_id, date, category_id, amount, title) VALUES (?, ?, ?, ?, ?)",
            (user_id, date, category_id, amount, title))
        new_id = cur.lastrowid
        _log(conn, "add", new_id, f"{category} {amount}", user_id)
        return new_id


def _delete(expense_id, owner_id, actor_id):
    """owner_id None means any owner (admin). Return True if a row was deleted."""
    query = """SELECT c.name AS category, e.amount
               FROM expenses e JOIN categories c ON c.id = e.category_id
               WHERE e.id = ?"""
    params = [expense_id]
    if owner_id is not None:
        query += " AND e.user_id = ?"
        params.append(owner_id)
    with connect() as conn:
        row = conn.execute(query, params).fetchone()
        if row is None:
            return False
        conn.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
        _log(conn, "delete", expense_id, f"{row['category']} {row['amount']}", actor_id)
        return True


def delete(user_id, expense_id):
    """Delete an expense only if it belongs to this user."""
    return _delete(expense_id, user_id, user_id)


def admin_delete(admin_id, expense_id):
    """Delete any expense. The log records who did it."""
    return _delete(expense_id, None, admin_id)


def export_all():
    """For the admin: the expenses of all users, as dictionaries."""
    query = """SELECT e.id, e.user_id, u.login AS user, e.date, c.name AS category,
                      e.amount, e.title
               FROM expenses e
               JOIN categories c ON c.id = e.category_id
               JOIN users u ON u.id = e.user_id
               ORDER BY e.date, e.id"""
    with connect() as conn:
        rows = conn.execute(query).fetchall()
    return [dict(row) for row in rows]


def totals_with_limits(user_id, month=None):
    """The JOIN report for one user: total per category next to its monthly limit.
    month is optional, for example "2026-11"."""
    query = """SELECT c.name AS name, SUM(e.amount) AS total, c.monthly_limit AS monthly_limit
               FROM expenses e JOIN categories c ON c.id = e.category_id
               WHERE e.user_id = ?"""
    params = [user_id]
    if month is not None:
        query += " AND e.date LIKE ?"
        params.append(month + "-%")
    query += " GROUP BY c.id ORDER BY total DESC"
    with connect() as conn:
        rows = conn.execute(query, params).fetchall()
    return [dict(row) for row in rows]


def log_entries(limit=50):
    """The latest rows of the action log, newest first."""
    with connect() as conn:
        rows = conn.execute(
            "SELECT id, ts, action, item_id, details, user_id FROM audit_log ORDER BY id DESC LIMIT ?",
            (limit,)).fetchall()
    return [dict(row) for row in rows]
