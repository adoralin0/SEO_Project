def test_list_requires_auth(client):
    res = client.get("/api/restaurants/")
    assert res.status_code == 401

def test_create_requires_auth(client):
    res = client.post("/api/restaurants/", json={"name": "Cafe"})
    assert res.status_code == 401

def test_create_and_list_with_token(client, auth_headers):
    res = client.post(
        "/api/restaurants/",
        json={"name": "Cafe"},
        headers=auth_headers,
    )
    assert res.status_code == 201
    body = res.get_json()
    assert body["name"] == "Cafe"

    res = client.get("/api/restaurants/", headers=auth_headers)
    assert res.status_code == 200
    assert len(res.get_json()) >= 1
