from datetime import datetime, timedelta, timezone


from app.models import (

    Application,

    ApplicationStatus,

    Candidate,

    InterviewStatus,

    Opportunity,

    User,

    UserRole,

)

from app.security import hash_password


TEST_PASSWORD = "TestWorkflowPassword123!"


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


def create_application(db, candidate_number, application_status):

    candidate_user = create_user(

        db,

        f"workflow-candidate-{candidate_number}@example.com",

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

        title=f"Workflow Opportunity {candidate_number}",

        description="Synthetic opportunity for workflow testing.",

        opportunity_type="Volunteer",

        location="Sundarbans, West Bengal",

        status="open",

    )

    db.add(opportunity)

    db.flush()


    application = Application(

        candidate_id=candidate.id,

        opportunity_id=opportunity.id,

        status=application_status,

    )

    db.add(application)

    db.flush()


    return application


def get_token(client, email):

    response = client.post(

        "/auth/login",

        json={

            "email": email,

            "password": TEST_PASSWORD,

        },

    )

    assert response.status_code == 200, response.text

    return response.json()["access_token"]


def test_staff_can_schedule_interview_for_interview_stage_application(

    client, test_session_factory

):

    staff_email = "workflow-staff@example.com"


    with test_session_factory() as db:

        create_user(db, staff_email, UserRole.STAFF)

        interviewer = create_user(

            db,

            "workflow-interviewer@example.com",

            UserRole.INTERVIEWER,

        )

        application = create_application(

            db, 201, ApplicationStatus.INTERVIEW

        )


        interviewer_id = interviewer.id

        application_id = application.id

        db.commit()


    token = get_token(client, staff_email)


    response = client.post(

        "/interviews",

        headers={"Authorization": f"Bearer {token}"},

        json={

            "application_id": application_id,

            "interviewer_id": interviewer_id,

            "scheduled_at": (

                datetime.now(timezone.utc) + timedelta(days=3)

            ).isoformat(),

            "meeting_link": "https://example.com/test-meeting",

        },

    )


    assert response.status_code == 201, response.text

    data = response.json()

    assert data["application_id"] == application_id

    assert data["interviewer_id"] == interviewer_id

    assert data["status"] == InterviewStatus.SCHEDULED.value


def test_staff_cannot_schedule_interview_before_interview_stage(

    client, test_session_factory

):

    staff_email = "workflow-stage-staff@example.com"


    with test_session_factory() as db:

        create_user(db, staff_email, UserRole.STAFF)

        interviewer = create_user(

            db,

            "workflow-stage-interviewer@example.com",

            UserRole.INTERVIEWER,

        )

        application = create_application(

            db, 202, ApplicationStatus.APPLIED

        )


        interviewer_id = interviewer.id

        application_id = application.id

        db.commit()


    token = get_token(client, staff_email)


    response = client.post(

        "/interviews",

        headers={"Authorization": f"Bearer {token}"},

        json={

            "application_id": application_id,

            "interviewer_id": interviewer_id,

            "scheduled_at": (

                datetime.now(timezone.utc) + timedelta(days=3)

            ).isoformat(),

            "meeting_link": "https://example.com/test-meeting",

        },

    )


    assert response.status_code == 400

    assert "interview status" in response.json()["detail"].lower()


def test_staff_cannot_assign_candidate_as_interviewer(

    client, test_session_factory

):

    staff_email = "workflow-invalid-assignment-staff@example.com"


    with test_session_factory() as db:

        create_user(db, staff_email, UserRole.STAFF)

        candidate_user = create_user(

            db,

            "workflow-not-an-interviewer@example.com",

            UserRole.CANDIDATE,

        )

        application = create_application(

            db, 203, ApplicationStatus.INTERVIEW

        )


        candidate_user_id = candidate_user.id

        application_id = application.id

        db.commit()


    token = get_token(client, staff_email)


    response = client.post(

        "/interviews",

        headers={"Authorization": f"Bearer {token}"},

        json={

            "application_id": application_id,

            "interviewer_id": candidate_user_id,

            "scheduled_at": (

                datetime.now(timezone.utc) + timedelta(days=3)

            ).isoformat(),

            "meeting_link": "https://example.com/test-meeting",

        },

    )


    assert response.status_code == 400

    assert "interviewer role" in response.json()["detail"].lower()


