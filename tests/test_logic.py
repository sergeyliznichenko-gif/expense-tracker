import pytest

from models import Item
from logic import find_by_category, large_items, total, total_by_category


def make_items():
    return [Item("2026-10-01", "food", 100), Item("2026-10-02", "food", 50),
            Item("2026-10-02", "transport", 40)]


def test_total_by_category_sums_per_category():
    assert total_by_category(make_items()) == {"food": 151.0, "transport": 40.0}


def test_total_by_category_empty():
    assert total_by_category([]) == {}


def test_total_of_all_items():
    assert total(make_items()) == 190.0


def test_find_by_category_ignores_capital_letters():
    found = find_by_category(make_items(), "FOOD")
    assert len(found) == 2


def test_large_items_is_strictly_above_the_limit():
    assert len(large_items(make_items(), 50)) == 1     # 100 only, 50 is not above 50


def test_item_rejects_text_amount():
    with pytest.raises(ValueError):
        Item("2026-10-01", "food", "abc")
