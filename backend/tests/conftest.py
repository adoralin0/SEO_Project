import pytest
from app import create_app
from models import db, User

@pytest.fixture
def app():
    app = create_app()
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
    })
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def auth_headers(client):
    client.post("/api/auth/register", json={"email": "test@example.com", "password": "secret"})
    res = client.post("/api/auth/login", json={"email": "test@example.com", "password": "secret"})
    token = res.get_json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