def test_completed_interview_allows_feedback_and_rejects_duplicate(

    client, test_session_factory

):

    staff_email = "workflow-completion-staff@example.com"

    interviewer_email = "workflow-completion-interviewer@example.com"


    with test_session_factory() as db:

        create_user(db, staff_email, UserRole.STAFF)

        interviewer = create_user(

            db, interviewer_email, UserRole.INTERVIEWER

        )

        application = create_application(

            db, 204, ApplicationStatus.INTERVIEW

        )


        interviewer_id = interviewer.id

        application_id = application.id

        db.commit()


    staff_token = get_token(client, staff_email)

    interviewer_token = get_token(client, interviewer_email)


    schedule_response = client.post(

        "/interviews",

        headers={"Authorization": f"Bearer {staff_token}"},

        json={

            "application_id": application_id,

            "interviewer_id": interviewer_id,

            "scheduled_at": (

                datetime.now(timezone.utc) + timedelta(days=3)

            ).isoformat(),

            "meeting_link": "https://example.com/test-meeting",

        },

    )


    assert schedule_response.status_code == 201, schedule_response.text

    interview_id = schedule_response.json()["id"]


    feedback_payload = {

        "technical_score": 8,

        "communication_score": 9,

        "problem_solving_score": 8,

        "comments": "Synthetic feedback for automated workflow testing.",

        "recommendation": "selected",

    }


    early_feedback = client.post(

        f"/feedback/{interview_id}",

        headers={"Authorization": f"Bearer {interviewer_token}"},

        json=feedback_payload,

    )

    assert early_feedback.status_code == 400


    completion_response = client.patch(

        f"/interviews/{interview_id}/status",

        params={"status_value": "completed"},

        headers={"Authorization": f"Bearer {staff_token}"},

    )

    assert completion_response.status_code == 200, completion_response.text

    assert completion_response.json()["status"] == "completed"


    feedback_response = client.post(

        f"/feedback/{interview_id}",

        headers={"Authorization": f"Bearer {interviewer_token}"},

        json=feedback_payload,

    )

    assert feedback_response.status_code == 201, feedback_response.text

    assert feedback_response.json()["technical_score"] == 8


    duplicate_response = client.post(

        f"/feedback/{interview_id}",

        headers={"Authorization": f"Bearer {interviewer_token}"},

        json=feedback_payload,

    )

    assert duplicate_response.status_code == 409


def test_unassigned_interviewer_cannot_submit_feedback(

    client, test_session_factory

):

    staff_email = "workflow-owner-staff@example.com"

    assigned_email = "workflow-assigned-interviewer@example.com"

    other_email = "workflow-other-interviewer@example.com"


    with test_session_factory() as db:

        create_user(db, staff_email, UserRole.STAFF)

        assigned_interviewer = create_user(

            db, assigned_email, UserRole.INTERVIEWER

        )

        create_user(db, other_email, UserRole.INTERVIEWER)


        application = create_application(

            db, 205, ApplicationStatus.INTERVIEW

        )


        assigned_interviewer_id = assigned_interviewer.id

        application_id = application.id

        db.commit()


    staff_token = get_token(client, staff_email)

    other_interviewer_token = get_token(client, other_email)


    schedule_response = client.post(

        "/interviews",

        headers={"Authorization": f"Bearer {staff_token}"},

        json={

            "application_id": application_id,

            "interviewer_id": assigned_interviewer_id,

            "scheduled_at": (

                datetime.now(timezone.utc) + timedelta(days=3)

            ).isoformat(),

            "meeting_link": "https://example.com/test-meeting",

        },

    )

    assert schedule_response.status_code == 201, schedule_response.text

    interview_id = schedule_response.json()["id"]


    completion_response = client.patch(

        f"/interviews/{interview_id}/status",

        params={"status_value": "completed"},

        headers={"Authorization": f"Bearer {staff_token}"},

    )

    assert completion_response.status_code == 200, completion_response.text


    response = client.post(

        f"/feedback/{interview_id}",

        headers={"Authorization": f"Bearer {other_interviewer_token}"},

        json={

            "technical_score": 8,

            "communication_score": 8,

            "problem_solving_score": 8,

            "comments": "This submission should be denied.",

            "recommendation": "selected",

        },

    )


    assert response.status_code == 403


def test_cannot_schedule_interview_in_the_past(

    client, test_session_factory

):

    staff_email = "workflow-past-date-staff@example.com"


    with test_session_factory() as db:

        create_user(db, staff_email, UserRole.STAFF)

        interviewer = create_user(

            db,

            "workflow-past-date-interviewer@example.com",

            UserRole.INTERVIEWER,

        )

        application = create_application(

            db, 206, ApplicationStatus.INTERVIEW

        )


        interviewer_id = interviewer.id

        application_id = application.id

        db.commit()


    token = get_token(client, staff_email)


    response = client.post(

        "/interviews",

        headers={"Authorization": f"Bearer {token}"},

        json={

            "application_id": application_id,

            "interviewer_id": interviewer_id,

            "scheduled_at": (

                datetime.now(timezone.utc) - timedelta(days=1)

            ).isoformat(),

            "meeting_link": "https://example.com/test-meeting",

        },

    )


    assert response.status_code == 400

    assert "future time" in response.json()["detail"].lower()


