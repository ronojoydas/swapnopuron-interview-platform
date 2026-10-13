import pytest

STAFF_EMAIL = "workflow-staff@example.com"
STAFF_PASSWORD = "WorkflowStaffPassword123!"

CANDIDATE_EMAIL = "workflow-candidate@example.com"
CANDIDATE_PASSWORD = "WorkflowCandidatePassword123!"

OTHER_CANDIDATE_EMAIL = "other-candidate@example.com"
OTHER_CANDIDATE_PASSWORD = "OtherCandidatePassword123!"


@pytest.fixture
def staff_account(test_session_factory):
    from app.models import User, UserRole
    from app.security import hash_password

    with test_session_factory() as db:
        db.add(
            User(
                full_name="Workflow Test Staff",
                email=STAFF_EMAIL,
                password_hash=hash_password(STAFF_PASSWORD),
                role=UserRole.STAFF,
            )
        )
        db.commit()


@pytest.fixture
def candidate_account(client):
    response = client.post(
        "/auth/register",
        json={
            "full_name": "Workflow Test Candidate",
            "email": CANDIDATE_EMAIL,
            "password": CANDIDATE_PASSWORD,
        },
    )
    assert response.status_code in (200, 201), response.text

    response = client.post(
        "/auth/login",
        json={"email": CANDIDATE_EMAIL, "password": CANDIDATE_PASSWORD},
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


@pytest.fixture
def other_candidate_account(client):
    response = client.post(
        "/auth/register",
        json={
            "full_name": "Other Workflow Candidate",
            "email": OTHER_CANDIDATE_EMAIL,
            "password": OTHER_CANDIDATE_PASSWORD,
        },
    )
    assert response.status_code in (200, 201), response.text

    login_response = client.post(
        "/auth/login",
        json={
            "email": OTHER_CANDIDATE_EMAIL,
            "password": OTHER_CANDIDATE_PASSWORD,
        },
    )
    assert login_response.status_code == 200, login_response.text

    token = login_response.json()["access_token"]

    # Create the second candidate's profile so the test reaches
    # the application ownership check.
    profile_response = client.post(
        "/candidates/me",
        headers={"Authorization": f"Bearer {token}"},
        json={},
    )
    assert profile_response.status_code in (200, 201), profile_response.text

    return token


@pytest.fixture
def staff_token(client, staff_account):
    response = client.post(
        "/auth/login",
        json={"email": STAFF_EMAIL, "password": STAFF_PASSWORD},
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


@pytest.fixture
def candidate_profile(client, candidate_account):
    response = client.post(
        "/candidates/me",
        headers={"Authorization": f"Bearer {candidate_account}"},
        json={},
    )
    assert response.status_code in (200, 201), response.text
    return response.json()


@pytest.fixture
def open_opportunity(client, staff_token):
    response = client.post(
        "/opportunities",
        headers={"Authorization": f"Bearer {staff_token}"},
        json={
            "title": "Workflow Test Opportunity",
            "description": "A synthetic opportunity for automated tests.",
            "opportunity_type": "Data Analyst",
            "location": "Kolkata",
        },
    )
    assert response.status_code in (200, 201), response.text
    return response.json()


def test_candidate_can_apply_for_open_opportunity(
    client, candidate_account, candidate_profile, open_opportunity
):
    response = client.post(
        f"/applications/{open_opportunity['id']}",
        headers={"Authorization": f"Bearer {candidate_account}"},
    )
    assert response.status_code == 201, response.text
    assert response.json()["status"] == "applied"


def test_candidate_cannot_apply_twice(
    client, candidate_account, candidate_profile, open_opportunity
):
    headers = {"Authorization": f"Bearer {candidate_account}"}
    url = f"/applications/{open_opportunity['id']}"

    response = client.post(url, headers=headers)
    assert response.status_code == 201, response.text

    response = client.post(url, headers=headers)
    assert response.status_code == 409


def test_candidate_cannot_apply_without_profile(
    client, candidate_account, open_opportunity
):
    response = client.post(
        f"/applications/{open_opportunity['id']}",
        headers={"Authorization": f"Bearer {candidate_account}"},
    )
    assert response.status_code == 404
    assert "profile" in response.json()["detail"].lower()


def test_candidate_cannot_apply_to_closed_opportunity(
    client,
    candidate_account,
    candidate_profile,
    open_opportunity,
    staff_token,
):
    response = client.patch(
        f"/opportunities/{open_opportunity['id']}/close",
        headers={"Authorization": f"Bearer {staff_token}"},
    )
    assert response.status_code == 200, response.text

    response = client.post(
        f"/applications/{open_opportunity['id']}",
        headers={"Authorization": f"Bearer {candidate_account}"},
    )
    assert response.status_code == 400


def test_candidate_can_view_own_applications(
    client, candidate_account, candidate_profile, open_opportunity
):
    headers = {"Authorization": f"Bearer {candidate_account}"}

    response = client.post(
        f"/applications/{open_opportunity['id']}", headers=headers
    )
    assert response.status_code == 201, response.text

    response = client.get("/applications/me", headers=headers)
    assert response.status_code == 200, response.text
    assert len(response.json()) == 1
    assert response.json()[0]["opportunity_id"] == open_opportunity["id"]


def test_staff_can_update_application_status(
    client,
    staff_token,
    candidate_account,
    candidate_profile,
    open_opportunity,
):
    response = client.post(
        f"/applications/{open_opportunity['id']}",
        headers={"Authorization": f"Bearer {candidate_account}"},
    )
    assert response.status_code == 201, response.text

    application_id = response.json()["id"]

    response = client.patch(
        f"/applications/{application_id}/status",
        headers={"Authorization": f"Bearer {staff_token}"},
        json={"status": "screening"},
    )
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "screening"


def test_candidate_cannot_view_another_candidates_application(
    client,
    candidate_account,
    candidate_profile,
    other_candidate_account,
    open_opportunity,
):
    response = client.post(
        f"/applications/{open_opportunity['id']}",
        headers={"Authorization": f"Bearer {candidate_account}"},
    )
    assert response.status_code == 201, response.text

    application_id = response.json()["id"]

    # Confirm the application exists and its owner can access it.
    response = client.get(
        f"/applications/{application_id}",
        headers={"Authorization": f"Bearer {candidate_account}"},
    )
    assert response.status_code == 200, response.text

    # A different candidate must not access the application.
    response = client.get(
        f"/applications/{application_id}",
        headers={"Authorization": f"Bearer {other_candidate_account}"},
    )
    assert response.status_code == 403, response.text
