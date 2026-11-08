from datetime import datetime

from flask import Flask, request, jsonify, redirect
from flask_cors import CORS

import db
import logic

app = Flask(__name__)
CORS(app, origins=["https://liznichenko.pp.ua"])
app.json.ensure_ascii = False
db.init()


@app.get("/items")
def list_items():
	category = request.args.get("category")
	if category is not None:
		category = category.strip().lower()
	return jsonify(db.load(category))


@app.post("/items")
def add_item():
	data = request.get_json(silent=True)
	if not isinstance(data, dict):
		return jsonify({"error": "expected a JSON object in the request body"}), 400

	for field in ("date", "category", "amount"):
		if field not in data:
			return jsonify({"error": f"missing field: {field}"}), 400

	day = data["date"]
	try:
		datetime.strptime(day, "%Y-%m-%d")
	except (ValueError, TypeError):
		return jsonify({"error": "date must look like 2026-10-20"}), 400

	try:
		amount = float(data["amount"])
	except (ValueError, TypeError):
		return jsonify({"error": "amount must be a number"}), 400
	if amount <= 0:
		return jsonify({"error": "amount must be greater than zero"}), 400

	category = str(data["category"]).strip().lower()
	if category == "":
		return jsonify({"error": "category must not be empty"}), 400

	title = str(data.get("title", ""))
	new_id = db.add(day, category, amount, title)
	return jsonify({"id": new_id}), 201


@app.delete("/items/<int:item_id>")
def delete_item(item_id):
	if db.delete(item_id):
		return jsonify({"deleted": item_id})
	return jsonify({"error": "not found"}), 404


@app.get("/report")
def report():
	expenses = db.load()
	return jsonify(logic.total_by_category({"expenses": expenses}))

@app.get("/")
def index():
    return redirect("/items")

if __name__ == "__main__":
	app.run(debug=True)