def test_history_logged_on_task_create(client, sample_project):
    """Создание задачи должно логироваться в History."""
    client.post(
        "/tasks/",
        json={"title": "Logged Task", "project_id": sample_project["id"]},
    )
    resp = client.get("/history/")
    assert resp.status_code == 200
    entries = resp.json()
    assert any(e["entity_type"] == "task" and e["action"] == "create" for e in entries)


def test_history_logged_on_status_change(client, sample_project):
    task = client.post(
        "/tasks/",
        json={"title": "T", "project_id": sample_project["id"]},
    ).json()
    client.patch(f"/tasks/{task['id']}", json={"status": "in_progress"})

    resp = client.get(f"/history/?task_id={task['id']}")
    assert resp.status_code == 200
    assert any(e["action"] == "status_change" for e in resp.json())