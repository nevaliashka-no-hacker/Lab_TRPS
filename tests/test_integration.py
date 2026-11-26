def test_receive_git_event(client, sample_project):
    resp = client.post(
        "/integration/git-events",
        json={
            "project_id": sample_project["id"],
            "event_type": "commit",
            "commit_sha": "abc123",
            "author": "alice",
        },
    )
    assert resp.status_code == 201
    assert resp.json()["commit_sha"] == "abc123"


def test_receive_cicd_status(client, sample_project):
    resp = client.post(
        "/integration/cicd-statuses",
        json={
            "project_id": sample_project["id"],
            "pipeline_id": "pipeline-1",
            "status": "success",
        },
    )
    assert resp.status_code == 201
    assert resp.json()["status"] == "success"


def test_list_git_events(client, sample_project):
    client.post(
        "/integration/git-events",
        json={"project_id": sample_project["id"], "event_type": "push"},
    )
    resp = client.get(f"/integration/git-events?project_id={sample_project['id']}")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1