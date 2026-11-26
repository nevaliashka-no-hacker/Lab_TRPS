def test_add_metric(client, sample_project):
    sprint = client.post(
        "/sprints/",
        json={"name": "S", "project_id": sample_project["id"]},
    ).json()
    resp = client.post(
        "/twins/metrics",
        json={
            "name": "velocity",
            "value": 20.0,
            "unit": "points",
            "sprint_id": sprint["id"],
        },
    )
    assert resp.status_code == 201
    assert resp.json()["value"] == 20.0


def test_add_metric_negative_value(client, sample_project):
    """Инвариант: value ≥ 0."""
    sprint = client.post(
        "/sprints/",
        json={"name": "S", "project_id": sample_project["id"]},
    ).json()
    resp = client.post(
        "/twins/metrics",
        json={
            "name": "velocity",
            "value": -5.0,
            "sprint_id": sprint["id"],
        },
    )
    assert resp.status_code == 422