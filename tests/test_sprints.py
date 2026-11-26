def test_create_sprint(client, sample_project):
    resp = client.post(
        "/sprints/",
        json={"name": "Sprint 1", "project_id": sample_project["id"]},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "planned"
    assert data["total_points"] == 0


def test_create_sprint_invalid_dates(client, sample_project):
    """Инвариант: end_date > start_date."""
    resp = client.post(
        "/sprints/",
        json={
            "name": "Bad Sprint",
            "project_id": sample_project["id"],
            "start_date": "2025-12-31T00:00:00",
            "end_date": "2025-01-01T00:00:00",
        },
    )
    assert resp.status_code == 422


def test_create_sprint_project_not_found(client):
    resp = client.post(
        "/sprints/",
        json={"name": "Sprint X", "project_id": 9999},
    )
    assert resp.status_code == 404


def test_complete_sprint_no_tasks(client, sample_project):
    """Спринт без задач можно завершить (все задачи Done тривиально)."""
    sprint = client.post(
        "/sprints/",
        json={"name": "Empty Sprint", "project_id": sample_project["id"]},
    ).json()

    resp = client.post(f"/sprints/{sprint['id']}/complete")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "completed"
    assert data["twin_updated"] is True
    # Первое завершение создаёт twin (version=1) и сразу обновляет модель (version=2)
    assert data["twin_version"] == 2
    assert len(data["metrics"]) == 5
    assert len(data["predictions"]) == 1


def test_complete_sprint_with_incomplete_tasks(client, sample_project):
    """Инвариант: нельзя завершить спринт, пока не все задачи Done."""
    sprint = client.post(
        "/sprints/",
        json={"name": "Sprint 2", "project_id": sample_project["id"]},
    ).json()

    client.post(
        "/tasks/",
        json={
            "title": "Task 1",
            "project_id": sample_project["id"],
            "sprint_id": sprint["id"],
            "story_points": 3,
        },
    )

    resp = client.post(f"/sprints/{sprint['id']}/complete")
    assert resp.status_code == 400
    assert "Not all tasks are done" in resp.json()["detail"]


def test_complete_sprint_twice(client, sample_project):
    """Инвариант: нельзя завершить уже завершённый спринт."""
    sprint = client.post(
        "/sprints/",
        json={"name": "Sprint 3", "project_id": sample_project["id"]},
    ).json()

    client.post(f"/sprints/{sprint['id']}/complete")
    resp = client.post(f"/sprints/{sprint['id']}/complete")
    assert resp.status_code == 400
    assert "already completed" in resp.json()["detail"]