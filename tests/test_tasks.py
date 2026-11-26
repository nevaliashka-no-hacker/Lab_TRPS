def test_create_task(client, sample_project):
    resp = client.post(
        "/tasks/",
        json={
            "title": "Implement API",
            "project_id": sample_project["id"],
            "story_points": 5,
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "todo"
    assert data["story_points"] == 5


def test_create_task_negative_story_points(client, sample_project):
    """Инвариант: story_points ≥ 0."""
    resp = client.post(
        "/tasks/",
        json={
            "title": "Bad Task",
            "project_id": sample_project["id"],
            "story_points": -1,
        },
    )
    assert resp.status_code == 422


def test_create_task_project_not_found(client):
    resp = client.post(
        "/tasks/",
        json={"title": "Orphan", "project_id": 9999},
    )
    assert resp.status_code == 404


def test_add_task_to_sprint_recalculates_points(client, sample_project):
    """Инвариант: total_points = Σ story_points."""
    sprint = client.post(
        "/sprints/",
        json={"name": "Sprint A", "project_id": sample_project["id"]},
    ).json()

    task1 = client.post(
        "/tasks/",
        json={
            "title": "T1",
            "project_id": sample_project["id"],
            "story_points": 3,
        },
    ).json()
    task2 = client.post(
        "/tasks/",
        json={
            "title": "T2",
            "project_id": sample_project["id"],
            "story_points": 5,
        },
    ).json()

    client.post(f"/tasks/{task1['id']}/add-to-sprint/{sprint['id']}")
    client.post(f"/tasks/{task2['id']}/add-to-sprint/{sprint['id']}")

    resp = client.get(f"/sprints/{sprint['id']}")
    assert resp.json()["total_points"] == 8


def test_update_task_invalid_status_transition(client, sample_project):
    """Инвариант: допустимые переходы статусов (todo → in_progress)."""
    task = client.post(
        "/tasks/",
        json={"title": "T", "project_id": sample_project["id"]},
    ).json()

    # todo → done — недопустимый переход
    resp = client.patch(f"/tasks/{task['id']}", json={"status": "done"})
    assert resp.status_code == 400
    assert "Invalid status transition" in resp.json()["detail"]


def test_update_task_valid_status_transition(client, sample_project):
    task = client.post(
        "/tasks/",
        json={"title": "T", "project_id": sample_project["id"]},
    ).json()

    resp = client.patch(f"/tasks/{task['id']}", json={"status": "in_progress"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "in_progress"

    resp = client.patch(f"/tasks/{task['id']}", json={"status": "review"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "review"

    resp = client.patch(f"/tasks/{task['id']}", json={"status": "done"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "done"


def test_delete_task_recalculates_sprint_points(client, sample_project):
    sprint = client.post(
        "/sprints/",
        json={"name": "Sprint B", "project_id": sample_project["id"]},
    ).json()
    task = client.post(
        "/tasks/",
        json={
            "title": "T",
            "project_id": sample_project["id"],
            "story_points": 4,
        },
    ).json()
    client.post(f"/tasks/{task['id']}/add-to-sprint/{sprint['id']}")

    client.delete(f"/tasks/{task['id']}")
    resp = client.get(f"/sprints/{sprint['id']}")
    assert resp.json()["total_points"] == 0