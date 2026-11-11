import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool
from app.main import app
from app.database.engine import get_session
from app.utils.security import hash_password
from app.models.user import User


@pytest.fixture(name="session", scope="function")
def session_fixture():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False},
                           poolclass=StaticPool)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    SQLModel.metadata.drop_all(engine)


@pytest.fixture(name="client", scope="function")
def client_fixture(session: Session):
    app.dependency_overrides[get_session] = lambda: session
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture(name="admin_user")
def admin_user_fixture(session: Session):
    user = User(full_name="Test Admin", email="testadmin@railconnect.com",
                hashed_password=hash_password("Admin@1234"), role="admin", is_active=True)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture(name="passenger_user")
def passenger_user_fixture(session: Session):
    user = User(full_name="Test Passenger", email="passenger@test.com",
                hashed_password=hash_password("Pass@1234"), role="passenger", is_active=True)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture(name="admin_token")
def admin_token_fixture(client: TestClient, admin_user: User):
    r = client.post("/api/v1/auth/login",
                    data={"username": admin_user.email, "password": "Admin@1234"})
    return r.json()["access_token"]


@pytest.fixture(name="passenger_token")
def passenger_token_fixture(client: TestClient, passenger_user: User):
    r = client.post("/api/v1/auth/login",
                    data={"username": passenger_user.email, "password": "Pass@1234"})
    return r.json()["access_token"]
