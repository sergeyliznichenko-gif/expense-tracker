class Item:
    """One expense: date, category, amount and a title."""

    def __init__(self, date, category, amount, title="", item_id=None):
        self.id = item_id
        self.date = date
        self.category = category
        self.amount = float(amount)      # the only place where text becomes a number
        self.title = title

    def to_dict(self):
        """For jsonify and the API response."""
        return {"id": self.id, "date": self.date, "category": self.category,
                "amount": self.amount, "title": self.title}

    @staticmethod
    def from_row(row):
        """From a sqlite3.Row to an object. A missing title becomes an empty string."""
        return Item(row["date"], row["category"], row["amount"],
                    row["title"] or "", row["id"])

    def is_large(self, limit):
        return self.amount > limit