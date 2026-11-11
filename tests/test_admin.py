def test_create_station_admin(client, admin_token):
    r = client.post("/api/v1/admin/stations/",
                    json={"code": "NDLS", "name": "New Delhi", "city": "New Delhi", "state": "Delhi"},
                    headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code == 201
    assert r.json()["code"] == "NDLS"


def test_create_station_duplicate(client, admin_token):
    p = {"code": "BCT", "name": "Mumbai Central", "city": "Mumbai", "state": "MH"}
    client.post("/api/v1/admin/stations/", json=p, headers={"Authorization": f"Bearer {admin_token}"})
    assert client.post("/api/v1/admin/stations/", json=p,
                       headers={"Authorization": f"Bearer {admin_token}"}).status_code == 409


def test_create_station_passenger_forbidden(client, passenger_token):
    r = client.post("/api/v1/admin/stations/",
                    json={"code": "XYZ", "name": "X", "city": "Y", "state": "Z"},
                    headers={"Authorization": f"Bearer {passenger_token}"})
    assert r.status_code == 403


def test_create_station_unauthenticated(client):
    assert client.post("/api/v1/admin/stations/",
                       json={"code": "HYB", "name": "H", "city": "H", "state": "T"}).status_code == 401


def test_list_stations(client, admin_token):
    r = client.get("/api/v1/admin/stations/", headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_update_station(client, admin_token):
    cr = client.post("/api/v1/admin/stations/",
                     json={"code": "UPD", "name": "Old", "city": "City", "state": "State"},
                     headers={"Authorization": f"Bearer {admin_token}"})
    sid = cr.json()["id"]
    r = client.patch(f"/api/v1/admin/stations/{sid}", json={"name": "New Name"},
                     headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code == 200
    assert r.json()["name"] == "New Name"


def test_create_train_admin(client, admin_token):
    r = client.post("/api/v1/admin/trains/",
                    json={"train_number": "12301", "name": "Rajdhani", "train_type": "RAJDHANI"},
                    headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code == 201
    assert r.json()["train_number"] == "12301"


def test_create_train_duplicate(client, admin_token):
    p = {"train_number": "99999", "name": "Test", "train_type": "EXPRESS"}
    client.post("/api/v1/admin/trains/", json=p, headers={"Authorization": f"Bearer {admin_token}"})
    assert client.post("/api/v1/admin/trains/", json=p,
                       headers={"Authorization": f"Bearer {admin_token}"}).status_code == 409


def test_add_stops_and_class(client, admin_token):
    s1 = client.post("/api/v1/admin/stations/",
                     json={"code": "ST1", "name": "St One", "city": "CA", "state": "SA"},
                     headers={"Authorization": f"Bearer {admin_token}"}).json()
    s2 = client.post("/api/v1/admin/stations/",
                     json={"code": "ST2", "name": "St Two", "city": "CB", "state": "SB"},
                     headers={"Authorization": f"Bearer {admin_token}"}).json()
    t = client.post("/api/v1/admin/trains/",
                    json={"train_number": "11111", "name": "Test Express", "train_type": "EXPRESS"},
                    headers={"Authorization": f"Bearer {admin_token}"}).json()
    tid = t["id"]
    r1 = client.post(f"/api/v1/admin/trains/{tid}/stops",
                     json={"station_id": s1["id"], "stop_order": 1, "departure_time": "08:00"},
                     headers={"Authorization": f"Bearer {admin_token}"})
    r2 = client.post(f"/api/v1/admin/trains/{tid}/stops",
                     json={"station_id": s2["id"], "stop_order": 2, "arrival_time": "12:00"},
                     headers={"Authorization": f"Bearer {admin_token}"})
    rc = client.post(f"/api/v1/admin/trains/{tid}/classes",
                     json={"class_code": "SL", "class_name": "Sleeper", "total_seats": 100, "fare_per_km": 0.5},
                     headers={"Authorization": f"Bearer {admin_token}"})
    assert r1.status_code == 201
    assert r2.status_code == 201
    assert rc.status_code == 201
    detail = client.get(f"/api/v1/admin/trains/{tid}",
                        headers={"Authorization": f"Bearer {admin_token}"}).json()
    assert len(detail["stops"]) == 2
    assert len(detail["classes"]) == 1
