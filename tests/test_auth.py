def test_register_success(client):
    r = client.post("/api/v1/auth/register", json={"full_name": "John Doe",
        "email": "john@example.com", "password": "Secret@123", "phone": "9876543210"})
    assert r.status_code == 201
    assert r.json()["email"] == "john@example.com"
    assert r.json()["role"] == "passenger"
    assert "hashed_password" not in r.json()


def test_register_duplicate(client):
    p = {"full_name": "Jane", "email": "jane@example.com", "password": "Secret@123"}
    client.post("/api/v1/auth/register", json=p)
    assert client.post("/api/v1/auth/register", json=p).status_code == 409


def test_register_weak_password(client):
    r = client.post("/api/v1/auth/register", json={"full_name": "Weak",
        "email": "weak@example.com", "password": "password"})
    assert r.status_code == 422


def test_register_invalid_email(client):
    r = client.post("/api/v1/auth/register", json={"full_name": "Bad",
        "email": "not-an-email", "password": "Secret@123"})
    assert r.status_code == 422


def test_login_success(client):
    client.post("/api/v1/auth/register", json={"full_name": "Login",
        "email": "login@example.com", "password": "Secret@123"})
    r = client.post("/api/v1/auth/login",
                    data={"username": "login@example.com", "password": "Secret@123"})
    assert r.status_code == 200
    assert "access_token" in r.json()


def test_login_wrong_password(client):
    client.post("/api/v1/auth/register", json={"full_name": "U",
        "email": "u@example.com", "password": "Secret@123"})
    assert client.post("/api/v1/auth/login",
                       data={"username": "u@example.com", "password": "Wrong@1"}).status_code == 401


def test_get_me(client, passenger_token):
    r = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {passenger_token}"})
    assert r.status_code == 200
    assert r.json()["email"] == "passenger@test.com"


def test_get_me_unauthenticated(client):
    assert client.get("/api/v1/auth/me").status_code == 401


def test_forgot_password_generic(client, passenger_user):
    r1 = client.post("/api/v1/auth/forgot-password", json={"email": "nobody@x.com"})
    r2 = client.post("/api/v1/auth/forgot-password", json={"email": passenger_user.email})
    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r1.json()["message"] == r2.json()["message"]


def test_change_password(client, passenger_token):
    r = client.post("/api/v1/auth/change-password",
                    json={"current_password": "Pass@1234", "new_password": "NewPass@123"},
                    headers={"Authorization": f"Bearer {passenger_token}"})
    assert r.status_code == 200
