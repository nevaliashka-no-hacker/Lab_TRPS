def test_create_user(client):
    resp = client.post(
        "/users/",
        json={"username": "bob", "email": "bob@example.com", "role": "developer"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["username"] == "bob"
    assert data["email"] == "bob@example.com"


def test_create_user_duplicate_email(client, sample_user):
    resp = client.post(
        "/users/",
        json={
            "username": "alice2",
            "email": sample_user["email"],  # дубликат
            "role": "developer",
        },
    )
    assert resp.status_code == 409


def test_get_user(client, sample_user):
    resp = client.get(f"/users/{sample_user['id']}")
    assert resp.status_code == 200
    assert resp.json()["id"] == sample_user["id"]


def test_get_user_not_found(client):
    resp = client.get("/users/9999")
    assert resp.status_code == 404


def test_update_user(client, sample_user):
    resp = client.patch(
        f"/users/{sample_user['id']}",
        json={"role": "scrum_master"},
    )
    assert resp.status_code == 200
    assert resp.json()["role"] == "scrum_master"


def test_delete_user(client, sample_user):
    resp = client.delete(f"/users/{sample_user['id']}")
    assert resp.status_code == 204
    assert client.get(f"/users/{sample_user['id']}").status_code == 404