
def test_get_feedback_without_token(client):
    response = client.get("/feedback/1")

    assert response.status_code in (401, 403)


def test_candidate_cannot_submit_feedback(client):
    email = "feedback-permission-test@example.com"
    password = "TestCandidatePassword123!"

    register_response = client.post(
        "/auth/register",
        json={
            "full_name": "Feedback Permission Test",
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

    response = client.post(
        "/feedback/1",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "technical_score": 8,
            "communication_score": 9,
            "problem_solving_score": 8,
            "comments": "Test feedback for permission checking.",
            "recommendation": "selected",
        },
    )

    assert response.status_code == 403
