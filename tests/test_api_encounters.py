"""API-level tests for encounter and combat endpoints."""


def test_create_encounter(client):
    r = client.post("/api/encounters", json={"name": "Goblin Ambush"})
    assert r.status_code == 201
    assert r.json()["name"] == "Goblin Ambush"


def test_list_encounters(client):
    client.post("/api/encounters", json={"name": "Encounter A"})
    client.post("/api/encounters", json={"name": "Encounter B"})
    r = client.get("/api/encounters")
    assert r.status_code == 200
    assert len(r.json()) == 2


def test_get_encounter_not_found(client):
    r = client.get("/api/encounters/9999")
    assert r.status_code == 404


def test_add_and_get_participants(client, sample_creature_data):
    # Create encounter and creature
    enc = client.post("/api/encounters", json={"name": "Fight"}).json()
    creature = client.post("/api/creatures", json=sample_creature_data).json()

    # Add creature participant
    r = client.post(
        f"/api/encounters/{enc['id']}/participants",
        json={"participant_type": "creature", "creature_id": creature["id"], "quantity": 3},
    )
    assert r.status_code == 201
    assert r.json()["quantity"] == 3

    # Fetch participants
    r = client.get(f"/api/encounters/{enc['id']}/participants")
    assert r.status_code == 200
    assert len(r.json()) == 1


def test_remove_participant(client, sample_creature_data):
    enc = client.post("/api/encounters", json={"name": "Fight"}).json()
    creature = client.post("/api/creatures", json=sample_creature_data).json()
    p = client.post(
        f"/api/encounters/{enc['id']}/participants",
        json={"participant_type": "creature", "creature_id": creature["id"]},
    ).json()

    r = client.delete(f"/api/encounters/{enc['id']}/participants/{p['id']}")
    assert r.status_code == 204


def test_start_combat(client):
    enc = client.post("/api/encounters", json={"name": "Battle"}).json()
    combatants = [
        {"name": "Goblin", "combatant_type": "creature", "initiative": 12, "max_hp": 7, "current_hp": 7, "ac": 15},
        {"name": "Aria", "combatant_type": "character", "initiative": 18, "max_hp": 38, "current_hp": 38, "ac": 16},
    ]
    r = client.post("/api/combat/sessions", json={"encounter_id": enc["id"], "combatants": combatants})
    assert r.status_code == 201
    body = r.json()
    assert body["session"]["is_active"] is True
    assert len(body["combatants"]) == 2
    # Sorted by initiative
    assert body["combatants"][0]["name"] == "Aria"
    assert body["combatants"][1]["name"] == "Goblin"


def test_next_turn(client):
    enc = client.post("/api/encounters", json={"name": "Battle"}).json()
    combatants = [
        {"name": "A", "combatant_type": "creature", "initiative": 20, "max_hp": 10, "current_hp": 10, "ac": 10},
        {"name": "B", "combatant_type": "creature", "initiative": 10, "max_hp": 10, "current_hp": 10, "ac": 10},
    ]
    session_data = client.post(
        "/api/combat/sessions", json={"encounter_id": enc["id"], "combatants": combatants}
    ).json()
    session_id = session_data["session"]["id"]

    r = client.post(f"/api/combat/sessions/{session_id}/next-turn")
    assert r.status_code == 200
    # current_turn_index should have advanced
    assert r.json()["session"]["current_turn_index"] > 0


def test_update_combatant_hp(client):
    enc = client.post("/api/encounters", json={"name": "Battle"}).json()
    combatants = [
        {"name": "Goblin", "combatant_type": "creature", "initiative": 10, "max_hp": 7, "current_hp": 7, "ac": 15},
    ]
    session_data = client.post(
        "/api/combat/sessions", json={"encounter_id": enc["id"], "combatants": combatants}
    ).json()
    combatant_id = session_data["combatants"][0]["id"]

    r = client.patch(f"/api/combat/combatants/{combatant_id}", json={"current_hp": 2})
    assert r.status_code == 200
    assert r.json()["current_hp"] == 2


def test_end_combat(client):
    enc = client.post("/api/encounters", json={"name": "Battle"}).json()
    session_data = client.post(
        "/api/combat/sessions",
        json={"encounter_id": enc["id"], "combatants": []},
    ).json()
    session_id = session_data["session"]["id"]

    r = client.post(f"/api/combat/sessions/{session_id}/end")
    assert r.status_code == 200
    assert r.json()["is_active"] is False
