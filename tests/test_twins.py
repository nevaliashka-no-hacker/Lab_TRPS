def test_create_twin(client, sample_project):
    resp = client.post(
        "/twins/",
        json={"project_id": sample_project["id"]},
    )
    assert resp.status_code == 201
    assert resp.json()["version"] == 1


def test_add_prediction_valid(client, sample_project):
    twin = client.post(
        "/twins/", json={"project_id": sample_project["id"]}
    ).json()

    resp = client.post(
        f"/twins/{twin['id']}/predictions",
        json={"twin_id": twin["id"], "predicted_time": 10.5, "accuracy": 0.85},
    )
    assert resp.status_code == 201
    assert resp.json()["accuracy"] == 0.85


def test_add_prediction_low_accuracy(client, sample_project):
    """Инвариант: accuracy ≥ 0.8."""
    twin = client.post(
        "/twins/", json={"project_id": sample_project["id"]}
    ).json()

    resp = client.post(
        f"/twins/{twin['id']}/predictions",
        json={"twin_id": twin["id"], "predicted_time": 5.0, "accuracy": 0.5},
    )
    assert resp.status_code == 422


def test_add_prediction_negative_time(client, sample_project):
    """Инвариант: predicted_time > 0."""
    twin = client.post(
        "/twins/", json={"project_id": sample_project["id"]}
    ).json()

    resp = client.post(
        f"/twins/{twin['id']}/predictions",
        json={"twin_id": twin["id"], "predicted_time": -1.0, "accuracy": 0.9},
    )
    assert resp.status_code == 422