def test_cannot_schedule_interview_without_timezone(

    client, test_session_factory

):

    staff_email = "workflow-no-timezone-staff@example.com"


    with test_session_factory() as db:

        create_user(db, staff_email, UserRole.STAFF)

        interviewer = create_user(

            db,

            "workflow-no-timezone-interviewer@example.com",

            UserRole.INTERVIEWER,

        )

        application = create_application(

            db, 207, ApplicationStatus.INTERVIEW

        )


        interviewer_id = interviewer.id

        application_id = application.id

        db.commit()


    token = get_token(client, staff_email)


    naive_datetime = (

        datetime.now(timezone.utc) + timedelta(days=3)

    ).strftime("%Y-%m-%dT%H:%M:%S")


    response = client.post(

        "/interviews",

        headers={"Authorization": f"Bearer {token}"},

        json={

            "application_id": application_id,

            "interviewer_id": interviewer_id,

            "scheduled_at": naive_datetime,

            "meeting_link": "https://example.com/test-meeting",

        },

    )


    assert response.status_code == 422

    assert "timezone" in response.json()["detail"].lower()


def test_cancelled_interview_cannot_be_completed(

    client, test_session_factory

):

    staff_email = "workflow-cancel-transition-staff@example.com"


    with test_session_factory() as db:

        create_user(db, staff_email, UserRole.STAFF)

        interviewer = create_user(

            db,

            "workflow-cancel-transition-interviewer@example.com",

            UserRole.INTERVIEWER,

        )

        application = create_application(

            db, 208, ApplicationStatus.INTERVIEW

        )


        interviewer_id = interviewer.id

        application_id = application.id

        db.commit()


    token = get_token(client, staff_email)


    schedule_response = client.post(

        "/interviews",

        headers={"Authorization": f"Bearer {token}"},

        json={

            "application_id": application_id,

            "interviewer_id": interviewer_id,

            "scheduled_at": (

                datetime.now(timezone.utc) + timedelta(days=3)

            ).isoformat(),

            "meeting_link": "https://example.com/test-meeting",

        },

    )

    assert schedule_response.status_code == 201, schedule_response.text


    interview_id = schedule_response.json()["id"]


    cancel_response = client.patch(

        f"/interviews/{interview_id}/status",

        params={"status_value": "cancelled"},

        headers={"Authorization": f"Bearer {token}"},

    )

    assert cancel_response.status_code == 200, cancel_response.text


    complete_response = client.patch(

        f"/interviews/{interview_id}/status",

        params={"status_value": "completed"},

        headers={"Authorization": f"Bearer {token}"},

    )


    assert complete_response.status_code == 400


def test_completed_interview_cannot_be_cancelled(

    client, test_session_factory

):

    staff_email = "workflow-complete-transition-staff@example.com"


    with test_session_factory() as db:

        create_user(db, staff_email, UserRole.STAFF)

        interviewer = create_user(

            db,

            "workflow-complete-transition-interviewer@example.com",

            UserRole.INTERVIEWER,

        )

        application = create_application(

            db, 209, ApplicationStatus.INTERVIEW

        )


        interviewer_id = interviewer.id

        application_id = application.id

        db.commit()


    token = get_token(client, staff_email)


    schedule_response = client.post(

        "/interviews",

        headers={"Authorization": f"Bearer {token}"},

        json={

            "application_id": application_id,

            "interviewer_id": interviewer_id,

            "scheduled_at": (

                datetime.now(timezone.utc) + timedelta(days=3)

            ).isoformat(),

            "meeting_link": "https://example.com/test-meeting",

        },

    )

    assert schedule_response.status_code == 201, schedule_response.text


    interview_id = schedule_response.json()["id"]


    complete_response = client.patch(

        f"/interviews/{interview_id}/status",

        params={"status_value": "completed"},

        headers={"Authorization": f"Bearer {token}"},

    )

    assert complete_response.status_code == 200, complete_response.text


    cancel_response = client.patch(

        f"/interviews/{interview_id}/status",

        params={"status_value": "cancelled"},

        headers={"Authorization": f"Bearer {token}"},

    )


    assert cancel_response.status_code == 400
