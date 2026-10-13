
def test_get_all_applications_without_token(client):
    response = client.get("/applications")

    assert response.status_code in (401, 403)


def test_candidate_cannot_get_all_applications(client):
    email = "permission-test-candidate@example.com"
    password = "TestCandidatePassword123!"

    register_response = client.post(
        "/auth/register",
        json={
            "full_name": "Permission Test Candidate",
            "email": email,
            "password": password,
        },
    )

    assert register_response.status_code in (201, 409)

    login_response = client.post(
        "/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    response = client.get(
        "/applications",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
