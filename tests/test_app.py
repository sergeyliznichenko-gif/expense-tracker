import os

import pytest

TOKEN = "test-token"
ADMIN = {"X-Admin-Token": TOKEN}


@pytest.fixture
def client(tmp_path):
    os.environ["DB_PATH"] = str(tmp_path / "test.db")   # an empty database for every test
    import app                                          # imported here, after DB_PATH is set
    app.ADMIN_TOKEN = TOKEN                             # not the real token from .env
    app.db.init()
    app.app.config["TESTING"] = True
    return app.app.test_client()


def add_item(client, category="Food", amount=100):
    return client.post("/items", json={"date": "2026-10-01", "category": category,
                                       "amount": amount, "title": "x"})


def test_add_and_list(client):
    assert add_item(client).status_code == 201
    r = client.get("/items")
    assert r.status_code == 200
    items = r.get_json()
    assert len(items) == 1
    assert items[0]["category"] == "food"          # saved in lowercase


def test_add_rejects_text_amount(client):
    assert add_item(client, amount="abc").status_code == 400


def test_add_rejects_bad_date(client):
    r = client.post("/items", json={"date": "yesterday", "category": "food", "amount": 5})
    assert r.status_code == 400


def test_add_rejects_missing_body(client):
    assert client.post("/items").status_code == 400


def test_public_delete_route_is_gone(client):
    assert client.delete("/items/1").status_code in (404, 405)


def test_admin_requires_token(client):
    assert client.get("/admin/export").status_code == 403
    assert client.get("/admin/export", headers={"X-Admin-Token": "wrong"}).status_code == 403


def test_admin_refuses_requests_that_came_through_cloudflare(client):
    r = client.get("/admin/export", headers={**ADMIN, "CF-Connecting-IP": "1.2.3.4"})
    assert r.status_code == 404


def test_admin_delete_missing_returns_404(client):
    assert client.delete("/admin/items/999", headers=ADMIN).status_code == 404


def test_add_and_delete_are_written_to_the_log(client):
    new_id = add_item(client).get_json()["id"]
    assert client.delete(f"/admin/items/{new_id}", headers=ADMIN).status_code == 200
    log = client.get("/admin/log", headers=ADMIN).get_json()
    assert [entry["action"] for entry in log] == ["delete", "add"]
    assert client.get("/items").get_json() == []


def test_import_is_all_or_nothing(client):
    data = [{"date": "2026-10-01", "category": "food", "amount": 10},
            {"date": "2026-10-01", "category": "food", "amount": -5}]
    r = client.post("/admin/import", json=data, headers=ADMIN)
    assert r.status_code == 400
    assert client.get("/items").get_json() == []


def test_report_limits_joins_both_tables(client):
    add_item(client, category="Food", amount=100)
    add_item(client, category="Food", amount=50)
    add_item(client, category="Bus", amount=10)
    rows = client.get("/report/limits").get_json()
    assert rows[0] == {"name": "food", "total": 150.0, "monthly_limit": None}
    assert len(rows) == 2


def test_log_limit_parameter(client):
    for _ in range(3):
        add_item(client)
    log = client.get("/admin/log?limit=2", headers=ADMIN).get_json()
    assert len(log) == 2
