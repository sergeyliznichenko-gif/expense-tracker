import os

import pytest
from werkzeug.security import generate_password_hash

PASSWORD = "password123"


@pytest.fixture
def make_client(tmp_path):
    """Returns a function. Every call gives a client with its own cookies, so its own user."""
    os.environ["DB_PATH"] = str(tmp_path / "test.db")      # an empty database for every test
    os.environ.setdefault("SECRET_KEY", "test-secret-key")
    import app                                             # imported here, after DB_PATH is set
    app.app.config["PREFERRED_URL_SCHEME"] = "https"       # the session cookie is Secure
    app.app.config["TESTING"] = True
    app.db.init()
    return app.app.test_client


def register(client, login="alice"):
    return client.post("/register", json={"login": login, "password": PASSWORD})


def make_admin(client, login="boss"):
    """No route can create an admin, so the test writes the user to the database."""
    import app
    app.db.add_user(login, generate_password_hash(PASSWORD), 1)
    return client.post("/login", json={"login": login, "password": PASSWORD})


def add_item(client, category="Food", amount=100):
    return client.post("/items", json={"date": "2026-10-01", "category": category,
                                       "amount": amount, "title": "x"})


def test_register_and_me(make_client):
    alice = make_client()
    assert register(alice).status_code == 201
    me = alice.get("/me").get_json()
    assert me["login"] == "alice"
    assert me["is_admin"] is False


def test_register_rejects_short_password(make_client):
    r = make_client().post("/register", json={"login": "alice", "password": "short"})
    assert r.status_code == 400


def test_register_rejects_taken_login(make_client):
    assert register(make_client()).status_code == 201
    assert register(make_client(), "Alice").status_code == 409     # logins are lowercase


def test_wrong_login_and_wrong_password_look_the_same(make_client):
    register(make_client())
    anon = make_client()
    wrong_password = anon.post("/login", json={"login": "alice", "password": "wrong-password"})
    unknown_login = anon.post("/login", json={"login": "nobody", "password": PASSWORD})
    assert wrong_password.status_code == 401
    assert unknown_login.status_code == 401
    assert wrong_password.get_json() == unknown_login.get_json()


def test_logout_and_login_again(make_client):
    alice = make_client()
    register(alice)
    assert alice.post("/logout").status_code == 200
    assert alice.get("/items").status_code == 401
    r = alice.post("/login", json={"login": "alice", "password": PASSWORD})
    assert r.status_code == 200
    assert alice.get("/items").status_code == 200


def test_data_routes_require_login(make_client):
    anon = make_client()
    assert anon.get("/items").status_code == 401
    r = anon.post("/items", json={"date": "2026-10-01", "category": "food", "amount": 5})
    assert r.status_code == 401
    assert anon.delete("/items/1").status_code == 401
    assert anon.get("/report").status_code == 401
    assert anon.get("/report/limits").status_code == 401


def test_add_and_list(make_client):
    alice = make_client()
    register(alice)
    assert add_item(alice).status_code == 201
    items = alice.get("/items").get_json()
    assert len(items) == 1
    assert items[0]["category"] == "food"          # saved in lowercase


def test_add_rejects_bad_input(make_client):
    alice = make_client()
    register(alice)
    assert add_item(alice, amount="abc").status_code == 400
    r = alice.post("/items", json={"date": "yesterday", "category": "food", "amount": 5})
    assert r.status_code == 400
    assert alice.post("/items").status_code == 400


def test_users_do_not_see_each_others_items(make_client):
    alice, bob = make_client(), make_client()
    register(alice)
    register(bob, "bob")
    add_item(alice)
    assert len(alice.get("/items").get_json()) == 1
    assert bob.get("/items").get_json() == []


def test_delete_someone_elses_item_is_404(make_client):
    alice, bob = make_client(), make_client()
    register(alice)
    register(bob, "bob")
    item_id = add_item(alice).get_json()["id"]
    assert bob.delete(f"/items/{item_id}").status_code == 404
    assert len(alice.get("/items").get_json()) == 1


def test_delete_own_item_is_logged_with_user_id(make_client):
    alice, boss = make_client(), make_client()
    alice_id = register(alice).get_json()["id"]
    item_id = add_item(alice).get_json()["id"]
    assert alice.delete(f"/items/{item_id}").status_code == 200
    assert alice.get("/items").get_json() == []
    make_admin(boss)
    log = boss.get("/admin/log").get_json()
    assert [entry["action"] for entry in log] == ["delete", "add"]
    assert all(entry["user_id"] == alice_id for entry in log)


def test_password_is_stored_as_hash(make_client):
    register(make_client())
    import app
    stored = app.db.get_user_by_login("alice")["password_hash"]
    assert stored.startswith(("scrypt", "pbkdf2"))
    assert PASSWORD not in stored


def test_admin_requires_admin_role(make_client):
    assert make_client().get("/admin/export").status_code == 401       # not logged in
    alice = make_client()
    register(alice)
    assert alice.get("/admin/export").status_code == 403               # logged in, not admin
    boss = make_client()
    make_admin(boss)
    assert boss.get("/admin/export").status_code == 200


def test_admin_export_shows_all_users(make_client):
    alice, bob, boss = make_client(), make_client(), make_client()
    register(alice)
    register(bob, "bob")
    add_item(alice)
    add_item(bob)
    make_admin(boss)
    rows = boss.get("/admin/export").get_json()
    assert {row["user"] for row in rows} == {"alice", "bob"}


def test_admin_refuses_requests_that_came_through_cloudflare(make_client):
    boss = make_client()
    make_admin(boss)
    r = boss.get("/admin/export", headers={"CF-Connecting-IP": "1.2.3.4"})
    assert r.status_code == 404


def test_admin_can_delete_any_item(make_client):
    alice, boss = make_client(), make_client()
    register(alice)
    item_id = add_item(alice).get_json()["id"]
    boss_id = make_admin(boss).get_json()["id"]
    assert boss.delete(f"/admin/items/{item_id}").status_code == 200
    assert boss.delete(f"/admin/items/{item_id}").status_code == 404
    assert alice.get("/items").get_json() == []
    log = boss.get("/admin/log").get_json()
    assert log[0]["action"] == "delete"
    assert log[0]["user_id"] == boss_id


def test_import_is_all_or_nothing(make_client):
    boss = make_client()
    make_admin(boss)
    data = [{"date": "2026-10-01", "category": "food", "amount": 10},
            {"date": "2026-10-01", "category": "food", "amount": -5}]
    assert boss.post("/admin/import", json=data).status_code == 400
    assert boss.get("/admin/export").get_json() == []


def test_report_limits_only_own_items(make_client):
    alice, bob = make_client(), make_client()
    register(alice)
    register(bob, "bob")
    add_item(alice, "Food", 100)
    add_item(alice, "Food", 50)
    add_item(bob, "Bus", 10)
    rows = alice.get("/report/limits").get_json()
    assert rows == [{"name": "food", "total": 150.0, "monthly_limit": None}]


def test_log_limit_parameter(make_client):
    boss = make_client()
    make_admin(boss)
    for _ in range(3):
        add_item(boss)
    assert len(boss.get("/admin/log?limit=2").get_json()) == 2


def test_health_needs_no_login(make_client):
    r = make_client().get("/health")
    assert r.status_code == 200
    assert r.get_json() == {"status": "ok"}


def test_health_reports_database_error(make_client, monkeypatch):
    client = make_client()
    import app

    def broken():
        raise RuntimeError("no database")

    monkeypatch.setattr(app.db, "connect", broken)
    assert client.get("/health").status_code == 503
