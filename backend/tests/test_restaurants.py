def test_list_requires_auth(client):
    res = client.get("/api/restaurants/")
    assert res.status_code == 401

def test_create_requires_auth(client):
    res = client.post("/api/restaurants/", json={"name": "Cafe"})
    assert res.status_code == 401

def test_create_and_list_with_token(client, auth_headers, monkeypatch):
    monkeypatch.setattr(
        "routes.restaurants.geocode_address",
        lambda address: (29.6516, -82.3248),
    )
    res = client.post(
        "/api/restaurants/",
        json={"name": "Cafe", "address": "12 Main St, Gainesville, FL"},
        headers=auth_headers,
    )
    assert res.status_code == 201
    body = res.get_json()
    assert body["address"] == "12 Main St, Gainesville, FL"
    assert body["lat"] == 29.6516

    res = client.get("/api/restaurants/?q=main", headers=auth_headers)
    assert res.status_code == 200
    assert len(res.get_json()) >= 1
