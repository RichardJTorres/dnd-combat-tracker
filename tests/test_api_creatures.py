"""API-level tests for creature endpoints."""


def test_status(client):
    r = client.get("/api/status")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_create_creature(client, sample_creature_data):
    r = client.post("/api/creatures", json=sample_creature_data)
    assert r.status_code == 201
    body = r.json()
    assert body["id"] is not None
    assert body["name"] == "Goblin"
    assert body["cr"] == 0.25


def test_list_creatures_empty(client):
    r = client.get("/api/creatures")
    assert r.status_code == 200
    assert r.json() == []


def test_list_creatures(client, sample_creature_data):
    client.post("/api/creatures", json=sample_creature_data)
    client.post("/api/creatures", json={**sample_creature_data, "name": "Orc"})
    r = client.get("/api/creatures")
    assert r.status_code == 200
    assert len(r.json()) == 2


def test_list_creatures_search(client, sample_creature_data):
    client.post("/api/creatures", json=sample_creature_data)
    client.post("/api/creatures", json={**sample_creature_data, "name": "Orc"})
    r = client.get("/api/creatures?search=goblin")
    assert r.status_code == 200
    results = r.json()
    assert len(results) == 1
    assert results[0]["name"] == "Goblin"


def test_get_creature(client, sample_creature_data):
    created = client.post("/api/creatures", json=sample_creature_data).json()
    r = client.get(f"/api/creatures/{created['id']}")
    assert r.status_code == 200
    assert r.json()["name"] == "Goblin"


def test_get_creature_not_found(client):
    r = client.get("/api/creatures/9999")
    assert r.status_code == 404


def test_update_creature(client, sample_creature_data):
    created = client.post("/api/creatures", json=sample_creature_data).json()
    r = client.patch(f"/api/creatures/{created['id']}", json={"hp": 20})
    assert r.status_code == 200
    assert r.json()["hp"] == 20
    assert r.json()["name"] == "Goblin"  # Unchanged


def test_delete_creature(client, sample_creature_data):
    created = client.post("/api/creatures", json=sample_creature_data).json()
    r = client.delete(f"/api/creatures/{created['id']}")
    assert r.status_code == 204
    # Verify gone
    r = client.get(f"/api/creatures/{created['id']}")
    assert r.status_code == 404


def test_delete_creature_not_found(client):
    r = client.delete("/api/creatures/9999")
    assert r.status_code == 404
