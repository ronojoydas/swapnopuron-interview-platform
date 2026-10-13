from datetime import datetime, timedelta, timezone

from app.models import (
    Application,
    ApplicationStatus,
    Candidate,
    Interview,
    InterviewStatus,
    Opportunity,
    User,
    UserRole,
)
from app.security import hash_password


TEST_PASSWORD = "TestFeedbackPassword123!"


def create_user(db, email, role):
    user = User(
        full_name=f"Test User {email}",
        email=email,
        password_hash=hash_password(TEST_PASSWORD),
        role=role,
    )
    db.add(user)
    db.flush()
    return user


def create_interview(db, candidate_number=301):
    interviewer = create_user(
        db,
        f"feedback-interviewer-{candidate_number}@example.com",
        UserRole.INTERVIEWER,
    )

    candidate_user = create_user(
        db,
        f"feedback-candidate-{candidate_number}@example.com",
        UserRole.CANDIDATE,
    )

    candidate = Candidate(
        user_id=candidate_user.id,
        phone="9000000000",
        education="Test qualification",
        skills="Python, SQL",
        experience="Synthetic test experience",
    )
    db.add(candidate)
    db.flush()

    opportunity = Opportunity(
        title=f"Feedback Test Opportunity {candidate_number}",
        description="Synthetic opportunity for feedback permission tests.",
        opportunity_type="Volunteer",
        location="Sundarbans, West Bengal",
        status="open",
    )
    db.add(opportunity)
    db.flush()

    application = Application(
        candidate_id=candidate.id,
        opportunity_id=opportunity.id,
        status=ApplicationStatus.INTERVIEW,
    )
    db.add(application)
    db.flush()

    interview = Interview(
        application_id=application.id,
        interviewer_id=interviewer.id,
        scheduled_at=datetime.now(timezone.utc) + timedelta(days=3),
        status=InterviewStatus.COMPLETED,
    )
    db.add(interview)
    db.flush()

    return interview, interviewer, candidate_user


def login(client, email):
    response = client.post(
        "/auth/login",
        json={
            "email": email,
            "password": TEST_PASSWORD,
        },
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def feedback_payload():
    return {
        "technical_score": 8,
        "communication_score": 9,
        "problem_solving_score": 8,
        "comments": "Synthetic feedback for permission testing.",
        "recommendation": "selected",
    }


def test_get_feedback_without_token(client):
    response = client.get("/feedback/1")
    assert response.status_code in (401, 403)


def test_candidate_cannot_submit_feedback(client, test_session_factory):
    email = "feedback-permission-test@example.com"

    register_response = client.post(
        "/auth/register",
        json={
            "full_name": "Feedback Permission Test",
            "email": email,
            "password": "TestCandidatePassword123!",
        },
    )
    assert register_response.status_code in (201, 409)

    login_response = client.post(
        "/auth/login",
        json={
            "email": email,
            "password": "TestCandidatePassword123!",
        },
    )
    assert login_response.status_code == 200

    response = client.post(
        "/feedback/1",
        headers={
            "Authorization": (
                f"Bearer {login_response.json()['access_token']}"
            )
        },
        json=feedback_payload(),
    )

    assert response.status_code == 403


def test_feedback_for_nonexistent_interview_returns_404(
    client, test_session_factory
):
    staff_email = "feedback-missing-staff@example.com"

    with test_session_factory() as db:
        create_user(db, staff_email, UserRole.STAFF)
        db.commit()

    token = login(client, staff_email)

    response = client.get(
        "/feedback/999999",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Interview not found"


def test_feedback_not_yet_submitted_returns_404(
    client, test_session_factory
):
    staff_email = "feedback-not-submitted-staff@example.com"

    with test_session_factory() as db:
        create_user(db, staff_email, UserRole.STAFF)
        interview, _, _ = create_interview(db, 302)
        interview_id = interview.id
        db.commit()

    token = login(client, staff_email)

    response = client.get(
        f"/feedback/{interview_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404
    assert (
        response.json()["detail"]
        == "Feedback has not been submitted yet"
    )


def test_unassigned_interviewer_cannot_read_feedback(
    client, test_session_factory
):
    staff_email = "feedback-owner-staff@example.com"
    other_interviewer_email = "feedback-other-interviewer@example.com"

    with test_session_factory() as db:
        create_user(db, staff_email, UserRole.STAFF)
        interview, assigned_interviewer, _ = create_interview(db, 303)
        create_user(db, other_interviewer_email, UserRole.INTERVIEWER)

        interview_id = interview.id
        assigned_interviewer_id = assigned_interviewer.id
        db.commit()

    staff_token = login(client, staff_email)

    # Create feedback through the actual API as the assigned interviewer.
    assigned_token = login(
        client,
        f"feedback-interviewer-303@example.com",
    )

    response = client.post(
        f"/feedback/{interview_id}",
        headers={"Authorization": f"Bearer {assigned_token}"},
        json=feedback_payload(),
    )
    assert response.status_code == 201, response.text

    other_token = login(client, other_interviewer_email)

    response = client.get(
        f"/feedback/{interview_id}",
        headers={"Authorization": f"Bearer {other_token}"},
    )

    assert response.status_code == 403

    # Staff should still be able to read the feedback.
    staff_response = client.get(
        f"/feedback/{interview_id}",
        headers={"Authorization": f"Bearer {staff_token}"},
    )
    assert staff_response.status_code == 200
    assert staff_response.json()["technical_score"] == 8


def test_candidate_cannot_read_existing_feedback(
    client, test_session_factory
):
    with test_session_factory() as db:
        interview, _, candidate_user = create_interview(db, 304)
        interview_id = interview.id
        candidate_email = candidate_user.email
        db.commit()

    assigned_token = login(
        client,
        "feedback-interviewer-304@example.com",
    )

    submit_response = client.post(
        f"/feedback/{interview_id}",
        headers={"Authorization": f"Bearer {assigned_token}"},
        json=feedback_payload(),
    )
    assert submit_response.status_code == 201, submit_response.text

    candidate_token = login(client, candidate_email)

    response = client.get(
        f"/feedback/{interview_id}",
        headers={"Authorization": f"Bearer {candidate_token}"},
    )

    assert response.status_code == 403