def test_create_project(client, sample_user):
    resp = client.post(
        "/projects/",
        json={
            "name": "Project A",
            "description": "Desc",
            "owner_id": sample_user["id"],
        },
    )
    assert resp.status_code == 201
    assert resp.json()["name"] == "Project A"


def test_create_project_owner_not_found(client):
    resp = client.post(
        "/projects/",
        json={"name": "Project B", "owner_id": 9999},
    )
    assert resp.status_code == 404


def test_create_project_invalid_dates(client, sample_user):
    """Инвариант: end_date > start_date."""
    resp = client.post(
        "/projects/",
        json={
            "name": "Bad Project",
            "owner_id": sample_user["id"],
            "start_date": "2025-12-31T00:00:00",
            "end_date": "2025-01-01T00:00:00",  # раньше start_date
        },
    )
    assert resp.status_code == 422


def test_list_projects(client, sample_project):
    resp = client.get("/projects/")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


def test_get_project(client, sample_project):
    resp = client.get(f"/projects/{sample_project['id']}")
    assert resp.status_code == 200


def test_update_project(client, sample_project):
    resp = client.patch(
        f"/projects/{sample_project['id']}",
        json={"name": "Renamed"},
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Renamed"


def test_delete_project(client, sample_project):
    resp = client.delete(f"/projects/{sample_project['id']}")
    assert resp.status_code == 204