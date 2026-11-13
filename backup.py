"""Copies the database into the backups folder next to the script, with the date in the name."""
import datetime
import os
import sqlite3

BASE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE, "data", "data.db")       # the server copy keeps the database in data/
if not os.path.exists(DB):
    DB = os.path.join(BASE, "data.db")           # the working copy keeps it next to the code
BACKUPS = os.path.join(BASE, "backups")

os.makedirs(BACKUPS, exist_ok=True)
target = os.path.join(BACKUPS, f"data-{datetime.date.today()}.db")
src = sqlite3.connect(DB)
dst = sqlite3.connect(target)
src.backup(dst)      # a consistent copy even while the service is running
dst.close()
src.close()
print("saved", target)