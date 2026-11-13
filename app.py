import os
import sqlite3
from datetime import datetime

from dotenv import load_dotenv
from flask import Flask, abort, jsonify, redirect, request, session
from flask_cors import CORS
from werkzeug.security import check_password_hash, generate_password_hash

import db
import logic

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ["SECRET_KEY"]      # the app refuses to start without it
app.config["SESSION_COOKIE_SECURE"] = True
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
CORS(app, origins=["https://liznichenko.pp.ua"], supports_credentials=True)
app.json.ensure_ascii = False
db.init()

# checked when the login does not exist, so the answer takes the same time
DUMMY_HASH = generate_password_hash("not-a-real-password")


@app.errorhandler(401)
def unauthorized(error):
    return jsonify({"error": "login required"}), 401


def current_user():
    """The user of this session, or stop the request with 401."""
    user_id = session.get("user_id")
    if user_id is None:
        abort(401)
    user = db.get_user(user_id)
    if user is None:
        session.clear()
        abort(401)
    return user


def require_admin():
    if "CF-Connecting-IP" in request.headers:    # the admin part is not served through the tunnel
        abort(404)
    user = current_user()
    if not user["is_admin"]:
        abort(403)
    return user


def read_credentials():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        data = {}
    return str(data.get("login", "")).strip().lower(), str(data.get("password", ""))


@app.post("/register")
def register():
    login, password = read_credentials()
    if len(login) < 3 or len(password) < 8:
        return jsonify({"error": "login must have 3+ characters and the password 8+"}), 400
    try:
        user_id = db.add_user(login, generate_password_hash(password))
    except sqlite3.IntegrityError:
        return jsonify({"error": "this login is taken"}), 409
    session.clear()
    session["user_id"] = user_id
    return jsonify({"id": user_id, "login": login}), 201


@app.post("/login")
def login():
    login_name, password = read_credentials()
    user = db.get_user_by_login(login_name)
    hash_to_check = user["password_hash"] if user else DUMMY_HASH
    password_ok = check_password_hash(hash_to_check, password)
    if user is None or not password_ok:
        return jsonify({"error": "wrong login or password"}), 401
    session.clear()
    session["user_id"] = user["id"]
    return jsonify({"id": user["id"], "login": user["login"]})


@app.post("/logout")
def logout():
    session.clear()
    return jsonify({"ok": True})


@app.get("/me")
def me():
    user = current_user()
    return jsonify({"id": user["id"], "login": user["login"], "is_admin": bool(user["is_admin"])})


def check_item(data):
    """Validate one item. Return ((date, category, amount, title), None) or (None, error)."""
    if not isinstance(data, dict):
        return None, "expected a JSON object"
    for field in ("date", "category", "amount"):
        if field not in data:
            return None, f"missing field: {field}"

    day = data["date"]
    try:
        datetime.strptime(day, "%Y-%m-%d")
    except (ValueError, TypeError):
        return None, "date must look like 2026-10-20"

    try:
        amount = float(data["amount"])
    except (ValueError, TypeError):
        return None, "amount must be a number"
    if amount <= 0:
        return None, "amount must be greater than zero"

    category = str(data["category"]).strip().lower()
    if category == "":
        return None, "category must not be empty"

    title = str(data.get("title", ""))
    return (day, category, amount, title), None


@app.get("/items")
def list_items():
    user = current_user()
    category = request.args.get("category")
    if category is not None:
        category = category.strip().lower()
    return jsonify([item.to_dict() for item in db.load(user["id"], category)])


@app.post("/items")
def add_item():
    user = current_user()
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "expected a JSON object in the request body"}), 400
    item, error = check_item(data)
    if error:
        return jsonify({"error": error}), 400
    return jsonify({"id": db.add(user["id"], *item)}), 201


@app.delete("/items/<int:item_id>")
def delete_item(item_id):
    user = current_user()
    if not db.delete(user["id"], item_id):          # not found and someone else's look the same
        return jsonify({"error": "not found"}), 404
    return jsonify({"deleted": item_id})


@app.get("/report")
def report():
    user = current_user()
    return jsonify(logic.total_by_category(db.load(user["id"])))


@app.get("/report/limits")
def report_limits():
    """The JOIN report: total per category next to its monthly limit."""
    user = current_user()
    return jsonify(db.totals_with_limits(user["id"], request.args.get("month")))


@app.get("/admin/export")
def admin_export():
    require_admin()
    return jsonify(db.export_all())


@app.post("/admin/import")
def admin_import():
    admin = require_admin()
    data = request.get_json(silent=True)
    if not isinstance(data, list):
        return jsonify({"error": "expected a JSON list"}), 400
    if len(data) > 1000:
        return jsonify({"error": "at most 1000 items at a time"}), 400

    items = []
    for number, entry in enumerate(data, start=1):
        item, error = check_item(entry)
        if error:
            return jsonify({"error": f"item {number}: {error}"}), 400
        items.append(item)
    for item in items:           # nothing is saved unless every item is valid
        db.add(admin["id"], *item)
    return jsonify({"added": len(items)}), 201


@app.delete("/admin/items/<int:item_id>")
def admin_delete_item(item_id):
    admin = require_admin()
    if not db.admin_delete(admin["id"], item_id):
        return jsonify({"error": "not found"}), 404
    return jsonify({"deleted": item_id})


@app.get("/admin/log")
def admin_log():
    require_admin()
    limit = request.args.get("limit", default=50, type=int)
    limit = max(1, min(limit, 500))
    return jsonify(db.log_entries(limit))


@app.get("/")
def index():
    return redirect("/items")


if __name__ == "__main__":
    app.run(debug=True)
