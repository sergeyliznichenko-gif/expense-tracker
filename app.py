from datetime import datetime

from flask import abort, Flask, request, jsonify, redirect
from flask_cors import CORS

import db
import logic
import os
from dotenv import load_dotenv
import hmac

load_dotenv()
ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN")

app = Flask(__name__)
CORS(app, origins=["https://liznichenko.pp.ua"])
app.json.ensure_ascii = False
db.init()

def require_admin():
    # Cloudflare adds this header to every request that came through it
    if "CF-Connecting-IP" in request.headers:
        abort(404)
    token = request.headers.get("X-Admin-Token", "")
    if not ADMIN_TOKEN or not hmac.compare_digest(token.encode(), ADMIN_TOKEN.encode()):
        abort(403)


@app.get("/items")
def list_items():
	category = request.args.get("category")
	if category is not None:
		category = category.strip().lower()
	return jsonify(db.load(category))


@app.post("/items")
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


@app.post("/items")
def add_item():
	data = request.get_json(silent=True)
	if not isinstance(data, dict):
		return jsonify({"error": "expected a JSON object in the request body"}), 400
	item, error = check_item(data)
	if error:
		return jsonify({"error": error}), 400
	return jsonify({"id": db.add(*item)}), 201
@app.delete("/items/<int:item_id>")
def delete_item(item_id):
	if db.delete(item_id):
		return jsonify({"deleted": item_id})
	return jsonify({"error": "not found"}), 404


@app.get("/admin/export")
def admin_export():
	require_admin()
	return jsonify(db.load())


@app.post("/admin/import")
def admin_import():
	require_admin()
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
		db.add(*item)
	return jsonify({"added": len(items)}), 201


@app.delete("/admin/items/<int:item_id>")
def admin_delete_item(item_id):
	require_admin()
	if not db.delete(item_id):
		return jsonify({"error": "not found"}), 404
	return jsonify({"deleted": item_id})
@app.get("/report")
def report():
	expenses = db.load()
	return jsonify(logic.total_by_category({"expenses": expenses}))

@app.get("/")
def index():
    return redirect("/items")

if __name__ == "__main__":
	app.run(debug=True)