from datetime import date, timedelta


def _setup_and_book(client, admin_token, passenger_token):
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    s1 = client.post("/api/v1/admin/stations/",
                     json={"code": "CNA", "name": "Cancel Src", "city": "CA", "state": "SA"},
                     headers={"Authorization": f"Bearer {admin_token}"}).json()
    s2 = client.post("/api/v1/admin/stations/",
                     json={"code": "CNB", "name": "Cancel Dst", "city": "CB", "state": "SB"},
                     headers={"Authorization": f"Bearer {admin_token}"}).json()
    t = client.post("/api/v1/admin/trains/",
                    json={"train_number": "44444", "name": "Cancel Express", "train_type": "EXPRESS"},
                    headers={"Authorization": f"Bearer {admin_token}"}).json()
    tid = t["id"]
    client.post(f"/api/v1/admin/trains/{tid}/stops",
                json={"station_id": s1["id"], "stop_order": 1, "departure_time": "10:00"},
                headers={"Authorization": f"Bearer {admin_token}"})
    client.post(f"/api/v1/admin/trains/{tid}/stops",
                json={"station_id": s2["id"], "stop_order": 2, "arrival_time": "16:00"},
                headers={"Authorization": f"Bearer {admin_token}"})
    cls = client.post(f"/api/v1/admin/trains/{tid}/classes",
                      json={"class_code": "SL", "class_name": "Sleeper", "total_seats": 3, "fare_per_km": 0.5},
                      headers={"Authorization": f"Bearer {admin_token}"}).json()
    booking = client.post("/api/v1/bookings/", json={
        "train_id": tid, "train_class_id": cls["id"],
        "source_station_id": s1["id"], "destination_station_id": s2["id"],
        "journey_date": tomorrow,
        "passengers": [{"name": "CancelTest", "age": 30, "gender": "FEMALE"}],
    }, headers={"Authorization": f"Bearer {passenger_token}"}).json()
    return booking, tid, cls["id"], tomorrow


def test_cancel_success(client, admin_token, passenger_token):
    booking, *_ = _setup_and_book(client, admin_token, passenger_token)
    r = client.post(f"/api/v1/bookings/{booking['pnr']}/cancel",
                    headers={"Authorization": f"Bearer {passenger_token}"})
    assert r.status_code == 200
    d = r.json()
    assert d["status"] == "CANCELLED"
    assert d["refund_amount"] > 0
    assert "SIMULATED" in d["message"]


def test_cancel_already_cancelled(client, admin_token, passenger_token):
    booking, *_ = _setup_and_book(client, admin_token, passenger_token)
    pnr = booking["pnr"]
    client.post(f"/api/v1/bookings/{pnr}/cancel",
                headers={"Authorization": f"Bearer {passenger_token}"})
    r = client.post(f"/api/v1/bookings/{pnr}/cancel",
                    headers={"Authorization": f"Bearer {passenger_token}"})
    assert r.status_code == 409


def test_cancel_wrong_user(client, admin_token, passenger_token, session):
    from app.models.user import User
    from app.utils.security import hash_password
    attacker = User(full_name="Attacker", email="attacker@test.com",
                    hashed_password=hash_password("Attack@123"), role="passenger", is_active=True)
    session.add(attacker)
    session.commit()
    booking, *_ = _setup_and_book(client, admin_token, passenger_token)
    tok = client.post("/api/v1/auth/login",
                      data={"username": "attacker@test.com", "password": "Attack@123"}).json()["access_token"]
    r = client.post(f"/api/v1/bookings/{booking['pnr']}/cancel",
                    headers={"Authorization": f"Bearer {tok}"})
    assert r.status_code == 403


def test_cancel_restores_inventory(client, admin_token, passenger_token):
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    s1 = client.post("/api/v1/admin/stations/",
                     json={"code": "INV", "name": "Inv Src", "city": "CA", "state": "SA"},
                     headers={"Authorization": f"Bearer {admin_token}"}).json()
    s2 = client.post("/api/v1/admin/stations/",
                     json={"code": "INW", "name": "Inv Dst", "city": "CB", "state": "SB"},
                     headers={"Authorization": f"Bearer {admin_token}"}).json()
    t = client.post("/api/v1/admin/trains/",
                    json={"train_number": "55555", "name": "Inv Express", "train_type": "EXPRESS"},
                    headers={"Authorization": f"Bearer {admin_token}"}).json()
    tid = t["id"]
    client.post(f"/api/v1/admin/trains/{tid}/stops",
                json={"station_id": s1["id"], "stop_order": 1, "departure_time": "09:00"},
                headers={"Authorization": f"Bearer {admin_token}"})
    client.post(f"/api/v1/admin/trains/{tid}/stops",
                json={"station_id": s2["id"], "stop_order": 2, "arrival_time": "15:00"},
                headers={"Authorization": f"Bearer {admin_token}"})
    cls = client.post(f"/api/v1/admin/trains/{tid}/classes",
                      json={"class_code": "SL", "class_name": "Sleeper", "total_seats": 3, "fare_per_km": 0.5},
                      headers={"Authorization": f"Bearer {admin_token}"}).json()

    def book(n):
        return client.post("/api/v1/bookings/", json={
            "train_id": tid, "train_class_id": cls["id"],
            "source_station_id": s1["id"], "destination_station_id": s2["id"],
            "journey_date": tomorrow,
            "passengers": [{"name": f"P{i}", "age": 25, "gender": "MALE"} for i in range(n)],
        }, headers={"Authorization": f"Bearer {passenger_token}"})

    r1 = book(3)
    assert r1.status_code == 201
    assert book(1).status_code == 409  # full
    client.post(f"/api/v1/bookings/{r1.json()['pnr']}/cancel",
                headers={"Authorization": f"Bearer {passenger_token}"})
    assert book(1).status_code == 201  # seat restored


def test_cancel_nonexistent(client, passenger_token):
    r = client.post("/api/v1/bookings/RCFAKE999/cancel",
                    headers={"Authorization": f"Bearer {passenger_token}"})
    assert r.status_code == 404
