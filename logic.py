"""Functions over a list of Item objects. No print, no input, no database."""


def find_by_category(items, category):
    """Items of one category (capital letters are ignored)."""
    wanted = category.strip().lower()
    result = []
    for item in items:
        if item.category.lower() == wanted:
            result.append(item)
    return result


def total(items):
    """The sum of all amounts."""
    result = 0
    for item in items:
        result += item.amount
    return result


def total_by_category(items):
    """A dictionary: category name -> sum of its amounts."""
    totals = {}
    for item in items:
        totals[item.category] = totals.get(item.category, 0) + item.amount
    return totals


def large_items(items, limit):
    """Items with an amount above the limit."""
    result = []
    for item in items:
        if item.is_large(limit):
            result.append(item)
    return result