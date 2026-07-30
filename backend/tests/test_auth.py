def test_auth0_config_unconfigured(client, app):
    app.config["AUTH0_DOMAIN"] = ""
    app.config["AUTH0_CLIENT_ID"] = ""
    res = client.get("/api/auth/auth0-config")
    assert res.status_code == 200
    assert res.get_json()["configured"] is False


def test_auth0_exchange_requires_token(client, app):
    app.config["AUTH0_DOMAIN"] = "example.auth0.com"
    app.config["AUTH0_CLIENT_ID"] = "test-client"
    res = client.post("/api/auth/auth0", json={})
    assert res.status_code == 400


def test_register_requires_fields(client):
    res = client.post("/api/auth/register", json={})
    assert res.status_code == 400

def test_login_invalid(client):
    res = client.post("/api/auth/login", json={"email": "x@y.com", "password": "no"})
    assert res.status_code == 401

def test_register_and_login(client):
    client.post("/api/auth/register", json={"email": "a@b.com", "password": "secret"})
    res = client.post("/api/auth/login", json={"email": "a@b.com", "password": "secret"})
    assert res.status_code == 200
    assert "access_token" in res.get_json()
