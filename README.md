# Expense Tracker

A command-line program for tracking personal expenses. Each expense has a date, a category, an amount and a title. Data is stored in a JSON file, so it is kept between runs.

## Requirements

Python 3 and Flask. Install the libraries with `pip install -r requirements.txt`.
## How to run

    python cli.py add DATE CATEGORY AMOUNT TITLE
    python cli.py list
    python cli.py find CATEGORY
    python cli.py report
    python cli.py delete ID

Examples:

    python cli.py add 2026-10-20 food 45,5 Milk
    python cli.py add 2026-10-20 transport 12 Bus ticket
    python cli.py list
    python cli.py find food
    python cli.py report
    python cli.py delete 1

## Commands

- `add`: adds an expense. The date must look like `2026-10-20`. The amount must be a positive number (a comma or a dot both work). The title is everything after the amount, so it can have several words. The category is saved in lowercase.
- `list`: prints all expenses.
- `find`: prints the expenses of one category (capital letters are ignored).
- `report`: prints the total amount for each category.
- `delete`: removes the expense with the given ID.

Wrong input (a bad date, a text instead of a number, a missing argument, an unknown command) prints a hint instead of crashing.

## Data format

Data is stored in `data.json`, which is created automatically on the first `add`:

    {
      "next_id": 3,
      "expenses": [
        {
          "id": 2,
          "title": "gym",
          "amount": 670.0,
          "category": "entertainment",
          "date": "2026-10-28"
        }
      ]
    }

- `next_id`: the ID that the next new expense will get. IDs are never reused, even after a delete.
- `expenses`: the list of expenses. Each expense has:
  - `id`: a whole number, unique for every expense
  - `title`: text
  - `amount`: a number greater than zero
  - `category`: text, lowercase
  - `date`: text in the format `YYYY-MM-DD`

If `data.json` is missing or damaged, the program starts with an empty list.

## Files

- `app.py`: the Flask web service (public routes and `/admin/` routes)
- `models.py`: the `Item` class (one expense)
- `logic.py`: functions over a list of `Item` objects (no `print`, no `input`, no database)
- `db.py`: SQLite storage: tables `categories`, `expenses`, `audit_log`; the database path comes from `DB_PATH` (default `data.db`)
- `migrate.py`: one-time migration of an old database (text category) to the `categories` table
- `migrate_users.py`: one-time migration that adds the `users` table and `user_id` columns
- `backup.py`: copies `data.db` into `backups/` (a daily scheduled task runs it)
- `frontend/index.html`: the web page deployed on Netlify
- `tests/`: pytest tests (`test_logic.py`, `test_app.py`)
- `legacy/`: the old console version (`cli.py`, `storage.py`, `logic.py`, `test.py`) with its own `data.json`

## Tests

    pytest -v

The tests run without a server and on a temporary empty database (`DB_PATH`), never on `data.db`. `tests/test_logic.py` checks the `Item` class and the functions in `logic.py`; `tests/test_app.py` checks the Flask routes, including bad requests and the `/admin/` routes.

## Web service (lab 7)

Install and run:

    python -m venv venv
    source venv/bin/activate        # Windows Git Bash: source venv/Scripts/activate
    pip install -r requirements.txt
    python app.py

The server runs at http://127.0.0.1:5000. Data is stored in `data.db` (SQLite), which is created automatically.

### Routes

| Method | Path | What it does |
|---|---|---|
| GET | /items | all expenses (JSON) |
| GET | /items?category=food | expenses of one category |
| POST | /items | add an expense (JSON body: date, category, amount, title) |
| GET | /report | total amount per category |

### Examples

    curl http://127.0.0.1:5000/items
    curl "http://127.0.0.1:5000/items?category=food"
    curl -X POST http://127.0.0.1:5000/items \
         -H "Content-Type: application/json" \
         -d '{"date": "2026-10-21", "category": "food", "amount": 45.5, "title": "Milk"}'
    curl http://127.0.0.1:5000/report

### Errors

A wrong request gets code 400 (bad data) or 404 (not found) and a JSON message, never a server crash:

    curl -i -X POST http://127.0.0.1:5000/items
    curl -i -X DELETE -H "X-Admin-Token: $TOKEN" http://127.0.0.1:5000/admin/items/99

## Running the server

Run everything from the project folder (it contains `data.db`).

1. First terminal, the server:

       source venv/Scripts/activate      # Linux/macOS: source venv/bin/activate
       python -m waitress --listen=127.0.0.1:8000 app:app

2. Second terminal, the tunnel (always start the server first, then the tunnel):

       cloudflared tunnel --url http://127.0.0.1:8000

Cloudflare prints an address like `https://random-words.trycloudflare.com`.
Open `.../items` on it. Stop with `Ctrl+C` in both terminals.

The server listens on 127.0.0.1 only, so it is not visible in the local network.

## Database

SQLite file `data.db` with four tables:

