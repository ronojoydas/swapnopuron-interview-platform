
def test_create_opportunity_without_token(client):
    response = client.post(
        "/opportunities",
        json={
            "title": "Permission Test Opportunity",
            "description": "This opportunity is created only for permission testing.",
            "opportunity_type": "Volunteer",
            "location": "Sundarbans, West Bengal",
        },
    )

    assert response.status_code in (401, 403)


def test_candidate_cannot_create_opportunity(client):
    email = "opportunity-permission-test@example.com"
    password = "TestCandidatePassword123!"

    register_response = client.post(
        "/auth/register",
        json={
            "full_name": "Opportunity Permission Test",
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
        "/opportunities",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Candidate Unauthorized Opportunity",
            "description": "A candidate should not be able to create this opportunity.",
            "opportunity_type": "Volunteer",
            "location": "Sundarbans, West Bengal",
        },
    )

    assert response.status_code == 403
