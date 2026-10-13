
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


TEST_PASSWORD = "TestInterviewerPassword123!"


def create_test_interviewer(db, email):
    user = User(
        full_name=f"Test Interviewer {email}",
        email=email,
        password_hash=hash_password(TEST_PASSWORD),
        role=UserRole.INTERVIEWER,
    )
    db.add(user)
    db.flush()
    return user


def create_test_application(db, interviewer_id, candidate_number):
    candidate_user = User(
        full_name=f"Test Candidate {candidate_number}",
        email=f"interview-candidate-{candidate_number}@example.com",
        password_hash=hash_password("TestCandidatePassword123!"),
        role=UserRole.CANDIDATE,
    )
    db.add(candidate_user)
    db.flush()

    candidate = Candidate(
        user_id=candidate_user.id,
        phone="9000000000",
        education="Test qualification",
        skills="Python, SQL",
        experience="Test experience",
    )
    db.add(candidate)
    db.flush()

    opportunity = Opportunity(
        title=f"Test Opportunity {candidate_number}",
        description="Synthetic opportunity for automated testing.",
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
        interviewer_id=interviewer_id,
        scheduled_at=datetime.now(timezone.utc) + timedelta(days=7),
        status=InterviewStatus.SCHEDULED,
    )
    db.add(interview)
    db.flush()

    return interview


def login(client, email, password):
    response = client.post(
        "/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200, (
        f"Login failed for {email}: "
        f"HTTP {response.status_code} - {response.text}"
    )
    return response.json()["access_token"]


def test_list_interviews_without_token(client):
    response = client.get("/interviews")
    assert response.status_code in (401, 403)


def test_candidate_cannot_update_interview_status(
    client, test_session_factory
):
    email = "interview-permission-test@example.com"
    password = "TestCandidatePassword123!"

    with test_session_factory() as db:
        user = User(
            full_name="Interview Permission Test",
            email=email,
            password_hash=hash_password(password),
            role=UserRole.CANDIDATE,
        )
        db.add(user)
        db.commit()

    token = login(client, email, password)

    response = client.patch(
        "/interviews/1/status",
        params={"status_value": "completed"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403


def test_interviewer_cannot_update_interview_status(
    client, test_session_factory
):
    email = "status-test-interviewer@example.com"

    with test_session_factory() as db:
        create_test_interviewer(db, email)
        db.commit()

    token = login(client, email, TEST_PASSWORD)

    response = client.patch(
        "/interviews/1/status",
        params={"status_value": "completed"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403


def test_interviewer_sees_only_assigned_interviews(
    client, test_session_factory
):
    with test_session_factory() as db:
        interviewer_one = create_test_interviewer(
            db, "interviewer-one@example.com"
        )
        interviewer_two = create_test_interviewer(
            db, "interviewer-two@example.com"
        )

        interview_one = create_test_application(
            db, interviewer_one.id, 101
        )
        interview_two = create_test_application(
            db, interviewer_two.id, 102
        )

        interview_one_id = interview_one.id
        interview_two_id = interview_two.id
        db.commit()

    token = login(
        client,
        "interviewer-one@example.com",
        TEST_PASSWORD,
    )

    response = client.get(
        "/interviews",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200, response.text
    returned_ids = {item["id"] for item in response.json()}

    assert interview_one_id in returned_ids
    assert interview_two_id not in returned_ids
