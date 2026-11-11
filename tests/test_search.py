from datetime import date, timedelta


def _setup(client, admin_token):
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    s1 = client.post("/api/v1/admin/stations/",
                     json={"code": "SRC", "name": "Source", "city": "CA", "state": "S1"},
                     headers={"Authorization": f"Bearer {admin_token}"}).json()
    s2 = client.post("/api/v1/admin/stations/",
                     json={"code": "DST", "name": "Dest", "city": "CB", "state": "S2"},
                     headers={"Authorization": f"Bearer {admin_token}"}).json()
    t = client.post("/api/v1/admin/trains/",
                    json={"train_number": "22222", "name": "Search Express", "train_type": "EXPRESS"},
                    headers={"Authorization": f"Bearer {admin_token}"}).json()
    tid = t["id"]
    client.post(f"/api/v1/admin/trains/{tid}/stops",
                json={"station_id": s1["id"], "stop_order": 1, "departure_time": "06:00"},
                headers={"Authorization": f"Bearer {admin_token}"})
    client.post(f"/api/v1/admin/trains/{tid}/stops",
                json={"station_id": s2["id"], "stop_order": 2, "arrival_time": "12:00"},
                headers={"Authorization": f"Bearer {admin_token}"})
    client.post(f"/api/v1/admin/trains/{tid}/classes",
                json={"class_code": "SL", "class_name": "Sleeper", "total_seats": 50, "fare_per_km": 0.5},
                headers={"Authorization": f"Bearer {admin_token}"})
    return tomorrow


def test_search_found(client, admin_token):
    tomorrow = _setup(client, admin_token)
    r = client.get(f"/api/v1/trains/search?from_station=SRC&to_station=DST&journey_date={tomorrow}")
    assert r.status_code == 200
    results = r.json()
    assert len(results) >= 1
    assert results[0]["train_number"] == "22222"


def test_search_invalid_station(client):
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    r = client.get(f"/api/v1/trains/search?from_station=XXX&to_station=YYY&journey_date={tomorrow}")
    assert r.status_code == 404


def test_search_same_station(client, admin_token):
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    client.post("/api/v1/admin/stations/",
                json={"code": "SAM", "name": "Same", "city": "SC", "state": "SS"},
                headers={"Authorization": f"Bearer {admin_token}"})
    r = client.get(f"/api/v1/trains/search?from_station=SAM&to_station=SAM&journey_date={tomorrow}")
    assert r.status_code == 400


def test_search_past_date(client):
    r = client.get("/api/v1/trains/search?from_station=A&to_station=B&journey_date=2020-01-01")
    assert r.status_code == 400


def test_search_no_trains(client, admin_token):
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    client.post("/api/v1/admin/stations/",
                json={"code": "NTA", "name": "NTA", "city": "CA", "state": "SA"},
                headers={"Authorization": f"Bearer {admin_token}"})
    client.post("/api/v1/admin/stations/",
                json={"code": "NTB", "name": "NTB", "city": "CB", "state": "SB"},
                headers={"Authorization": f"Bearer {admin_token}"})
    r = client.get(f"/api/v1/trains/search?from_station=NTA&to_station=NTB&journey_date={tomorrow}")
    assert r.status_code == 200
    assert r.json() == []
