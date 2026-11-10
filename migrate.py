"""One-time migration: the text category in expenses becomes a row in categories
and a category_id. Run: python migrate.py [path-to-database]   (default data.db)"""
import sqlite3
import sys

path = sys.argv[1] if len(sys.argv) > 1 else "data.db"
conn = sqlite3.connect(path)
conn.row_factory = sqlite3.Row
conn.isolation_level = None            # we control the transaction ourselves

columns = [row["name"] for row in conn.execute("PRAGMA table_info(expenses)")]
if "category_id" in columns:
    print("already migrated, nothing to do")
    sys.exit(0)

before = tuple(conn.execute("SELECT COUNT(*), COALESCE(SUM(amount), 0) FROM expenses").fetchone())

conn.execute("BEGIN")                  # everything below happens or nothing does
try:
    conn.execute("""CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        monthly_limit REAL)""")
    conn.execute("INSERT OR IGNORE INTO categories (name) SELECT DISTINCT category FROM expenses")
    conn.execute("""CREATE TABLE expenses_new (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        category_id INTEGER NOT NULL REFERENCES categories(id),
        amount REAL NOT NULL,
        title TEXT)""")
    conn.execute("""INSERT INTO expenses_new (id, date, category_id, amount, title)
        SELECT e.id, e.date, c.id, e.amount, e.title
        FROM expenses e JOIN categories c ON c.name = e.category""")
    conn.execute("DROP TABLE expenses")
    conn.execute("ALTER TABLE expenses_new RENAME TO expenses")
    after = tuple(conn.execute("SELECT COUNT(*), COALESCE(SUM(amount), 0) FROM expenses").fetchone())
    if after != before:
        raise RuntimeError(f"numbers differ: before {before}, after {after}")
    conn.execute("COMMIT")
except Exception:
    conn.execute("ROLLBACK")
    raise

print("migrated: rows and total before", before, "after", after)
