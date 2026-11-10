from logic import (add_expense, get_all, find_by_id, delete_expense,
                   find_by_category, total_by_category)


def make_data():
    data = {"next_id": 1, "expenses": []}
    add_expense(data, "Milk", 45.5, "food", "2026-10-14")
    add_expense(data, "Bus", 12, "transport", "2026-10-14")
    add_expense(data, "Bread", 20, "Food", "2026-10-15")
    return data


def test_add_expense():
    data = {"next_id": 1, "expenses": []}
    e = add_expense(data, "Milk", 45.5, "food", "2026-10-14")
    assert e["id"] == 1
    assert data["next_id"] == 2
    assert len(data["expenses"]) == 1
    e2 = add_expense(data, "Bus", 12, "transport", "2026-10-14")
    assert e2["id"] == 2


def test_get_all():
    assert len(get_all(make_data())) == 3
    assert get_all({"next_id": 1, "expenses": []}) == []


def test_find_by_id():
    data = make_data()
    assert find_by_id(data, 2)["title"] == "Bus"
    assert find_by_id(data, 99) is None


def test_delete_expense():
    data = make_data()
    assert delete_expense(data, 1) is True
    assert find_by_id(data, 1) is None
    assert len(data["expenses"]) == 2
    assert delete_expense(data, 99) is False


def test_find_by_category():
    data = make_data()
    assert len(find_by_category(data, "food")) == 2
    assert len(find_by_category(data, "TRANSPORT")) == 1
    assert find_by_category(data, "books") == []


def test_total_by_category():
    data = {"next_id": 1, "expenses": []}
    add_expense(data, "Milk", 45.5, "food", "2026-10-14")
    add_expense(data, "Bread", 20, "food", "2026-10-15")
    add_expense(data, "Bus", 12, "transport", "2026-10-14")
    totals = total_by_category(data)
    assert totals["food"] == 65.5
    assert totals["transport"] == 12
    assert total_by_category({"next_id": 1, "expenses": []}) == {}


test_add_expense()
test_get_all()
test_find_by_id()
test_delete_expense()
test_find_by_category()
test_total_by_category()
print("All tests passed")