| Table | Columns |
|---|---|
| users | id, login (unique, lowercase), password_hash (scrypt), is_admin, created |
| categories | id, name (unique), monthly_limit |
| expenses | id, user_id (links to users), date, category_id (links to categories), amount, title |
| audit_log | id, ts, action (`add` or `delete`), item_id, details, user_id (who did it) |

`GET /items` and `GET /report` return the category as text, so the web page does not change. An older database with a text category is converted once with `python migrate.py`, and `python migrate_users.py` then adds the users table and gives all existing records to the first user, who becomes the admin (make a backup first).

## Users and login

Create a `.env` file in the project folder (it is in `.gitignore`, never commit it):

    SECRET_KEY=a-long-random-string

The key signs the session cookie, and the app does not start without it. Passwords are stored only as scrypt hashes. The cookie is `Secure`, `HttpOnly` and `SameSite=Lax`, so use the `https://` addresses (the tunnel or Tailscale), not `127.0.0.1`. The older `curl` examples in the lab 7 part above were written before logins existed: now they need a session (`curl -c cookies.txt -X POST .../login ...`, then `curl -b cookies.txt ...`).

| Method | Path | What it does |
|---|---|---|
| POST | /register | create a user (JSON: login, password of 8+ characters) and log in |
| POST | /login | log in; a wrong login and a wrong password get the same answer |
| POST | /logout | log out |
| GET | /me | who is logged in |
| GET, POST | /items | your expenses, add an expense |
| DELETE | /items/ID | delete your own expense (someone else's gives 404) |
| GET | /report, /report/limits | your totals per category |

## Admin routes

They work only for a logged-in user with `is_admin = 1`, and the tunnel blocks `/admin/` from the internet (use them through Tailscale). There is no admin registration: the first user is made admin by `migrate_users.py`.

| Method | Path | What it does |
|---|---|---|
| GET | /admin/export | all expenses of all users (JSON) |
| POST | /admin/import | add a list of expenses (JSON list, at most 1000, all or nothing) |
| DELETE | /admin/items/ID | delete any expense (the log records who did it) |
| GET | /admin/log | the action log (newest first) |

## Backups

    python backup.py

It copies `data.db` to `backups/data-DATE.db`. A Windows scheduled task (`expense-backup`) runs it daily at 20:00.

## Console version

The command-line version described in the first part of this file now lives in `legacy/`. Run it from that folder (`cd legacy`, then `python cli.py list`); it keeps its own `data.json`.

## Безпека

Перевірено 2026-11-09. Для кожної загрози: що зроблено для перевірки і чим закрито.

| Загроза | Перевірка і результат | Статус, чим закрито |
| --- | --- | --- |
| SQL-ін’єкція | POST з category = `'; DROP TABLE expenses; --`, потім GET /items: таблиця ціла, текст збережено як звичайна категорія | закрито: параметри `?` у всіх запитах (db.py) |
| XSS у фронтенді | запис з title = `<img src=x onerror=alert(1)>`: на сторінці показано як текст, вікна alert немає | закрито: дані виводяться через `textContent` |
| сервер розробки в інтернеті | тунель дивиться на waitress, а не на `python app.py` | закрито: waitress; `debug=True` лише в блоці `if __name__ == "__main__"`, тобто для локального запуску |
| доступ в обхід Cloudflare | `netstat -ano \| grep :8000`: порт слухає лише 127.0.0.1 | закрито: публічної IP немає, доступ лише через тунель |
| флуд запитами | 100 POST у циклі через https://api...: 65 відповідей 400 і 35 відповідей 429 | закрито: rate limiting у Cloudflare |
| адмінка з інтернету | /admin/export з телефона через інтернет дає 404; через Tailscale без входу 401, користувачем без прав 403, адміном працює | закрито: правило тунелю, перевірка CF-Connecting-IP, роль is_admin |
| чужі записи | DELETE чужого запису дає 404, список показує лише записи користувача (тести) | закрито: кожен запит фільтрується за user_id із сесії |
| паролі | у базі лише хеші scrypt | закрито: generate_password_hash |
| вгадування паролів | 100 запитів на /login: 49 відповідей 401 і 51 відповідь 429 | закрито: rate limiting у Cloudflare охоплює /items, /login і /register |
| секрети в git | `git log -p \| grep -i token` і пошук .env, cert.pem, UUID.json в історії: порожньо | закрито: .env у .gitignore, токен тунелю в репозиторії немає |
| втрата даних | базу відновлено з копії backups/data-2026-11-09.db, сайт працює | закрито: backup.py щодня о 20:00 (планувальник Windows) |
| копії на тому ж диску | копії лежать на одному диску з базою | відкрито: від поломки диска не рятує; прийнятно для навчального проєкту, але раз на тиждень копіюю backups/ на інший пристрій |
| вразливі бібліотеки | `pip-audit -r requirements.txt`: No known vulnerabilities found | закрито; перевіряти повторно перед здаванням наступних лаб |