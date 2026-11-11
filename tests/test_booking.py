from datetime import date, timedelta


def _setup(client, admin_token):
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    s1 = client.post("/api/v1/admin/stations/",
                     json={"code": "BKS", "name": "Src", "city": "CA", "state": "SA"},
                     headers={"Authorization": f"Bearer {admin_token}"}).json()
    s2 = client.post("/api/v1/admin/stations/",
                     json={"code": "BKD", "name": "Dst", "city": "CB", "state": "SB"},
                     headers={"Authorization": f"Bearer {admin_token}"}).json()
    t = client.post("/api/v1/admin/trains/",
                    json={"train_number": "33333", "name": "Book Express", "train_type": "EXPRESS"},
                    headers={"Authorization": f"Bearer {admin_token}"}).json()
    tid = t["id"]
    client.post(f"/api/v1/admin/trains/{tid}/stops",
                json={"station_id": s1["id"], "stop_order": 1, "departure_time": "08:00"},
                headers={"Authorization": f"Bearer {admin_token}"})
    client.post(f"/api/v1/admin/trains/{tid}/stops",
                json={"station_id": s2["id"], "stop_order": 2, "arrival_time": "14:00"},
                headers={"Authorization": f"Bearer {admin_token}"})
    cls = client.post(f"/api/v1/admin/trains/{tid}/classes",
                      json={"class_code": "SL", "class_name": "Sleeper", "total_seats": 5, "fare_per_km": 0.5},
                      headers={"Authorization": f"Bearer {admin_token}"}).json()
    return {"train_id": tid, "class_id": cls["id"], "src": s1["id"], "dst": s2["id"], "date": tomorrow}


def _book(client, token, d, n=1):
    pax = [{"name": f"P{i}", "age": 25, "gender": "MALE"} for i in range(n)]
    return client.post("/api/v1/bookings/", json={
        "train_id": d["train_id"], "train_class_id": d["class_id"],
        "source_station_id": d["src"], "destination_station_id": d["dst"],
        "journey_date": d["date"], "passengers": pax,
    }, headers={"Authorization": f"Bearer {token}"})


def test_booking_success(client, admin_token, passenger_token):
    d = _setup(client, admin_token)
    r = _book(client, passenger_token, d)
    assert r.status_code == 201
    b = r.json()
    assert b["status"] == "CONFIRMED"
    assert b["pnr"].startswith("RC")
    assert b["payment"]["payment_status"] == "SUCCESS"
    assert "SIMULATED" in b["payment"]["note"]


def test_pnr_uniqueness(client, admin_token, passenger_token):
    d = _setup(client, admin_token)
    pnrs = {_book(client, passenger_token, d).json()["pnr"] for _ in range(3)}
    assert len(pnrs) == 3


def test_booking_unauthenticated(client, admin_token):
    d = _setup(client, admin_token)
    r = client.post("/api/v1/bookings/", json={
        "train_id": d["train_id"], "train_class_id": d["class_id"],
        "source_station_id": d["src"], "destination_station_id": d["dst"],
        "journey_date": d["date"], "passengers": [{"name": "X", "age": 25, "gender": "MALE"}],
    })
    assert r.status_code == 401


def test_max_passengers_exceeded(client, admin_token, passenger_token):
    d = _setup(client, admin_token)
    assert _book(client, passenger_token, d, n=7).status_code == 422


def test_no_overbooking(client, admin_token, passenger_token):
    d = _setup(client, admin_token)
    assert _book(client, passenger_token, d, n=5).status_code == 201
    assert _book(client, passenger_token, d, n=1).status_code == 409


def test_get_by_pnr(client, admin_token, passenger_token):
    d = _setup(client, admin_token)
    pnr = _book(client, passenger_token, d).json()["pnr"]
    r = client.get(f"/api/v1/bookings/{pnr}",
                   headers={"Authorization": f"Bearer {passenger_token}"})
    assert r.status_code == 200
    assert r.json()["pnr"] == pnr


def test_get_by_pnr_wrong_user(client, admin_token, passenger_token, session):
    from app.models.user import User
    from app.utils.security import hash_password
    other = User(full_name="Other", email="other@test.com",
                 hashed_password=hash_password("Other@123"), role="passenger", is_active=True)
    session.add(other)
    session.commit()
    d = _setup(client, admin_token)
    pnr = _book(client, passenger_token, d).json()["pnr"]
    tok = client.post("/api/v1/auth/login",
                      data={"username": "other@test.com", "password": "Other@123"}).json()["access_token"]
    assert client.get(f"/api/v1/bookings/{pnr}",
                      headers={"Authorization": f"Bearer {tok}"}).status_code == 403


def test_my_bookings(client, admin_token, passenger_token):
    d = _setup(client, admin_token)
    _book(client, passenger_token, d)
    _book(client, passenger_token, d)
    r = client.get("/api/v1/bookings/my",
                   headers={"Authorization": f"Bearer {passenger_token}"})
    assert r.status_code == 200
    assert len(r.json()) >= 2
