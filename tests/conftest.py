import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app


@pytest.fixture(scope="function")
def db_engine():
    """Создаём in-memory SQLite для каждого теста."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(db_engine):
    """Сессия БД для прямого доступа в тестах."""
    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=db_engine
    )
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def client(db_engine):
    """TestClient с подменой зависимости get_db на тестовую БД."""
    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=db_engine
    )

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def sample_user(client):
    """Создаёт пользователя через API и возвращает его."""
    resp = client.post(
        "/users/",
        json={
            "username": "alice",
            "email": "alice@example.com",
            "role": "developer",
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


@pytest.fixture
def sample_project(client, sample_user):
    """Создаёт проект через API."""
    resp = client.post(
        "/projects/",
        json={
            "name": "Digital Twin",
            "description": "Test project",
            "owner_id": sample_user["id"],
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()