"""One-time migration for lab 12: users table, user_id in expenses and audit_log.
Run: python migrate_users.py [path-to-database]   (default data.db)
It asks for the login and password of the first user (the owner and admin)
and gives that user all existing records."""
import getpass
import sqlite3
import sys
from datetime import datetime

from werkzeug.security import generate_password_hash

path = sys.argv[1] if len(sys.argv) > 1 else "data.db"
conn = sqlite3.connect(path)
conn.row_factory = sqlite3.Row
conn.isolation_level = None            # we control the transaction ourselves

columns = [row["name"] for row in conn.execute("PRAGMA table_info(expenses)")]
if "user_id" in columns:
    print("already migrated, nothing to do")
    sys.exit(0)
if "category_id" not in columns:
    sys.exit("run migrate.py first: the categories table is missing")

login = input("Login of the first user (becomes admin): ").strip()
password = getpass.getpass("Password (at least 8 characters, not shown): ")
if len(login) < 3 or len(password) < 8:
    sys.exit("login must have 3+ characters and the password 8+")
if getpass.getpass("Repeat the password: ") != password:
    sys.exit("the passwords differ")

before = tuple(conn.execute("SELECT COUNT(*), COALESCE(SUM(amount), 0) FROM expenses").fetchone())

conn.execute("BEGIN")                  # everything below happens or nothing does
try:
    conn.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        login TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        is_admin INTEGER NOT NULL DEFAULT 0,
        created TEXT NOT NULL)""")
    cur = conn.execute(
        "INSERT INTO users (login, password_hash, is_admin, created) VALUES (?, ?, 1, ?)",
        (login, generate_password_hash(password), datetime.now().isoformat()))
    owner = cur.lastrowid
    conn.execute("""CREATE TABLE expenses_new (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL REFERENCES users(id),
        date TEXT NOT NULL,
        category_id INTEGER NOT NULL REFERENCES categories(id),
        amount REAL NOT NULL,
        title TEXT)""")
    conn.execute("""INSERT INTO expenses_new (id, user_id, date, category_id, amount, title)
        SELECT id, ?, date, category_id, amount, title FROM expenses""", (owner,))
    conn.execute("DROP TABLE expenses")
    conn.execute("ALTER TABLE expenses_new RENAME TO expenses")
    conn.execute("ALTER TABLE audit_log ADD COLUMN user_id INTEGER REFERENCES users(id)")
    after = tuple(conn.execute("SELECT COUNT(*), COALESCE(SUM(amount), 0) FROM expenses").fetchone())
    if after != before:
        raise RuntimeError(f"numbers differ: before {before}, after {after}")
    conn.execute("COMMIT")
except Exception:
    conn.execute("ROLLBACK")
    raise

print("migrated: rows and total before", before, "after", after, "- all records belong to", login)
