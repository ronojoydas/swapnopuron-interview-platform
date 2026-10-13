
def test_create_candidate_profile_without_token(client):
    response = client.post(
        "/candidates/me",
        json={
            "phone": "9000000000",
            "education": "Test qualification",
            "skills": "Python, SQL",
            "experience": "Test experience",
            "resume_path": None,
        },
    )

    assert response.status_code in (401, 403)


def test_candidate_can_create_own_profile(client):
    email = "candidate-profile-permission-test@example.com"
    password = "TestCandidatePassword123!"

    register_response = client.post(
        "/auth/register",
        json={
            "full_name": "Candidate Profile Test",
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
    headers = {"Authorization": f"Bearer {token}"}

    profile_response = client.post(
        "/candidates/me",
        headers=headers,
        json={
            "phone": "9000000000",
            "education": "Test qualification",
            "skills": "Python, SQL",
            "experience": "Test experience",
            "resume_path": None,
        },
    )

    assert profile_response.status_code in (201, 409)
